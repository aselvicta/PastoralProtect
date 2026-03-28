# PASTORALPROTECT

Fresh Code for Hackathon Submission · Infrastructure & Digital Rights Track

PastoralProtect is climate risk infrastructure specifically designed for pastoralists, not just another generic farmer app. It integrates verifiable NDVI-style triggers, Filecoin/IPFS-ready decentralized storage, optional Solidity pool validation, and mobile-money-style payout rails. This empowers insurers, cooperatives, NGOs, and governments to deliver automatic, transparent protection—eliminating manual claims and on-the-ground field inspections.

---

## DEMO QUICKSTART OVERVIEW

| GOAL                       | WHAT YOU NEED                                                                                                      |
|----------------------------|--------------------------------------------------------------------------------------------------------------------|
| RUN THE FULL UI + API LOOP | `backend/.env` from `.env.example`, `frontend/.env.local` from `frontend/.env.example`, SQLite default—no Storacha, chain, or paid APIs. |
| REAL IPFS/FILECOIN PINS    | Optional: [storacha-uploader](storacha-uploader/README.md) or legacy `WEB3_STORAGE_TOKEN`. See [docs/SETUP.md](docs/SETUP.md). |
| ON-CHAIN POOL              | Optional: `BASE_RPC_URL`, funded `PRIVATE_KEY`, deploy contract, `CONTRACT_ADDRESS`. See [docs/SETUP.md](docs/SETUP.md). |
| PRODUCTION-STYLE DEPLOY    | PostgreSQL `DATABASE_URL`, `DEMO_PUBLIC_ACCESS=false`, strong secrets, HTTPS. See [docs/SETUP.md](docs/SETUP.md). |

- STORAGE: Mock CIDs are sufficient for a complete demo; real Storacha is optional.
- NOT INCLUDED: Real M-Pesa, production-only concerns, and live satellite feeds. See [docs/FUTURE_WORK.md](docs/FUTURE_WORK.md).

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
- Sign in as `admin` on the Dashboard and monitor the README pipeline card.
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

| LAYER     | STACK                                                         |
|-----------|---------------------------------------------------------------|
| API       | FastAPI, Pydantic, Uvicorn                                    |
| DATA      | SQLAlchemy + PostgreSQL or SQLite                             |
| STORAGE   | IPFS/Filecoin (HTTP pinning + gateway fetch)                  |
| AUTH      | JWT roles (`ADMIN`, `ORACLE`, `USER`)—Lit-style ready         |
| CHAIN     | Solidity (`PastoralProtectPool`) + Hardhat + web3.py          |
| UI        | Next.js 14, Tailwind, Recharts                                |

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

SEEDED LOGINS:  
- `admin` / `Admin123!`  
- `oracle` / `Oracle123!`  
- `farmer` / `User123!`  

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
- Visit `/dashboard` and login as `admin`.
- Click Run full demo or manually `/enroll` → `/simulate` (browser session must store JWT).
- Check GET /api/storage/{cid} response for demo CIDs.

### STEP 3: CONTRACTS (OPTIONAL)

```bash
cd contracts
npm install && npx hardhat test
```

---

## DEMO FLOW IN 4 SIMPLE STEPS (3 MINUTES)

1. Understand the Problem: Pastoralists suffer losses in droughts; insurance is too slow and inefficient.
2. Experience the Solution: Rules-driven flow—NDVI bundles archived to Filecoin/IPFS, with verifiable triggers and automatic payouts.
3. See the Live Pipeline:  
   - Enroll user  
   - Simulate drought (NDVI drops below threshold)  
   - Oracle verifies CID and hash  
   - Payouts executed, dashboard impact metrics updated
4. Conclude: “No claims. No paperwork. Just rules-based, verifiable protection.”

JUDGES' SUMMARY:  
“We built climate risk infrastructure powered by verifiable data and decentralized storage—not just another mobile app for farmers.”

---

## MVP SECURITY NOTES

- Always set `DEMO_PUBLIC_ACCESS=false` and rely on JWT security for all demo execution in any public deployment.
- Regularly rotate `JWT_SECRET`, `ORACLE_SECRET`, and `WEB3_STORAGE_TOKEN`.
- You may replace pbkdf2 password hashes with your organization’s standard algorithm.

---

## LICENSE

[MIT](LICENSE)
