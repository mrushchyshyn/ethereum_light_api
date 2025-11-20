# ethereum_light_api

**Lightweight, dependency-free Ethereum API in pure Python.**  
Ethereum-like chains utilities for wallets, transactions, and contract calls, built with only stdlib Python.

---

## 🚀 Installation

```bash
pip install ethereum_light_api
```

---

## ⚙️ Quickstart Tutorial

Below is a complete set of examples showing how to:

- Query blockchain data  
- Derive an address from a private key  
- Check nonce and ether balance  
- Build and send transactions  
- Interact with smart contracts  

All examples use the **Ethereum Sepolia testnet** RPC endpoint.

---

### Get the current block number

```python
from ethereum_light_api import eth_get_block_number

# Public RPC endpoint (Sepolia testnet)
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"

# Fetch latest block
block_number = eth_get_block_number(RPC_URL)
print("Current block:", block_number)
```

---

### Convert private key → address

```python
from ethereum_light_api import pkey_to_addr

# Example private key (use test key only!)
PRIVATE_KEY = "0x..."

# Derive Ethereum address
address = pkey_to_addr(PRIVATE_KEY)
print("Address:", address)
```

---

### Get nonce

```python
from ethereum_light_api import eth_get_transaction_count

RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
address = "0x..."

# Get nonce considering pending transactions (recommended before sending)
nonce_pending = eth_get_transaction_count(RPC_URL, address, block="pending")
print("Next nonce (pending):", nonce_pending)

# You can also get the confirmed nonce (latest)
nonce_latest = eth_get_transaction_count(RPC_URL, address, block="latest")
print("Nonce (latest):", nonce_latest)
```
---

### Get ETH balance

```python
from ethereum_light_api import eth_get_balance

# RPC endpoint and address from previous example
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
address = "0x..."  # example address

# Get balance in wei
balance = eth_get_balance(RPC_URL, address)
print("Balance (wei):", balance)
print("Balance (ETH):", balance / 1e18)
```

---

### Create and send a simple ETH transfer

```python
from ethereum_light_api import create_raw_tx, eth_send_raw_transaction

RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
PRIVATE_KEY = "0x..."
chain_id = 11155111  # Sepolia testnet
to_addr = "0x..."  # receiver address

# Build raw transaction
raw_tx = create_raw_tx(
    nonce=0,  # replace with actual nonce
    gas_price=1_000_000_000,  # 1 gwei
    gas_limit=500_000,
    to_addr=to_addr,
    value=10_000_000_000_000_000,  # 0.01 ETH
    data=b"",
    chain_id=chain_id,
    priv_key=PRIVATE_KEY,
)

print("Raw transaction:", raw_tx)

# Send to network
result = eth_send_raw_transaction(RPC_URL, raw_tx)
print("Transaction hash:", result)
```

---

### Read data from a smart contract (ERC-20 `balanceOf`)

```python
from ethereum_light_api import eth_call_contract

RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"

# DAI token (example) and user address
token_addr = "0x..."
holder_addr = "0x..."

# Call contract function balanceOf(address)
raw_result = eth_call_contract(
    RPC_URL,
    to_addr=token_addr,
    signature="balanceOf(address)",
    args=[holder_addr]
)

print("Raw result:", raw_result)
print("Token balance:", int(raw_result, 16) / 1e18)
```

---

### Interactions with the smart contract (Build and send ERC-20 token transaction)

```python
from ethereum_light_api import build_contract_tx_data, create_raw_tx, eth_send_raw_transaction

RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
PRIVATE_KEY = "0x..."
chain_id = 11155111  # Sepolia testnet

# Example ERC-20 contract and receiver
token_contract = "0x..."
receiver_addr = "0x..."
amount = 1_234_567_890_000_000_000  # 1.23456789 tokens (18 decimals)

# Build transaction data for transfer(address,uint256)
data = build_contract_tx_data(
    "transfer(address,uint256)",
    [receiver_addr, amount]
)

# Construct and sign raw transaction
raw_tx = create_raw_tx(
    nonce=5,  # replace with your actual nonce
    gas_price=2_000_000_000,
    gas_limit=500_000,
    to_addr=token_contract,
    value=0,
    data=data,
    chain_id=chain_id,
    priv_key=PRIVATE_KEY,
)

print("Raw ERC-20 TX:", raw_tx)

# Send it
result = eth_send_raw_transaction(RPC_URL, raw_tx)
print("Broadcast result:", result)
```

---

## 🧠 Notes

- Created entirely with the **Python standard library** — no external dependencies.  
- Ideal for low-resource environments, education, or building minimal web3 tools.

---

## 🔗 Links

- 📦 **PyPI:** [pypi.org/project/ethereum_light_api](https://pypi.org/project/ethereum_light_api/)
- ✉️ **Contact:** [markorushchyshyn@gmail.com](mailto:markorushchyshyn@gmail.com)
