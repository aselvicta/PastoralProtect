"""Run from backend/: set PYTHONPATH to this directory's parent (backend root).

Requires SEED_ORACLE_PASSWORD in the environment (same as API .env).
"""

import os

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    oracle_pw = (os.environ.get("SEED_ORACLE_PASSWORD") or "").strip()
    if not oracle_pw:
        raise SystemExit("Set SEED_ORACLE_PASSWORD (e.g. from backend/.env) to run smoke test.")

    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": "oracle", "password": oracle_pw})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        z = c.get("/api/zones")
        assert z.status_code == 200
        print("zones", len(z.json()))

        r2 = c.post(
            "/api/oracle/simulate",
            headers=headers,
            json={"zone_id": "Z1", "ndvi_value": 0.1, "week": 7},
        )
        assert r2.status_code == 200, r2.text
        body = r2.json()
        print("oracle ok", body.get("storage_cid", "")[:24], "verify", body.get("verification_passed"))


if __name__ == "__main__":
    main()
