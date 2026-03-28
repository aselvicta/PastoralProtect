/**
 * HTTP bridge for PastoralProtect: accepts canonical JSON bytes (base64) and uploads via @storacha/client.
 *
 * Upload uses Base._invocationConfig → this._agent.currentSpace() (raw DID on @storacha/access Agent),
 * NOT Client.currentSpace(). If the spaces map is empty on load but delegations exist (known state
 * corruption / edge), agent.currentSpace() is null and upload fails. We call addSpacesFromDelegations
 * to rebuild spaces from the delegation store, then setCurrentSpace.
 */
import "dotenv/config";
import express from "express";
import { create } from "@storacha/client";
import { addSpacesFromDelegations } from "@storacha/access/agent";
import { store, storeDiagnostics } from "./storacha-store.js";

const PORT = Number(process.env.PORT || 8788);
const SECRET = (process.env.STORACHA_UPLOADER_SECRET || "").trim();
if (!SECRET) {
  console.error("Set STORACHA_UPLOADER_SECRET in the environment.");
  process.exit(1);
}

/** Prefer this DID when set (must exist in agent.spaces after sync). */
const PREFERRED_SPACE_DID = (process.env.STORACHA_SPACE_DID || "").trim();

const diag = storeDiagnostics();
console.log("[storacha-uploader] startup config:", JSON.stringify(diag, null, 2));

const app = express();
app.use(express.json({ limit: "20mb" }));

function auth(req, res, next) {
  const h = req.headers.authorization || "";
  const bearer = h.startsWith("Bearer ") ? h.slice(7).trim() : "";
  const x = (req.headers["x-storacha-upload-secret"] || "").trim();
  if (bearer === SECRET || x === SECRET) {
    return next();
  }
  res.status(401).json({ detail: "Unauthorized" });
}

/**
 * Snapshot using the same fields upload uses: Agent#currentSpace (raw DID), not only Client#currentSpace.
 */
function agentSnapshot(client) {
  const agent = client.agent;
  const id = agent.currentSpace();
  const curClient = client.currentSpace();
  return {
    spacesMapSize: agent.spaces.size,
    spaceDids: [...agent.spaces.keys()],
    agentCurrentSpaceId: id ?? null,
    agentCurrentSpaceIsNull: id == null,
    clientCurrentSpaceDid: curClient ? curClient.did() : null,
  };
}

/**
 * If spaces map is empty but delegations exist, rebuild spaces (Storacha access helper).
 */
async function syncSpacesFromDelegationsIfNeeded(client) {
  const agent = client.agent;
  if (agent.spaces.size > 0) {
    return { ran: false, reason: "spaces_map_already_populated" };
  }
  const proofs = agent.delegations([]);
  if (proofs.length === 0) {
    return { ran: false, reason: "no_delegations_to_import_spaces" };
  }
  await addSpacesFromDelegations(agent, proofs);
  return { ran: true, proofsUsed: proofs.length, spaceCountAfter: agent.spaces.size };
}

/**
 * Ensure Agent has a current space DID (required by Base._invocationConfig for upload).
 */
async function ensureAgentCurrentSpace(client) {
  const agent = client.agent;
  const keys = [...agent.spaces.keys()];
  if (keys.length === 0) {
    return { ok: false, detail: "no_spaces_after_sync" };
  }
  let pick = null;
  if (PREFERRED_SPACE_DID && agent.spaces.has(PREFERRED_SPACE_DID)) {
    pick = PREFERRED_SPACE_DID;
  } else if (agent.currentSpace() && agent.spaces.has(agent.currentSpace())) {
    pick = agent.currentSpace();
  } else {
    pick = keys[0];
  }
  await client.setCurrentSpace(pick);
  return { ok: true, selectedDid: pick };
}

/**
 * Full pipeline: create client → sync spaces from delegations if needed → set current space.
 */
