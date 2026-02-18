from dataclasses import dataclass
from typing import Dict, List, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
import os
import time


# ==========================================================
# NETWORK CONFIG
# ==========================================================

@dataclass
class NetworkConfig:
    name: str
    chain_id: int
    rpc_urls: List[str]
    explorer_url: str
    usdc_contract: str
    symbol: str
    decimals: int
    is_poa: bool = False


# ==========================================================
# SUPPORTED NETWORKS
# ==========================================================

SUPPORTED_NETWORKS: Dict[str, NetworkConfig] = {

    "POLYGON": NetworkConfig(
        name="Polygon Mainnet",
        chain_id=137,
        rpc_urls=[
            os.getenv("POLYGON_RPC_1"),
            os.getenv("POLYGON_RPC_2"),
        ],
        explorer_url="https://polygonscan.com/tx/",
        usdc_contract="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        symbol="MATIC",
        decimals=18,
        is_poa=True,
    ),

    "ETHEREUM": NetworkConfig(
        name="Ethereum Mainnet",
        chain_id=1,
        rpc_urls=[
            os.getenv("ETH_RPC_1"),
            os.getenv("ETH_RPC_2"),
        ],
        explorer_url="https://etherscan.io/tx/",
        usdc_contract="0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        symbol="ETH",
        decimals=18,
    ),

    "BSC": NetworkConfig(
        name="Binance Smart Chain",
        chain_id=56,
        rpc_urls=[
            os.getenv("BSC_RPC_1"),
            os.getenv("BSC_RPC_2"),
        ],
        explorer_url="https://bscscan.com/tx/",
        usdc_contract="0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
        symbol="BNB",
        decimals=18,
        is_poa=True,
    ),
}


# ==========================================================
# NETWORK MANAGER PRO
# ==========================================================

class NetworkManager:

    MAX_RPC_RETRIES = 3

    def __init__(self, network_name: str):

        network_name = network_name.upper()

        if network_name not in SUPPORTED_NETWORKS:
            raise ValueError("Unsupported network")

        self.config = SUPPORTED_NETWORKS[network_name]
        self.web3 = self._connect_with_failover()

    # ------------------------------------------------------
    # RPC FAILOVER SYSTEM
    # ------------------------------------------------------

    def _connect_with_failover(self) -> Web3:

        for rpc_url in self.config.rpc_urls:

            if not rpc_url:
                continue

            try:
                web3 = Web3(Web3.HTTPProvider(rpc_url))

                if self.config.is_poa:
                    web3.middleware_onion.inject(
                        geth_poa_middleware, layer=0
                    )

                if web3.is_connected():
                    return web3

            except Exception:
                continue

        raise ConnectionError(f"All RPCs failed for {self.config.name}")

    # ------------------------------------------------------
    # ADDRESS UTILITIES
    # ------------------------------------------------------

    def is_valid_address(self, address: str) -> bool:
        return self.web3.is_address(address)

    def to_checksum(self, address: str) -> str:
        return self.web3.to_checksum_address(address)

    # ------------------------------------------------------
    # GAS STRATEGY (EIP-1559 + LEGACY)
    # ------------------------------------------------------

    def get_gas_fees(self) -> Dict:

        latest_block = self.web3.eth.get_block("latest")

        if "baseFeePerGas" in latest_block:

            base_fee = latest_block["baseFeePerGas"]
            priority_fee = self.web3.eth.max_priority_fee

            return {
                "maxFeePerGas": int(base_fee * 1.2 + priority_fee),
                "maxPriorityFeePerGas": priority_fee,
                "type": "EIP1559"
            }

        else:
            return {
                "gasPrice": self.web3.eth.gas_price,
                "type": "LEGACY"
            }

    # ------------------------------------------------------
    # BUILD TRANSACTION
    # ------------------------------------------------------

    def build_transaction(
        self,
        from_address: str,
        to_address: str,
        data: bytes,
        value: int = 0
    ) -> dict:

        checksum_from = self.to_checksum(from_address)

        nonce = self.web3.eth.get_transaction_count(checksum_from)

        tx = {
            "chainId": self.config.chain_id,
            "nonce": nonce,
            "to": self.to_checksum(to_address),
            "value": value,
            "data": data,
        }

        gas_data = self.get_gas_fees()
        tx.update(gas_data)

        tx["gas"] = self.web3.eth.estimate_gas(tx)

        return tx

    # ------------------------------------------------------
    # SIGN & SEND
    # ------------------------------------------------------

    def sign_transaction(self, tx: dict, private_key: str):
        return self.web3.eth.account.sign_transaction(tx, private_key)

    def send_raw_transaction(self, signed_tx):
        tx_hash = self.web3.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        return self.web3.to_hex(tx_hash)

    # ------------------------------------------------------
    # CONFIRMATIONS
    # ------------------------------------------------------

    def get_transaction_receipt(self, tx_hash: str):
        try:
            return self.web3.eth.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return None

    def get_confirmations(self, tx_hash: str) -> Optional[int]:

        receipt = self.get_transaction_receipt(tx_hash)

        if not receipt:
            return None

        current_block = self.web3.eth.block_number
        return current_block - receipt.blockNumber

    # ------------------------------------------------------
    # EXPLORER LINK
    # ------------------------------------------------------

    def get_explorer_url(self, tx_hash: str) -> str:
        return f"{self.config.explorer_url}{tx_hash}"

    # ------------------------------------------------------
    # HEALTH CHECK
    # ------------------------------------------------------

    def health_check(self) -> bool:
        try:
            self.web3.eth.block_number
            return True
        except Exception:
            return False

    # ------------------------------------------------------
    # AUTO RECONNECT
    # ------------------------------------------------------

    def reconnect(self):
        self.web3 = self._connect_with_failover()