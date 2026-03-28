/**
 * One-time email sign-in for Storacha. Stores agent + space on this machine.
 * Usage: node login.js MY_EMAIL
 *
 * Uses the same StoreConf instance as server.js (storacha-store.js) so login and /upload share one config file.
 */
import "dotenv/config";
import { create } from "@storacha/client";
import { store, storeDiagnostics } from "./storacha-store.js";

const email = (process.argv[2] || process.env.STORACHA_LOGIN_EMAIL || "").trim();
if (!email || !email.includes("@")) {
  console.error("Usage: node login.js you@example.com  (or set STORACHA_LOGIN_EMAIL in storacha-uploader/.env)");
  process.exit(1);
}

const diag = storeDiagnostics();
console.log("[storacha] login config:", JSON.stringify(diag, null, 2));

const client = await create({ store });
console.log("Opening Storacha login for:", email);
await client.login(email);
const spaces = client.spaces();
if (spaces.length && !client.currentSpace()) {
  await client.setCurrentSpace(spaces[0].did());
}
const space = client.currentSpace();
console.log("Login OK. Space:", space ? space.did() : "(none — create a space in the Storacha dashboard if needed)");

// Prove persistence: second client from same store must see the same space list (same file on disk).
const verify = await create({ store });
console.log(
  "[storacha] reload verify — spaces:",
  verify.spaces().length,
  "current:",
  verify.currentSpace() ? verify.currentSpace().did() : null,
);

// Windows / atomic writes: avoid process.exit(0) immediately after save (can skip flush in edge cases).
await new Promise((r) => setTimeout(r, 500));
process.exit(0);
