"""
ethereum_light_api
------------------
Lightweight, dependency-free Ethereum API in pure Python.

Implements:
- secp256k1 ECDSA signing
- RLP transaction encoding
- Keccak-256 hashing
- Basic ABI encoding for contract calls
- JSON-RPC HTTP utilities for blockchain interaction

Project URL: https://github.com/mrushchyshyn/ethereum_light_api
Contact: markorushchyshyn@gmail.com
"""

__title__ = "ethereum_light_api"
__description__ = "Lightweight, dependency-free Ethereum API in pure Python."
__url__ = "https://github.com/mrushchyshyn/ethereum_light_api"
__version__ = "0.1.0"
__author__ = "mrushchyshyn"
__author_email__ = "markorushchyshyn@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 mrushchyshyn"

from .private_key import pkey_to_addr
from .raw_transaction import create_raw_tx
from .contracts import build_contract_tx_data, eth_call_contract
from .http_api import (
    eth_rpc_request,
    eth_get_block_number,
    eth_get_balance,
    eth_get_transaction_count,
    eth_send_raw_transaction
)

__all__ = [
    "pkey_to_addr",
    "create_raw_tx",
    "build_contract_tx_data",
    "eth_call_contract",
    "eth_rpc_request",
    "eth_get_block_number",
    "eth_get_balance",
    "eth_get_transaction_count",
    "eth_send_raw_transaction",
]