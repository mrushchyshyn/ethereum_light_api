import json
import urllib.request

def eth_rpc_request(url, method, params=None):
    if params is None:
        params = []
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
        return json.loads(data)

def eth_get_block_number(url):
    res = eth_rpc_request(url, "eth_blockNumber")
    return int(res["result"], 16)

def eth_get_balance(url, address, block="latest"):
    res = eth_rpc_request(url, "eth_getBalance", [address, block])
    return int(res["result"], 16)

def eth_get_transaction_count(url, address, block="latest"):
    res = eth_rpc_request(url, "eth_getTransactionCount", [address, block])
    return int(res["result"], 16)

def eth_get_transaction(url, tx_hash):
    return eth_rpc_request(url, "eth_getTransactionByHash", [tx_hash])

def eth_get_block(url, block_number=None):
    if block_number is None:
        block = "latest"
    elif isinstance(block_number, int):
        block = hex(block_number)
    else:
        block = block_number
    return eth_rpc_request(url, "eth_getBlockByNumber", [block, True])

def eth_send_raw_transaction(url, raw_tx_hex):
    if not isinstance(raw_tx_hex, str) or not raw_tx_hex.startswith("0x"):
        raise ValueError("raw_tx_hex must be a 0x-prefixed string")
    result = eth_rpc_request(url, "eth_sendRawTransaction", [raw_tx_hex])
    if "error" in result:
        raise Exception(f"RPC Error: {result['error']}")
    return result["result"]

'''
RPC_URL = ""

print("Block number:", eth_get_block_number(RPC_URL))

addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
bal = eth_get_balance(RPC_URL, addr)
print("Balance (ETH):", bal / 1e18)

tx_count = eth_get_transaction_count(RPC_URL, addr)
print("Transaction count:", tx_count)

block = eth_get_block(RPC_URL, "latest")
print("Latest block hash:", block["result"]["hash"])
'''