from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db_models import PaymentLog, Payout


class PaymentService:
    async def execute_mock_payout(self, db: Session, payout: Payout) -> tuple[str, str]:
        delay = max(0, settings.mock_payment_delay_ms) / 1000.0
        await asyncio.sleep(delay)
        ref = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
        payout.provider_reference = ref
        payout.status = "completed"
        payout.completed_at = datetime.now(timezone.utc)
        log = PaymentLog(
            payout_id=payout.id,
            provider=payout.provider,
            status="success",
            request_payload=json.dumps({"payout_id": payout.id, "amount": payout.amount}),
            response_payload=json.dumps({"reference": ref, "status": "success"}),
        )
        db.add(log)
        db.flush()
        return ref, "success"


payment_service = PaymentService()
