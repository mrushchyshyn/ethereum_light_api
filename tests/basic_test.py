# tests/test_integration.py
import time
from ethereum_light_api import (
    pkey_to_addr,
    create_raw_tx,
    build_contract_tx_data,
    eth_get_block_number,
    eth_get_balance,
    eth_get_transaction_count,
    eth_send_raw_transaction,
)

# RPC endpoint (replace with your testnet endpoint, e.g., Sepolia)
RPC_URL = ""

# Private key of sender (⚠️ use a test wallet)
PRIVATE_KEY = ""

# Known Ethereum address (Vitalik)
VITALIK_ADDR = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

# Example ERC-20 contract (user-specified)
TOKEN_CONTRACT = "0xD821DE8a07061241337CD29E92Ab2ca88217d920"


def print_eth(x):
    return f"{x / 1e18:.6f} ETH"


def main():
    print("=== Ethereum Integration Test ===")

    # 1. Derive sender address
    my_addr = pkey_to_addr(PRIVATE_KEY)
    print("My address:", my_addr)

    # 2. Query blockchain info
    block = eth_get_block_number(RPC_URL)
    print("Current block:", block)

    balance = eth_get_balance(RPC_URL, my_addr)
    print("My balance:", print_eth(balance))

    nonce = eth_get_transaction_count(RPC_URL, my_addr)
    print("Nonce:", nonce)

    # 3. Simple ETH transfer
    print("\n--- Testing plain ETH transfer ---")
    value_wei = int(0.0001 * 1e18)
    gas_price = 3_000_000_000  # 3 gwei
    gas_limit = 100000
    chain_id = 11155111  # Sepolia testnet

    raw_tx_eth = create_raw_tx(
        nonce=nonce,
        gas_price=gas_price,
        gas_limit=gas_limit,
        to_addr=VITALIK_ADDR,
        value=value_wei,
        data=b"",
        chain_id=chain_id,
        priv_key=PRIVATE_KEY,
    )
    print("Raw ETH TX:", raw_tx_eth)
    print("TX size:", len(raw_tx_eth) // 2, "bytes")

    # 4. ERC20 token transfer
    print("\n--- Testing ERC20 token transfer ---")
    token_amount = int(10 * 1e18)

    data = build_contract_tx_data(
        "transfer(address,uint256)", [VITALIK_ADDR, token_amount]
    )

    gas_limit_token = 1_000_000
    raw_tx_token = create_raw_tx(
        nonce=nonce + 1,
        gas_price=gas_price,
        gas_limit=gas_limit_token,
        to_addr=TOKEN_CONTRACT,
        value=0,
        data=data,
        chain_id=chain_id,
        priv_key=PRIVATE_KEY,
    )

    print("Raw ERC20 TX:", raw_tx_token)
    print("TX size:", len(raw_tx_token) // 2, "bytes")

    # 5. Broadcast
    time.sleep(10)
    print("\nBroadcasting ETH transfer...")
    tx_hash_eth = eth_send_raw_transaction(RPC_URL, raw_tx_eth)
    print("ETH TX hash:", tx_hash_eth)

    time.sleep(30)
    print("Broadcasting token transfer...")
    tx_hash_token = eth_send_raw_transaction(RPC_URL, raw_tx_token)
    print("Token TX hash:", tx_hash_token)

    print("\n=== Done ===")


if __name__ == "__main__":
    main()