async function prepareClientForUpload() {
  const client = await create({ store });
  const before = agentSnapshot(client);

  const sync = await syncSpacesFromDelegationsIfNeeded(client);
  const afterSync = agentSnapshot(client);

  const ensured = await ensureAgentCurrentSpace(client);
  const after = agentSnapshot(client);

  return {
    before,
    sync,
    afterSync,
    ensured,
    after,
    ready: ensured.ok === true && after.agentCurrentSpaceId != null,
  };
}

async function buildDebugJson() {
  const client = await create({ store });
  const prep = await prepareClientForUpload();
  return {
    storePath: diag.storePath,
    profile: diag.profile,
    preferredSpaceDid: PREFERRED_SPACE_DID || null,
    ...prep,
  };
}

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "pastoral-protect-storacha-uploader", store: storeDiagnostics() });
});

/** Temporary: same auth as /upload — returns same space state as the uploader uses. */
app.get("/debug/storacha", auth, async (_req, res) => {
  try {
    const json = await buildDebugJson();
    res.json({
      storePath: json.storePath,
      spacesCount: json.after?.spaceDids?.length ?? 0,
      spaces: json.after?.spaceDids ?? [],
      currentSpace: json.after?.agentCurrentSpaceId ?? null,
      full: json,
    });
  } catch (e) {
    console.error(e);
    res.status(500).json({ detail: e instanceof Error ? e.message : String(e) });
  }
});

app.post("/upload", auth, async (req, res) => {
  const label = typeof req.body?.label === "string" ? req.body.label : "upload";
  const bodyB64 = req.body?.body_b64;
  if (typeof bodyB64 !== "string" || !bodyB64.length) {
    return res.status(400).json({ detail: "Missing body_b64 (base64 of canonical JSON bytes)" });
  }
  let raw;
  try {
    raw = Buffer.from(bodyB64, "base64");
  } catch {
    return res.status(400).json({ detail: "Invalid base64" });
  }
  if (!raw.length) {
    return res.status(400).json({ detail: "Empty body" });
  }

  try {
    const client = await create({ store });
    const snapBefore = agentSnapshot(client);
    console.log("[storacha-uploader] /upload BEFORE prepare:", JSON.stringify(snapBefore));

    const sync = await syncSpacesFromDelegationsIfNeeded(client);
    if (sync.ran) {
      console.log("[storacha-uploader] /upload syncSpacesFromDelegations:", JSON.stringify(sync));
    }

    const snapMid = agentSnapshot(client);
    console.log("[storacha-uploader] /upload AFTER sync:", JSON.stringify(snapMid));

    const ensured = await ensureAgentCurrentSpace(client);
    const snapAfter = agentSnapshot(client);
    console.log("[storacha-uploader] /upload AFTER ensure:", JSON.stringify({ ensured, snapAfter }));

    if (!ensured.ok || snapAfter.agentCurrentSpaceId == null) {
      return res.status(503).json({
        message: "Cannot select a Storacha space for upload.",
        storePath: diag.storePath,
        ...snapAfter,
        sync,
        ensured,
        hint: "Run npm run login once, or set STORACHA_SPACE_DID to a DID in spaceDids",
      });
    }

    console.log(
      "[storacha-uploader] upload using agent.currentSpace:",
      snapAfter.agentCurrentSpaceId,
      "label:",
      label,
    );

    const blob = new Blob([raw], { type: "application/json" });
    const root = await client.uploadFile(blob, { retries: 3 });
    const cid = String(root);
    return res.json({ cid });
  } catch (e) {
    console.error(e);
    const msg = e instanceof Error ? e.message : String(e);
    return res.status(500).json({ detail: msg, storePath: diag.storePath });
  }
});

async function startupProbe() {
  const prep = await prepareClientForUpload();
  console.log("[storacha-uploader] STARTUP probe (before listen):", JSON.stringify(prep, null, 2));
}

startupProbe()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Storacha uploader listening on http://127.0.0.1:${PORT}`);
    });
  })
  .catch((e) => {
    console.error("[storacha-uploader] startup probe failed:", e);
    process.exit(1);
  });
