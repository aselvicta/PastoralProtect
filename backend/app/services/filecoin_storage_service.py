"""
Decentralized storage via IPFS / Filecoin.

Priority:
1. STORACHA_UPLOADER_URL — Node service using @storacha/client (Storacha; email auth, no legacy API keys)
2. WEB3_STORAGE_TOKEN — legacy HTTP Bearer upload (deprecated by Storacha for many accounts)
3. Mock in-memory CIDs for local demos

When STORACHA_FALLBACK_MOCK_ON_ERROR is true, Storacha (or legacy HTTP) failures fall back to mock CIDs
with storage_mode=mock and a warning string — except 401 from the uploader (secret mismatch), which always fails fast.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from typing import Any, Literal, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_mock_blobs: dict[str, bytes] = {}


class StorachaUploaderAuthError(ValueError):
    """401 from uploader — wrong STORACHA_UPLOADER_SECRET; do not mask with mock CID."""


@dataclass(frozen=True)
class StorageUploadResult:
    cid: str
    content_sha256: str
    storage_mode: Literal["live", "mock"]
    gateway_url: Optional[str] = None
    warning: Optional[str] = None


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _live_gateway_url(cid: str) -> str:
    base = settings.ipfs_gateway_base.rstrip("/")
    return f"{base}/{cid.strip()}"


def _mock_upload_result(
    raw: bytes,
    label: str,
    digest: str,
    *,
    warning: Optional[str] = None,
    no_warning: bool = False,
) -> StorageUploadResult:
    cid = f"bafyMOCK{secrets.token_hex(12)}"
    _mock_blobs[cid] = raw
    if no_warning:
        w: Optional[str] = None
    elif warning is not None:
        w = warning
    else:
        w = "Storacha upload unavailable; using in-memory mock CID for demo continuity."
    logger.info(
        "Storage MOCK upload label=%s cid=%s sha256=%s storage_mode=mock",
        label,
        cid,
        digest[:16],
    )
    return StorageUploadResult(
        cid=cid,
        content_sha256=digest,
        storage_mode="mock",
        gateway_url=None,
        warning=w,
    )


def _extract_error_detail(r: httpx.Response) -> str:
    try:
        body = r.json()
        if isinstance(body, dict):
            return str(body.get("detail", body))
    except Exception:
        pass
    return (r.text or "")[:500]


class FilecoinStorageService:
    """Async JSON uploads with CID; integrity verification against gateway or in-memory mock store."""

    async def upload_json(self, label: str, payload: dict[str, Any]) -> StorageUploadResult:
        raw = canonical_json_bytes(payload)
        digest = sha256_hex(raw)

        sidecar = (settings.storacha_uploader_url or "").strip().rstrip("/")
        sidecar_secret = (settings.storacha_uploader_secret or "").strip()
        if sidecar and sidecar_secret:
            return await self._upload_via_storacha_sidecar(label, raw, digest)

        token = (settings.web3_storage_token or "").strip()
        if not token:
            return _mock_upload_result(raw, label, digest, no_warning=True)

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
            cid_s = str(cid)
            logger.info("Storage legacy HTTP upload label=%s cid=%s sha256=%s", label, cid_s, digest[:16])
            return StorageUploadResult(
                cid=cid_s,
                content_sha256=digest,
                storage_mode="live",
                gateway_url=_live_gateway_url(cid_s),
                warning=None,
            )
        except Exception as e:
            logger.exception("Storage legacy HTTP upload failed label=%s", label)
            if settings.storacha_fallback_mock_on_error:
                return _mock_upload_result(
                    raw,
                    label,
                    digest,
                    warning=f"Legacy web3.storage upload failed: {e!s}",
                )
            raise

    async def _upload_via_storacha_sidecar(self, label: str, raw: bytes, digest: str) -> StorageUploadResult:
        sidecar = (settings.storacha_uploader_url or "").strip().rstrip("/")
        sidecar_secret = (settings.storacha_uploader_secret or "").strip()

        def success_result(cid_str: str) -> StorageUploadResult:
            logger.info(
                "Storage Storacha (sidecar) label=%s cid=%s sha256=%s storage_mode=live",
                label,
                cid_str,
                digest[:16],
            )
            return StorageUploadResult(
                cid=cid_str,
                content_sha256=digest,
                storage_mode="live",
                gateway_url=_live_gateway_url(cid_str),
                warning=None,
            )

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
                    raise StorachaUploaderAuthError(
                        "Storacha uploader returned 401 (secret mismatch). Set "
                        "STORACHA_UPLOADER_SECRET in backend/.env to the exact same value "
                        "as STORACHA_UPLOADER_SECRET when you run npm start in storacha-uploader."
                    )
                if r.is_success:
                    body = r.json()
                    cid = body.get("cid")
                    if not cid:
                        raise ValueError(f"Storacha uploader response missing cid: {body!r}")
                    return success_result(str(cid))

                detail = _extract_error_detail(r).strip() or "bridge error"
                err_msg = f"Storacha uploader HTTP {r.status_code}: {detail}"
                if settings.storacha_fallback_mock_on_error:
                    logger.warning(
                        "Storacha sidecar non-success; mock fallback (STORACHA_FALLBACK_MOCK_ON_ERROR=true). %s",
                        err_msg,
                    )
                    return _mock_upload_result(raw, label, digest, warning=err_msg)
                raise ValueError(err_msg)
        except StorachaUploaderAuthError:
            raise
        except httpx.HTTPError as e:
            err_msg = f"Storacha uploader unreachable: {e!s}"
            if settings.storacha_fallback_mock_on_error:
                logger.warning(
                    "Storacha sidecar request failed; mock fallback (STORACHA_FALLBACK_MOCK_ON_ERROR=true). %s",
                    err_msg,
                )
                return _mock_upload_result(raw, label, digest, warning=err_msg)
            raise ValueError(err_msg) from e
        except ValueError as e:
            if settings.storacha_fallback_mock_on_error:
                logger.warning(
                    "Storacha sidecar failed; mock fallback (STORACHA_FALLBACK_MOCK_ON_ERROR=true). %s",
                    e,
                )
                return _mock_upload_result(raw, label, digest, warning=str(e))
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
