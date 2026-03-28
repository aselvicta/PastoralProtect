# Future work (not in this repo)

This hackathon demo is **complete for judges and GitHub clones** using SQLite, mock storage CIDs, and mock mobile-money flows. The following are **intentionally out of scope** here; treat them as product / integration follow-ups.

| Area | Notes |
|------|--------|
| **Real M-Pesa** | Safaricom (Daraja) Till, Pay Bill, B2C, etc. require business registration, shortcodes, consumer key/secret, passkey, and often IP allowlisting. No M-Pesa env vars are wired in this codebase; payouts are **simulated** for demo. |
| **Production PostgreSQL** | Swap `DATABASE_URL` to a managed Postgres (Neon, Supabase, RDS, Railway, …) when you deploy; run migrations if you add schema changes. SQLite remains the default for local clones. |
| **Live satellite / NDVI feeds** | The oracle accepts **simulated** NDVI values via API/UI. Plugging in Copernicus, Planet, or a commercial feed is a separate data pipeline (scheduling, cloud masks, zonal stats, API keys). |
| **Storacha for every cloner** | **Not required.** Leaving `STORACHA_UPLOADER_*` and `WEB3_STORAGE_TOKEN` empty uses **in-memory mock CIDs** so the full demo loop works offline. Real uploads are optional; see [SETUP.md §2](SETUP.md). |

When you implement any of the above, add new env vars and document them in `backend/.env.example` — do not commit real secrets.
