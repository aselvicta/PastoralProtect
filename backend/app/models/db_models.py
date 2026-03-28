from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """JWT auth users; roles ADMIN / ORACLE / USER — swap for Lit PKP-wrapped keys later."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farmer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(32), index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(8), default="sw")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    contract_zone_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(255))
    ndvi_threshold: Mapped[float] = mapped_column(Float)  # 0-1 scale in DB
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
    )

    policies: Mapped[list["Policy"]] = relationship(back_populates="zone")


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farmer_id: Mapped[str] = mapped_column(String(64), index=True)
    zone_db_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))
    livestock_count: Mapped[int] = mapped_column(Integer)
    premium_amount: Mapped[int] = mapped_column(Integer)  # mock TZS
    status: Mapped[str] = mapped_column(String(32), default="active")
    enrolled_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))
    last_payout_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    contract_policy_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enroll_tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    zone: Mapped["Zone"] = relationship(back_populates="policies")
    payouts: Mapped[list["Payout"]] = relationship(back_populates="policy")


class NdviReading(Base):
    __tablename__ = "ndvi_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_db_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    ndvi_value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(64), default="mock")
    content_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    storage_cid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class TriggerEvent(Base):
    __tablename__ = "trigger_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_db_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), index=True)
    week: Mapped[int] = mapped_column(Integer)
    ndvi_value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    breached: Mapped[bool] = mapped_column(Boolean)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    storage_cid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    verification_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    verification_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), index=True)
    farmer_id: Mapped[str] = mapped_column(String(64), index=True)
    zone_db_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    week: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    provider: Mapped[str] = mapped_column(String(64), default="mock-mpesa")
    provider_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    storage_cid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))
    completed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    policy: Mapped["Policy"] = relationship(back_populates="payouts")
    payment_logs: Mapped[list["PaymentLog"]] = relationship(back_populates="payout")


class PaymentLog(Base):
    __tablename__ = "payment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payout_id: Mapped[int] = mapped_column(ForeignKey("payouts.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    request_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))

    payout: Mapped["Payout"] = relationship(back_populates="payment_logs")


class OracleExecutionLog(Base):
    __tablename__ = "oracle_execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_db_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), index=True)
    week: Mapped[int] = mapped_column(Integer)
    ndvi_value: Mapped[float] = mapped_column(Float)
    action_taken: Mapped[str] = mapped_column(String(255))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class StorageUploadLog(Base):
    __tablename__ = "storage_upload_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_kind: Mapped[str] = mapped_column(String(32), index=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    cid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))
