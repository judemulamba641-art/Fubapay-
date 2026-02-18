from decimal import Decimal
from web3 import Web3
from web3.exceptions import TransactionNotFound
from typing import Optional, Dict
import time
import os

from .networks import NetworkManager


# ==========================================================
# MINIMAL ERC20 ABI
# ==========================================================

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
]


# ==========================================================
# GAS STRATEGY
# ==========================================================

class GasStrategy:

    @staticmethod
    def aggressive(web3: Web3) -> int:
        return int(web3.eth.gas_price * 1.2)

    @staticmethod
    def medium(web3: Web3) -> int:
        return int(web3.eth.gas_price * 1.1)

    @staticmethod
    def slow(web3: Web3) -> int:
        return web3.eth.gas_price


# ==========================================================
# USDC SERVICE PRO
# ==========================================================

class USDCService:

    MIN_CONFIRMATIONS = 3
    MAX_RETRIES = 3

    def __init__(self, network_name: str):

        self.network = NetworkManager(network_name)
        self.web3 = self.network.web3

        self.contract = self.network.get_erc20_contract(
            self.network.config.usdc_contract,
            ERC20_ABI
        )

        self.decimals = 6

    # ------------------------------------------------------
    # BALANCE
    # ------------------------------------------------------

    def get_balance(self, address: str) -> Decimal:

        checksum = self.network.to_checksum(address)
        raw_balance = self.contract.functions.balanceOf(
            checksum
        ).call()

        return Decimal(raw_balance) / Decimal(10 ** self.decimals)

    # ------------------------------------------------------
    # SAFE GAS CALCULATION
    # ------------------------------------------------------

    def _apply_gas_strategy(self, tx: dict, level: str = "medium"):

        if level == "aggressive":
            tx["gasPrice"] = GasStrategy.aggressive(self.web3)
        elif level == "slow":
            tx["gasPrice"] = GasStrategy.slow(self.web3)
        else:
            tx["gasPrice"] = GasStrategy.medium(self.web3)

        tx["gas"] = self.web3.eth.estimate_gas(tx)
        return tx

    # ------------------------------------------------------
    # BUILD TRANSFER
    # ------------------------------------------------------

    def build_transfer_tx(
        self,
        from_address: str,
        to_address: str,
        amount: Decimal,
        gas_mode: str = "medium"
    ) -> dict:

        checksum_from = self.network.to_checksum(from_address)
        checksum_to = self.network.to_checksum(to_address)

        if not self.network.is_valid_address(checksum_to):
            raise ValueError("Invalid destination address")

        raw_amount = int(amount * (10 ** self.decimals))

        data = self.contract.encodeABI(
            fn_name="transfer",
            args=[checksum_to, raw_amount]
        )

        nonce = self.web3.eth.get_transaction_count(checksum_from)

        tx = {
            "chainId": self.network.config.chain_id,
            "nonce": nonce,
            "to": self.network.config.usdc_contract,
            "value": 0,
            "data": data,
        }

        tx = self._apply_gas_strategy(tx, gas_mode)

        return tx

    # ------------------------------------------------------
    # SIGN & SEND WITH RETRY
    # ------------------------------------------------------

    def _sign_and_send(self, tx: dict, private_key: str) -> str:

        for attempt in range(self.MAX_RETRIES):

            try:
                signed_tx = self.web3.eth.account.sign_transaction(
                    tx,
                    private_key
                )

                tx_hash = self.web3.eth.send_raw_transaction(
                    signed_tx.rawTransaction
                )

                return self.web3.to_hex(tx_hash)

            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise e
                time.sleep(2)

    # ------------------------------------------------------
    # PUBLIC TRANSFER METHOD
    # ------------------------------------------------------

    def transfer(
        self,
        private_key: str,
        from_address: str,
        to_address: str,
        amount: Decimal,
        gas_mode: str = "medium"
    ) -> Dict:

        if amount <= 0:
            raise ValueError("Amount must be positive")

        tx = self.build_transfer_tx(
            from_address,
            to_address,
            amount,
            gas_mode
        )

        tx_hash = self._sign_and_send(tx, private_key)

        return {
            "tx_hash": tx_hash,
            "explorer_url": self.network.get_explorer_url(tx_hash),
            "status": "SUBMITTED"
        }

    # ------------------------------------------------------
    # CONFIRMATION TRACKER
    # ------------------------------------------------------

    def wait_for_confirmation(
        self,
        tx_hash: str,
        min_confirmations: Optional[int] = None,
        timeout: int = 120
    ) -> Dict:

        confirmations_needed = min_confirmations or self.MIN_CONFIRMATIONS

        start_time = time.time()

        while True:

            if time.time() - start_time > timeout:
                return {
                    "status": "TIMEOUT",
                    "confirmations": 0
                }

            try:
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)

                if receipt is None:
                    time.sleep(3)
                    continue

                current_block = self.web3.eth.block_number
                confirmations = current_block - receipt.blockNumber

                if receipt.status == 0:
                    return {
                        "status": "FAILED",
                        "confirmations": confirmations
                    }

                if confirmations >= confirmations_needed:
                    return {
                        "status": "CONFIRMED",
                        "confirmations": confirmations
                    }

                time.sleep(5)

            except TransactionNotFound:
                time.sleep(3)

    # ------------------------------------------------------
    # VERIFY QUICK STATUS
    # ------------------------------------------------------

    def verify_transaction(self, tx_hash: str) -> Dict:

        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)

            if not receipt:
                return {"status": "PENDING"}

            confirmations = self.network.get_confirmations(tx_hash)

            return {
                "status": "SUCCESS" if receipt.status == 1 else "FAILED",
                "confirmations": confirmations
            }

        except Exception:
            return {"status": "UNKNOWN"}

    # ------------------------------------------------------
    # TREASURY TRANSFER (HOT WALLET CONTROLLED)
    # ------------------------------------------------------

    def treasury_transfer(
        self,
        to_address: str,
        amount: Decimal,
        gas_mode: str = "medium"
    ) -> Dict:

        private_key = os.getenv("TREASURY_PRIVATE_KEY")
        from_address = os.getenv("TREASURY_WALLET")

        if not private_key or not from_address:
            raise Exception("Treasury wallet not configured")

        return self.transfer(
            private_key,
            from_address,
            to_address,
            amount,
            gas_mode
        )