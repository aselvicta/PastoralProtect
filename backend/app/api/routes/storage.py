import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.services.filecoin_storage_service import filecoin_storage_service

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/{cid}")
async def get_by_cid(cid: str, raw: bool = False) -> Any:
    """Retrieve JSON archived by CID (IPFS / Filecoin pinning via web3.storage-compatible API)."""
    c = cid.strip()
    try:
        blob = await filecoin_storage_service.fetch_raw(c)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Could not fetch CID: {e!s}") from e
    if raw:
        return PlainTextResponse(content=blob.decode("utf-8", errors="replace"), media_type="text/plain; charset=utf-8")
    try:
        return json.loads(blob.decode("utf-8"))
    except json.JSONDecodeError:
        return {"raw_base64": blob.hex()}
