# Production deployment checklist (PastoralProtect)

Stack that matches the hackathon demo with **live IPFS CIDs**:

| Piece | Typical host | Role |
|--------|----------------|------|
| Frontend | **Vercel** (or similar) | Next.js UI; only needs public `NEXT_PUBLIC_*` API URL |
| Backend API | **Render** Web Service | FastAPI, Postgres URL, JWT, oracle, calls uploader |
| Storacha uploader | **Render** Web Service (2nd service) | Node: `@storacha/client` bridge; **stateful** |
| Database | **Render Postgres** (or other) | `DATABASE_URL` for SQLAlchemy |

Mock CIDs still work if you omit Storacha; the API falls back when `STORACHA_FALLBACK_MOCK_ON_ERROR=true` (default). Responses include `storage_mode` (`live` \| `mock`) and optional `storage_warning`.

---

## 1. Credentials and secrets (what to create)

### Shared between backend and uploader

| Name | Where | Purpose |
|------|--------|---------|
| `STORACHA_UPLOADER_SECRET` | **Backend env** + **Uploader env** | Long random string; same value on both. Protects `POST /upload` on the Node service. **Not** exposed to the browser. |

Generate once (example): 32+ bytes of random hex or a password manager secret.

### Backend only (Render → Web Service → Environment)

| Variable | Required? | Notes |
|----------|------------|--------|
| `DATABASE_URL` | **Yes** for production | Postgres, e.g. `postgresql+psycopg2://user:pass@host:5432/dbname` |
| `JWT_SECRET` | **Yes** | Strong random string; signs user/admin JWTs |
| `ORACLE_SECRET` | Yes if you call oracle routes with shared secret | Match how you secure `/api/oracle/*` |
| `ADMIN_API_KEY` | Yes for admin routes | Or rely on JWT admin role |
| `STORACHA_UPLOADER_URL` | For **live** CIDs | Public **HTTPS** URL of the uploader, no trailing slash, e.g. `https://pastoral-uploader.onrender.com` |
| `STORACHA_UPLOADER_SECRET` | With URL | Same as uploader’s `STORACHA_UPLOADER_SECRET` |
| `STORACHA_FALLBACK_MOCK_ON_ERROR` | Recommended `true` for demos | If live upload fails, return mock CID and set `storage_warning` instead of failing the flow |
| `IPFS_GATEWAY_BASE` | Optional | Default `https://w3s.link/ipfs` — used for live CID gateway URLs in API responses |
| `CORS_ALLOWED_ORIGINS` | **Yes** for browser | Comma-separated origins, e.g. `https://your-app.vercel.app` |
| `DEMO_PUBLIC_ACCESS` | Set `false` for public internet | Otherwise `POST /api/demo/run` is open |

Optional chain / payments (leave empty for demo without chain):

- `BASE_RPC_URL`, `PRIVATE_KEY`, `CONTRACT_ADDRESS`, etc.

Legacy (only if you still have a web3.storage HTTP token):

- `WEB3_STORAGE_TOKEN`, `FILECOIN_UPLOAD_URL`

### Storacha uploader only (Render → 2nd Web Service → Environment)

| Variable | Required? | Notes |
|----------|------------|--------|
| `STORACHA_UPLOADER_SECRET` | **Yes** | Must match backend |
| `PORT` | Auto on Render | Render sets `PORT`; your `server.js` already uses `process.env.PORT` |
| `STORACHA_SPACE_DID` | Optional | Pin a specific space if you have multiple |
| `STORACHA_PROFILE` | Optional | Default `w3up-client` |

**Storacha email login** is not an API key in the env file: you run `npm run login -- you@email.com` **once** in an environment whose **on-disk agent store** is the same one the running service uses (see persistence below).

### Frontend (Vercel)

| Variable | Notes |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | Public URL of the FastAPI backend (HTTPS) |

Do **not** put `STORACHA_UPLOADER_SECRET`, `JWT_SECRET`, `PRIVATE_KEY`, or database URLs in the frontend.

---

## 2. Render: backend service

- **Root directory:** `backend` (or repo root with `start` pointing at uvicorn).
- **Build:** install Python deps from `pyproject.toml` / requirements.
- **Start:** e.g. `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Database:** Create Render Postgres; paste `DATABASE_URL` into the backend service (use SQLAlchemy URL form for psycopg2 as in `.env.example`).

---

## 3. Render: Storacha uploader (second service)

**Why a second service:** the FastAPI app does **not** upload to IPFS itself; it calls `STORACHA_UPLOADER_URL` (`POST /upload` with JSON + base64 body).

**Why persistence:** the uploader uses `@storacha/access` `StoreConf` (profile `w3up-client` by default). That path (`storePath` in startup logs) must **survive restarts**. On Render, attach a **persistent disk** and arrange env so that config directory lives on the disk (often `HOME` or `XDG_CONFIG_HOME` pointing at the mount, depending on where `storePath` resolves — confirm via logs or `GET /debug/storacha` with auth).

**Suggested settings:**

- **Root directory:** `storacha-uploader`
- **Runtime:** Node 18+
- **Build command:** `npm install`
- **Start command:** `npm start`
- **Disk:** mount persistent storage; ensure Storacha’s store writes there.

**After deploy:** run **one-time** Storacha login in that persisted environment (see [`storacha-uploader/README.md`](../storacha-uploader/README.md)).

---

## 4. Fallback behavior (backend)

With `STORACHA_FALLBACK_MOCK_ON_ERROR=true` (default):

- Try **live** upload to the uploader first.
- On **401** from the uploader (wrong secret): **no** fallback — fix `STORACHA_UPLOADER_SECRET` on both sides.
- On other failures (timeouts, 5xx, 503, network, missing `cid`): **mock CID** and set `storage_warning` in oracle responses; `storage_mode` is `mock`.

When `STORACHA_UPLOADER_URL` / secret are **unset**, the backend uses mock CIDs only (`storage_mode=mock`, `storage_warning` usually null).

---

## 5. Verification order

1. Backend health: `GET /docs` or `GET /health` if exposed.
2. Uploader: `GET /health` on the uploader URL.
3. Backend → uploader: trigger a flow that uploads (or run oracle) with `STORACHA_UPLOADER_URL` set; confirm `storage_mode: "live"` in JSON when healthy.
4. Pull a live CID via `IPFS_GATEWAY_BASE` / `w3s.link`.

---

## 6. Security

- Keep `STORACHA_UPLOADER_SECRET` only on server-side env.
- Restrict or protect `/debug/storacha` on the uploader (same Bearer secret as upload).
- Use HTTPS everywhere; set `CORS_ALLOWED_ORIGINS` explicitly.

For more local setup detail, see [SETUP.md](SETUP.md) and [storacha-uploader/README.md](../storacha-uploader/README.md).
