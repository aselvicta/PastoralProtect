"""
Decentralized storage via IPFS / Filecoin.

Priority:
1. STORACHA_UPLOADER_URL — local Node service using @storacha/client (Storacha; email auth, no legacy API keys)
2. WEB3_STORAGE_TOKEN — legacy HTTP Bearer upload (deprecated by Storacha for many accounts)
3. Mock in-memory CIDs for local demos
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_mock_blobs: dict[str, bytes] = {}


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _mock_upload(raw: bytes, label: str, digest: str) -> tuple[str, str]:
    cid = f"bafyMOCK{secrets.token_hex(12)}"
    _mock_blobs[cid] = raw
    logger.info("Storage MOCK upload label=%s cid=%s sha256=%s", label, cid, digest[:16])
    return cid, digest


class FilecoinStorageService:
    """Async JSON uploads with CID; integrity verification against raw CAR/file bytes."""

    async def upload_json(self, label: str, payload: dict[str, Any]) -> tuple[str, str]:
        raw = canonical_json_bytes(payload)
        digest = sha256_hex(raw)

        sidecar = (settings.storacha_uploader_url or "").strip().rstrip("/")
        sidecar_secret = (settings.storacha_uploader_secret or "").strip()
        if sidecar and sidecar_secret:
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    r = await client.post(
                        f"{sidecar}/upload",
                        json={
                            "label": label,
                            "body_b64": base64.b64encode(raw).decode("ascii"),
                        },
                        headers={"Authorization": f"Bearer {sidecar_secret}"},
                    )
                    if r.status_code == 401:
                        raise ValueError(
                            "Storacha uploader returned 401 (secret mismatch). Set "
                            "STORACHA_UPLOADER_SECRET in backend/.env to the exact same value "
                            "as STORACHA_UPLOADER_SECRET when you run npm start in storacha-uploader."
                        )
                    if r.status_code == 503:
                        detail = ""
                        try:
                            detail = (r.json() or {}).get("detail", "")
                        except Exception:
                            detail = r.text[:500]
                        if settings.storacha_fallback_mock_on_error:
                            logger.warning(
                                "Storacha uploader 503; using mock CID (STORACHA_FALLBACK_MOCK_ON_ERROR=true). %s",
                                detail.strip() or "bridge not ready",
                            )
                            return _mock_upload(raw, label, digest)
                        raise ValueError(
                            f"Storacha uploader not ready (503). {detail}".strip()
                        )
                    r.raise_for_status()
                    body = r.json()
                    cid = body.get("cid")
                    if not cid:
                        raise ValueError(f"Storacha uploader response missing cid: {body!r}")
                logger.info("Storage Storacha (sidecar) label=%s cid=%s sha256=%s", label, cid, digest[:16])
                return str(cid), digest
            except Exception:
                logger.exception("Storacha sidecar upload failed label=%s", label)
                raise

        token = (settings.web3_storage_token or "").strip()
        if not token:
            return _mock_upload(raw, label, digest)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": (f"{label}.json", raw, "application/json")}
                headers = {"Authorization": f"Bearer {token}"}
                r = await client.post(settings.filecoin_upload_url, headers=headers, files=files)
                r.raise_for_status()
                body = r.json()
                cid = body.get("cid") or body.get("Cid")
                if not cid:
                    raise ValueError(f"Upload response missing cid: {body!r}")
            logger.info("Storage legacy HTTP upload label=%s cid=%s sha256=%s", label, cid, digest[:16])
            return str(cid), digest
        except Exception:
            logger.exception("Storage upload failed label=%s", label)
            raise

    async def fetch_raw(self, cid: str) -> bytes:
        cid = cid.strip()
        if cid in _mock_blobs:
            return _mock_blobs[cid]
        base = settings.ipfs_gateway_base.rstrip("/")
        url = f"{base}/{cid}"
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.content

    async def fetch_json(self, cid: str) -> Any:
        raw = await self.fetch_raw(cid)
        return json.loads(raw.decode("utf-8"))

    async def verify_cid_matches_hash(self, cid: str, expected_sha256_hex: str) -> tuple[bool, Optional[str]]:
        try:
            raw = await self.fetch_raw(cid)
        except Exception as e:  # noqa: BLE001
            return False, f"fetch failed: {e!s}"
        got = sha256_hex(raw)
        if not secrets.compare_digest(got.lower(), expected_sha256_hex.lower()):
            return False, f"hash mismatch expected={expected_sha256_hex[:12]} got={got[:12]}"
        return True, None


filecoin_storage_service = FilecoinStorageService()
