from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from eth_account import Account
from web3 import Web3
from web3.contract import Contract

from app.core.config import settings
from app.utils.numeric import ndvi_to_micro


class ContractService:
    def __init__(self) -> None:
        self._w3: Optional[Web3] = None
        self._contract: Optional[Contract] = None

    def enabled(self) -> bool:
        return bool(
            settings.base_rpc_url
            and settings.contract_address
            and settings.private_key
            and Path(settings.contract_artifact_path).is_file()
        )

    def _ensure(self) -> tuple[Web3, Contract]:
        if self._w3 is None:
            self._w3 = Web3(Web3.HTTPProvider(settings.base_rpc_url))
        if self._contract is None:
            path = Path(settings.contract_artifact_path)
            with path.open(encoding="utf-8") as f:
                artifact = json.load(f)
            abi = artifact["abi"]
            self._contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(settings.contract_address),
                abi=abi,
            )
        assert self._contract is not None
        assert self._w3 is not None
        return self._w3, self._contract

    def admin_account(self) -> Account:
        key = settings.admin_private_key or settings.private_key
        return Account.from_key(key)

    def oracle_account(self) -> Account:
        return Account.from_key(settings.private_key)

    def enroll_policy(
        self,
        farmer_id: str,
        contract_zone_id: int,
        livestock_count: int,
        farmer_wallet: Optional[str],
    ) -> tuple[str, int]:
        w3, c = self._ensure()
        acct = self.admin_account()
        to_addr = (
            Web3.to_checksum_address(farmer_wallet)
            if farmer_wallet
            else Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        )
        fn = c.functions.enrollPolicy(
            farmer_id,
            int(contract_zone_id),
            int(livestock_count),
            to_addr,
        )
        tx = fn.build_transaction(
            {
                "from": acct.address,
                "value": int(settings.chain_enroll_value_wei),
                "nonce": w3.eth.get_transaction_count(acct.address),
                "chainId": w3.eth.chain_id,
            }
        )
        tx["gas"] = int(tx.get("gas", 600_000) * 1.2) if tx.get("gas") else 800_000
        if "maxFeePerGas" not in tx and "gasPrice" not in tx:
            tx["gasPrice"] = w3.eth.gas_price

        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        h = w3.eth.send_raw_transaction(raw)
        receipt = w3.eth.wait_for_transaction_receipt(h)
        policy_id = self._parse_policy_id_from_receipt(c, receipt)
        tx_hex = receipt["transactionHash"].hex()
        if tx_hex and not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex, policy_id

    def validate_and_payout(
        self,
        contract_zone_id: int,
        ndvi_value: float,
        week: int,
        policy_contract_ids: list[int],
        amounts: list[int],
    ) -> str:
        w3, c = self._ensure()
        acct = self.oracle_account()
        ndvi_micro = ndvi_to_micro(ndvi_value)
        fn = c.functions.validateAndPayout(
            int(contract_zone_id),
            int(ndvi_micro),
            int(week),
            [int(x) for x in policy_contract_ids],
            [int(x) for x in amounts],
        )
        tx = fn.build_transaction(
            {
                "from": acct.address,
                "nonce": w3.eth.get_transaction_count(acct.address),
                "chainId": w3.eth.chain_id,
            }
        )
        tx["gas"] = int(tx.get("gas", 900_000) * 1.2) if tx.get("gas") else 900_000
        if "maxFeePerGas" not in tx and "gasPrice" not in tx:
            tx["gasPrice"] = w3.eth.gas_price

        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        h = w3.eth.send_raw_transaction(raw)
        receipt = w3.eth.wait_for_transaction_receipt(h)
        tx_hex = receipt["transactionHash"].hex()
        if tx_hex and not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex

    def add_zone_chain(
        self,
        contract_zone_id: int,
        name: str,
        ndvi_threshold: float,
        is_active: bool = True,
    ) -> str:
        w3, c = self._ensure()
        acct = self.admin_account()
        micro = ndvi_to_micro(ndvi_threshold)
        fn = c.functions.addZone(
            int(contract_zone_id),
            name,
            int(micro),
            bool(is_active),
        )
        tx = fn.build_transaction(
            {
                "from": acct.address,
                "nonce": w3.eth.get_transaction_count(acct.address),
                "chainId": w3.eth.chain_id,
            }
        )
        tx["gas"] = 500_000
        if "maxFeePerGas" not in tx and "gasPrice" not in tx:
            tx["gasPrice"] = w3.eth.gas_price
        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        h = w3.eth.send_raw_transaction(raw)
        receipt = w3.eth.wait_for_transaction_receipt(h)
        tx_hex = receipt["transactionHash"].hex()
        if tx_hex and not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex

    def update_zone_threshold_chain(self, contract_zone_id: int, ndvi_threshold: float) -> str:
        w3, c = self._ensure()
        acct = self.admin_account()
        micro = ndvi_to_micro(ndvi_threshold)
        fn = c.functions.updateZoneThreshold(int(contract_zone_id), int(micro))
        tx = fn.build_transaction(
            {
                "from": acct.address,
                "nonce": w3.eth.get_transaction_count(acct.address),
                "chainId": w3.eth.chain_id,
            }
        )
        tx["gas"] = 300_000
        if "maxFeePerGas" not in tx and "gasPrice" not in tx:
            tx["gasPrice"] = w3.eth.gas_price
        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        h = w3.eth.send_raw_transaction(raw)
        receipt = w3.eth.wait_for_transaction_receipt(h)
        tx_hex = receipt["transactionHash"].hex()
        if tx_hex and not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex

    def pool_metrics(self) -> Optional[dict[str, Any]]:
        if not self.enabled():
            return None
        _, c = self._ensure()
        p, pay, n = c.functions.getPoolMetrics().call()
        return {
            "premiums_wei": str(p),
            "payouts_recorded": str(pay),
            "active_policies": int(n),
        }

    @staticmethod
    def _parse_policy_id_from_receipt(contract: Contract, receipt: Any) -> int:
        try:
            events = contract.events.PolicyEnrolled().process_receipt(receipt)
            if events:
                return int(events[0]["args"]["policyId"])
        except Exception:
            pass
        return 0


contract_service = ContractService()
