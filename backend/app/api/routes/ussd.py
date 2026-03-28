from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from app.api.deps import DbSession
from app.api.routes import policies as policies_routes
from app.models.db_models import Zone
from app.schemas.policies import EnrollRequest as ER

router = APIRouter(prefix="/ussd", tags=["ussd"])
logger = logging.getLogger(__name__)

SESSIONS: dict[str, dict[str, Any]] = {}


class UssdBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    service_code: str = Field(default="*123#", alias="serviceCode")
    phone_number: str = Field(..., alias="phoneNumber")
    text: str = ""


def con(msg: str) -> str:
    return f"CON {msg}"


def end(msg: str) -> str:
    return f"END {msg}"


@router.post("", response_class=PlainTextResponse)
def ussd(body: UssdBody, db: DbSession) -> str:
    sid = body.session_id
    parts = body.text.split("*") if body.text else [""]

    if body.text == "" or body.text.strip() == "":
        SESSIONS.pop(sid, None)
        return con("Karibu PastoralProtect.\n1. Jiunge na kinga\n2. Angalia hali ya bima\n3. Kuhusu huduma")

    st = SESSIONS.get(sid, {"step": "menu"})

    if parts[0] == "3":
        return end("PastoralProtect: kinga ya mifugo kihali-hewa. Demo USSD.")

    if parts[0] == "2":
        return end("Hali ya bima: tumia dashboard au piga *123# baadaye (demo).")

    if parts[0] != "1":
        return end("Chaguo si sahihi.")

    # Enrollment path 1*...
    if len(parts) == 1:
        zones = db.execute(select(Zone).where(Zone.is_active.is_(True))).scalars().all()
        lines = "\n".join([f"{z.contract_zone_id}. {z.zone_id} {z.name}" for z in zones])
        SESSIONS[sid] = {"step": "zone", "phone": body.phone_number}
        return con(f"Chagua eneo la malisho:\n{lines}")

    if len(parts) == 2:
        choice = parts[1]
        zone = db.execute(select(Zone).where(Zone.contract_zone_id == int(choice))).scalar_one_or_none()
        if zone is None:
            zone = db.execute(select(Zone).where(Zone.zone_id == choice)).scalar_one_or_none()
        if zone is None:
            return end("Eneo halijulikani.")
        st.update({"step": "livestock", "zone_id": zone.zone_id})
        SESSIONS[sid] = st
        return con("Ingiza idadi ya mifugo (namba):")

    if len(parts) == 3:
        try:
            n = int(parts[2])
            if n < 1:
                raise ValueError
        except ValueError:
            return end("Nambari si sahihi.")
        st.update({"livestock": n})
        SESSIONS[sid] = st
        return con("Ingiza malipo ya kinga (TZS, mfano 5000):")

    if len(parts) == 4:
        try:
            prem = int(parts[3])
            if prem < 1:
                raise ValueError
        except ValueError:
            return end("Malipo si sahihi.")
        st.update({"premium": prem})
        SESSIONS[sid] = st
        zid: str = st.get("zone_id", "")
        return con(f"Thibitisha: Eneo {zid}, mifugo {st.get('livestock')}, malipo {prem} TZS.\n1. Ndio\n2. Hapana")

    if len(parts) == 5:
        if parts[4] != "1":
            SESSIONS.pop(sid, None)
            return end("Umefuta usajili.")
        farmer_id = f"USSD-{body.phone_number[-9:]}"
        req = ER(
            farmer_id=farmer_id,
            phone_number=body.phone_number,
            zone_id=st.get("zone_id", ""),
            livestock_count=int(st.get("livestock", 0)),
            premium_amount=int(st.get("premium", 0)),
            preferred_language="sw",
        )
        try:
            res = policies_routes.enroll(req, db)
        except HTTPException as he:
            SESSIONS.pop(sid, None)
            detail = he.detail if isinstance(he.detail, str) else "Usajili umeshindwa."
            return end(detail)
        except Exception as e:  # noqa: BLE001
            SESSIONS.pop(sid, None)
            return end(f"Hitilafu kwenye usajili: {e!s}")
        SESSIONS.pop(sid, None)
        logger.info("ussd.enroll_ok farmer_id=%s zone=%s", farmer_id, st.get("zone_id"))
        return end(f"Asante. {res.enrollment_message}")

    return end("Muundo si sahihi.")
