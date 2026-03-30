# PastoralProtect: credentials and complete setup checklist

Use this document together with [README.md](../README.md). Nothing here replaces rotating secrets for production.

## 1. Minimum path (local demo, no paid services)

You can run the full stack **without** blockchain keys or Filecoin tokens.

| Step | Action |
|------|--------|
| Backend env | Copy [`backend/.env.example`](../backend/.env.example) to `backend/.env` and set **`SEED_JUDGE_DEMO_PASSWORD`** (and optional `SEED_*` for dev users). Or run [`scripts/bootstrap-local.ps1`](../scripts/bootstrap-local.ps1) / [`scripts/bootstrap-local.sh`](../scripts/bootstrap-local.sh) once (creates env files if missing). Also: SQLite `DATABASE_URL`, `JWT_SECRET`, `ORACLE_SECRET`, `ADMIN_API_KEY`. |
| Frontend env | Copy [`frontend/.env.example`](../frontend/.env.example) to `frontend/.env.local` and adjust `NEXT_PUBLIC_API_BASE_URL` if the API is not on `http://127.0.0.1:8000`. The bootstrap scripts also create this file when missing. |
| Python | From `backend/`: `python -m pip install -r requirements.txt` |
| Node | From `frontend/`, `contracts/`, and (optional) [`storacha-uploader/`](../storacha-uploader/): `npm install` as needed |
| Run API | From `backend/`: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Run UI | From `frontend/`: `npm run dev` |

**No secrets required** for: Storacha bridge (leave `STORACHA_UPLOADER_*` empty), legacy IPFS token (leave `WEB3_STORAGE_TOKEN` empty), chain (leave `BASE_RPC_URL`, `PRIVATE_KEY`, `CONTRACT_ADDRESS` empty), real M-Pesa.

**Demo logins** are created only from **`SEED_*_PASSWORD`** in `backend/.env` (see [`backend/.env.example`](../backend/.env.example)). Set at least **`SEED_JUDGE_DEMO_PASSWORD`** for the judge sandbox; leave others empty to skip. **Not production-safe** — rotate for real deployments.

---

## 2. Optional: real Storacha uploads (recommended — no legacy API keys)

Storacha has moved to **email login** + `@storacha/client`; many accounts no longer have HTTP **API tokens**.

| Credential | Env var | Notes |
|------------|---------|--------|
| Uploader base URL | `STORACHA_UPLOADER_URL` | e.g. `http://127.0.0.1:8788` — [storacha-uploader](../storacha-uploader/) Node service. |
| Shared secret | `STORACHA_UPLOADER_SECRET` | Same value in the uploader’s `STORACHA_UPLOADER_SECRET` env; protects `POST /upload`. |
| Gateway | `IPFS_GATEWAY_BASE` | Default `https://w3s.link/ipfs` — used when fetching CIDs for verification (Storacha serves via w3s / compatible gateways). |

**Steps:** See [`storacha-uploader/README.md`](../storacha-uploader/README.md): `npm install`, `npm run login -- you@email.com`, set secret, `npm start`, then point `backend/.env` at the uploader URL + secret.

---

## 2b. Legacy: HTTP Bearer upload (web3.storage-style)

| Credential | Env var | Notes |
|------------|---------|--------|
| API token | `WEB3_STORAGE_TOKEN` | Only if your provider still issues a Bearer token for `FILECOIN_UPLOAD_URL`. Lower priority than `STORACHA_UPLOADER_URL`. |
| Upload URL | `FILECOIN_UPLOAD_URL` | Default `https://api.web3.storage/upload`. |

If neither Storacha uploader nor legacy token is configured, the app uses **mock CIDs** locally for demos.

---

## 3. Optional: Base / Solidity pool

| Credential | Env var | Notes |
|------------|---------|--------|
| RPC URL | `BASE_RPC_URL` | Base Sepolia public RPC or Alchemy/Infura URL (API key is in the URL). |
| Deployer / tx key | `PRIVATE_KEY` | Hex private key for the wallet that deploys and sends txs — **never commit**. |
| Admin key | `ADMIN_PRIVATE_KEY` | If the backend uses a separate admin signer for pool calls — see backend config. |
| Contract address | `CONTRACT_ADDRESS` | After `npx hardhat run` deploy script; paste address. |
| Artifact path | `CONTRACT_ARTIFACT_PATH` | Points to Hardhat JSON artifact (`PastoralProtectPool.json`). |

See also [`contracts/.env.example`](../contracts/.env.example) for `BASE_RPC_URL`, `PRIVATE_KEY`, `ADMIN_ADDRESS`, `ORACLE_ADDRESS` used by deploy scripts.

Fund the wallet with **Base Sepolia** ETH from a faucet before deploying.

---

## 4. API auth model (what each secret is for)

- **`JWT_SECRET`**: signs access tokens; use a long random value in production.
- **`ORACLE_SECRET`**, **`ADMIN_API_KEY`**: optional legacy header auth for scripts (`X-Oracle-Secret`, `X-Admin-Key`).
- **`JWT_EXPIRE_MINUTES`**: session lifetime (default 480).

---

## 5. Demo / kiosk safety

| Env | Purpose |
|-----|---------|
| `DEMO_PUBLIC_ACCESS` | If `true`, `POST /api/demo/run` works **without** JWT. Set **`false`** for any public deployment; require JWT. |

---

## 6. Tunables (not third-party credentials)

From `backend/.env.example`: `MOCK_PAYMENT_DELAY_MS`, `PAYOUT_PER_HEAD`, `CHAIN_ENROLL_VALUE_WEI`, `PORT`.

---

## 7. Production / deployment

- **Database**: PostgreSQL `DATABASE_URL` (replace SQLite).
- **HTTPS**: terminate TLS at the host; set **`NEXT_PUBLIC_API_BASE_URL`** in the frontend to your public API URL.
- **CORS**: ensure FastAPI allows your frontend origin when exposing the API publicly.
- **Rotate**: `JWT_SECRET`, `ORACLE_SECRET`, `WEB3_STORAGE_TOKEN`, demo user passwords; consider disabling seed users.

**Not implemented in this repo** (no env vars today): real **M-Pesa** (Safaricom APIs); live **satellite** feeds — future integrations.

See also **[FUTURE_WORK.md](FUTURE_WORK.md)** for M-Pesa, managed Postgres, and live NDVI feeds as explicit follow-ups.

---

## Quick “what to bring” summary

1. **Always**: `backend/.env` from `.env.example`, `frontend/.env.local` from `frontend/.env.example`, run backend + frontend, use seeded logins or JWT from `POST /api/auth/login`.
2. **For Filecoin/IPFS (real Storacha)**: run `storacha-uploader` (see §2), set `STORACHA_UPLOADER_URL` + `STORACHA_UPLOADER_SECRET` in `backend/.env`. **Legacy**: `WEB3_STORAGE_TOKEN` only (deprecated HTTP API keys).
3. **For chain**: funded Base Sepolia wallet, RPC URL, `PRIVATE_KEY`, deploy contract, set `CONTRACT_ADDRESS` and artifact path.
4. **For public internet**: `DEMO_PUBLIC_ACCESS=false`, strong secrets, PostgreSQL, HTTPS, rotated passwords.

No external service is **required** for the core demo loop; everything else is optional.
