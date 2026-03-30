# PASTORALPROTECT

Fresh Code for Hackathon Submission · Infrastructure & Digital Rights Track

PastoralProtect is climate risk infrastructure specifically designed for pastoralists, not just another generic farmer app. It integrates verifiable NDVI-style triggers, Filecoin/IPFS-ready decentralized storage, optional Solidity pool validation, and mobile-money-style payout rails. This empowers insurers, cooperatives, NGOs, and governments to deliver automatic, transparent protection—eliminating manual claims and on-the-ground field inspections.

---

## PROBLEM STATEMENT

Pastoralists in drought-prone areas often lose livestock due to climate shocks. Traditional insurance coverage fails them with manual claims processing, slow verification, complex paperwork, and unreliable connectivity—leading to delayed or denied payouts and limiting the scalability of relief.

---

## SOLUTION OVERVIEW

We have developed a rules-first pipeline that follows these steps:

1. Enroll the user.
2. Archive NDVI bundles to IPFS (Filecoin ecosystem) with SHA-256 integrity.
3. Oracle verifies retrieval before any payouts execute.
4. Optional on-chain validation: Uses `validateAndPayout` for full auditability.
5. Mock M-Pesa demo payouts: Ensures end-to-end demo flow.
6. Role-based access: JWT roles (`ADMIN`, `ORACLE`, `USER`) control dashboards; architecture is cleanly split for future Lit Protocol integration.

---

## ARCHITECTURE DIAGRAM

```
[ PASTORALIST / USSD / WEB ]
        │
        ▼
 ┌───────────────────────┐
 │   FASTAPI (PYTHON)    │   Pydantic · SQLAlchemy · async IPFS upload
 │  policies · zones     │
 │  oracle · payments    │
 │  auth (JWT roles)     │
 └──────────┬────────────┘
            │ canonical JSON + CID + hash
            ▼
 ┌───────────────────────┐
 │ IPFS / FILECOIN PIN   │   web3.storage-compatible HTTP (or local mock CIDs)
 └──────────┬────────────┘
            │
 ┌──────────▼────────────┐
 │  VERIFIABLE ORACLE    │   fetch CID · verify SHA-256 · tamper rejection
 └──────────┬────────────┘
            │
 ┌──────────▼────────────┐          ┌──────────────────┐
 │ PASTORALPROTECTPOOL   │◄─────────│   web3.py txs    │   optional Base Sepolia
 │    (SOLIDITY)         │          └──────────────────┘
 └──────────┬────────────┘
            ▼
 [ Mock mobile money + admin metrics + demo mode ]
```

HOW TO FOLLOW PIPELINE IN UI:
- Sign in on the Dashboard (**Demo quick sign-in**) and monitor the README pipeline card.
- `GET /api/cycle/status` (must be admin JWT) mirrors this pipeline.
- With default mock stack, Run full demo turns all phases green. Solidity is *skipped* unless configured.

---

## FILECOIN INTEGRATION

- STORAGE PROCESS: NDVI/trigger bundles and payout records are:
  1. Serialized to canonical JSON
  2. Pinned using one of:
      - (a) [storacha-uploader](storacha-uploader/README.md) (+ `@storacha/client`)
      - (b) Legacy `WEB3_STORAGE_TOKEN` + `FILECOIN_UPLOAD_URL`
      - (c) Mock CIDs for local/demo.
  3. Fetch with `GET /api/storage/{cid}` for judges/reviewers.
- DEFAULT: Leave Storacha/token unset to use in-process mock CIDs for full end-to-end local testing.

---

## TECHNOLOGY STACK

API: FastAPI, Pydantic, Uvicorn
DATA: SQLAlchemy + PostgreSQL or SQLite
STORAGE: IPFS/Filecoin (HTTP pinning + gateway fetch)
AUTH: JWT roles (ADMIN, ORACLE, USER) — Lit-style ready
CHAIN: Solidity (PastoralProtectPool) + Hardhat + web3.py
UI: Next.js 14, Tailwind, Recharts

---

## FEATURES BUILT DURING THE HACKATHON

1. Filecoin/IPFS Storage Service
   - Async JSON upload.
   - CID + SHA-256 hashing for `NdviReading`, `TriggerEvent`, `Payout`.
   - `StorageUploadLog` for audits.
2. Verifiable Oracle Path
   - Pre-payout CID fetch + hash check.
   - Rejects any tampered bundles.
   - Surfaces `verification_passed` in API/UI.
3. JWT Access Control
   - `ADMIN` for dashboard/config.
   - `ORACLE`/`ADMIN` for `/api/oracle/simulate`.
   - `USER` seeded for extension.
   - Legacy keys still supported for script integration.
4. Impact Metrics
   - `GET /api/admin/impact` provides stats: farmers, livestock, payouts, drought events, NDVI archives.
5. Demo Mode
   - `POST /api/demo/run` executes: enroll → shock → oracle + storage + payouts.
   - Dashboard provides Run full demo button with JSON trace.
6. Retrieval API
   - `GET /api/storage/{cid}` available for external review/testing.

**Public demo (judges / reviewers):**  
- User `judge_demo` is seeded when **`SEED_JUDGE_DEMO_PASSWORD`** is set in **`backend/.env`** (never commit `.env`). Use **Demo quick sign-in** on `/dashboard`; the password must match that env value (defaults in the frontend expect the same string you set server-side).

Optional dev seeds: **`SEED_ADMIN_PASSWORD`**, **`SEED_ORACLE_PASSWORD`**, **`SEED_FARMER_PASSWORD`** — same file; empty means skip that user. See [`backend/.env.example`](backend/.env.example).

---

## STEP-BY-STEP SETUP CHECKLIST

For detailed setup, refer to [docs/SETUP.md](docs/SETUP.md).

### 1. CREDENTIALS & OPTIONAL SERVICES

- For Storacha: run [storacha-uploader](storacha-uploader/README.md), set `STORACHA_UPLOADER_URL` and `STORACHA_UPLOADER_SECRET` in `backend/.env`.
- Quick bootstrap:  
  - Windows: `.\scripts\bootstrap-local.ps1`  
  - macOS/Linux: `bash scripts/bootstrap-local.sh`  
  (Creates config files from examples if missing)

---

## HOW TO RUN LOCALLY

### STEP 1: BACKEND SETUP

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env: set at least SEED_JUDGE_DEMO_PASSWORD (must match frontend demo quick sign-in, e.g. Demo123!)
# If using old SQLite w/o new columns, delete pastoral_protect.db
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Open API docs at: `http://127.0.0.1:8000/docs`.
- Login: `POST /api/auth/login` and use Bearer token for admin/oracle functions.

### STEP 2: FRONTEND SETUP

```bash
cd frontend
npm install
cp .env.example .env.local
# Or: echo NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 > .env.local
npm run dev
```
- Visit `/dashboard` and use **Demo quick sign-in**.
- Click Run full demo or manually `/enroll` → `/simulate` (browser session must store JWT).
- Check GET /api/storage/{cid} response for demo CIDs.

### STEP 3: CONTRACTS (OPTIONAL)

```bash
cd contracts
npm install && npx hardhat test
```

## LICENSE

[MIT](LICENSE)