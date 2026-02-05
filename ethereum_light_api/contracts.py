import json
import urllib.request
import struct

def eth_rpc_request(url, method, params=None):
    """Handles the low-level JSON-RPC networking."""
    if params is None:
        params = []
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def keccak_256(data):
    """Pure Python implementation of Keccak-256 hash."""
    RC = [
        0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
        0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
        0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
        0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
        0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
        0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008
    ]
    r = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
    def rotl(x,n):n%=64;return((x<<n)&((1<<64)-1))|(x>>(64-n))
    def keccak_f(st):
        for rnd in range(24):
            C=[st[x]^st[x+5]^st[x+10]^st[x+15]^st[x+20]for x in range(5)]
            D=[C[(x-1)%5]^rotl(C[(x+1)%5],1)for x in range(5)]
            for x in range(5):
                for y in range(5):st[x+5*y]^=D[x]
            B=[0]*25
            for x in range(5):
                for y in range(5):B[y+5*((2*x+3*y)%5)]=rotl(st[x+5*y],r[x][y])
            for x in range(5):
                for y in range(5):st[x+5*y]=B[x+5*y]^((~B[((x+1)%5)+5*y])&B[((x+2)%5)+5*y])
            st[0]^=RC[rnd]
    rate=136;st=[0]*25;p=bytearray(data);p.append(0x01)
    while(len(p)%rate)!=(rate-1):p.append(0)
    p.append(0x80)
    for o in range(0,len(p),rate):
        b=p[o:o+rate]
        for i in range(rate//8):st[i]^=int.from_bytes(b[i*8:(i+1)*8],"little")
        keccak_f(st)
    out=bytearray()
    for i in range(4):out+=st[i].to_bytes(8,"little")
    return bytes(out[:32])

def encode_abi(args):
    """
    Encodes Python values into Solidity ABI format.
    Supports: int, bool, address, bytes, string, and list (dynamic arrays).
    """
    head_parts = []
    tail_parts = []
    
    current_tail_offset = len(args) * 32

    for arg in args:
        is_dynamic = False
        encoded = b""

        if isinstance(arg, bool):
            encoded = (1 if arg else 0).to_bytes(32, "big")

        elif isinstance(arg, int):
            encoded = arg.to_bytes(32, "big")

        elif isinstance(arg, str) and arg.startswith("0x"):
            if len(arg) == 42:
                encoded = int(arg, 16).to_bytes(32, "big")
            else:
                b_val = bytes.fromhex(arg[2:])
                encoded = b_val.ljust(32, b"\x00")

        elif isinstance(arg, str):
            is_dynamic = True
            arg_bytes = arg.encode("utf-8")
            length = len(arg_bytes).to_bytes(32, "big")
            padding_len = (32 - (len(arg_bytes) % 32)) % 32
            encoded = length + arg_bytes + (b"\x00" * padding_len)

        elif isinstance(arg, (bytes, bytearray)):
            is_dynamic = True
            length = len(arg).to_bytes(32, "big")
            padding_len = (32 - (len(arg) % 32)) % 32
            encoded = length + arg + (b"\x00" * padding_len)

        elif isinstance(arg, list):
            is_dynamic = True
            length = len(arg).to_bytes(32, "big")
            content = b""
            for item in arg:
                if isinstance(item, int):
                    content += item.to_bytes(32, "big")
                elif isinstance(item, str) and item.startswith("0x"):
                    content += int(item, 16).to_bytes(32, "big")
                else:
                    raise TypeError("Nested dynamic types in arrays not supported in this lightweight version")
            encoded = length + content

        else:
            raise TypeError(f"Unsupported type: {type(arg)}")

        if is_dynamic:
            head_parts.append(current_tail_offset.to_bytes(32, "big"))
            tail_parts.append(encoded)
            current_tail_offset += len(encoded)
        else:
            head_parts.append(encoded)

    return b"".join(head_parts + tail_parts)

def encode_function_call(signature, args):
    """Generates the 4-byte selector and ABI encoded args."""
    sig_bytes = keccak_256(signature.encode("ascii"))
    selector = sig_bytes[:4]
    
    if args:
        encoded_args = encode_abi(args)
    else:
        encoded_args = b""
        
    return "0x" + (selector + encoded_args).hex()

def eth_call_contract(url, to_addr, signature, args=None, from_addr=None, block="latest"):
    """Reads data from a smart contract."""
    if args is None:
        args = []
    call_data = encode_function_call(signature, args)
    call_obj = {
        "to": to_addr,
        "data": call_data
    }
    if from_addr:
        call_obj["from"] = from_addr
    res = eth_rpc_request(url, "eth_call", [call_obj, block])
    return res["result"]

def build_contract_tx_data(signature, args=None):
    """Builds the data payload for a write transaction."""
    if args is None:
        args = []
    return encode_function_call(signature, args)

# ==========================================
# 1. MANUAL TEST
# ==========================================
'''
print("\n--- Running Manual Tests ---\n")

# Test 1: Mixed Static Types (uint, bool, address)
# signature: setConfig(uint256,bool,address)
sig1 = "setConfig(uint256,bool,address)"
args1 = [50, True, "0x" + "1" * 40]
res1 = build_contract_tx_data(sig1, args1)
print(f"Test 1 (Mixed Static): {sig1}")
print(f"Result: {res1}\n")

# Test 2: Dynamic String in the middle
# signature: createUser(uint256,string,bool)
sig2 = "createUser(uint256,string,bool)"
args2 = [1, "Alice", True]
res2 = build_contract_tx_data(sig2, args2)
print(f"Test 2 (String Middle): {sig2}")
print(f"Result: {res2}\n")

# Test 3: Raw Bytes (Dynamic)
# signature: submitProof(bytes)
sig3 = "submitProof(bytes)"
args3 = [bytes.fromhex("deadbeef")]
res3 = build_contract_tx_data(sig3, args3)
print(f"Test 3 (Bytes): {sig3}")
print(f"Result: {res3}\n")

# Test 4: Array of Addresses
# signature: whitelist(address[])
addr_a = "0x" + "a" * 40
addr_b = "0x" + "b" * 40
sig4 = "whitelist(address[])"
args4 = [addr_a, addr_b]
res4 = build_contract_tx_data(sig4, args4)
print(f"Test 4 (Address Array): {sig4}")
print(f"Result: {res4}\n")

# Test 5: Complex Multi-Dynamic
# signature: multi(string,uint256[],string)
sig5 = "multi(string,uint256[],string)"
args5 = ["First", [10, 20], "Second"]
res5 = build_contract_tx_data(sig5, args5)
print(f"Test 5 (Multiple Dynamic): {sig5}")
print(f"Result: {res5}\n")

# Verification helper for offsets
def verify_offset(hex_str, arg_index, expected_offset):
    # Head starts at index 10 (0x + 8 chars selector). Each arg is 64 hex chars.
    start = 10 + (arg_index * 64)
    chunk = hex_str[start : start + 64]
    val = int(chunk, 16)
    status = "PASS" if val == expected_offset else f"FAIL (Got {val}, Expected {expected_offset})"
    print(f"  -> Arg {arg_index} Offset Check: {status}")

print("--- Automated Checks for Test 5 ---")
verify_offset(res5, 0, 96)   # String "First" pointer
verify_offset(res5, 1, 160)  # Array pointer
verify_offset(res5, 2, 256)  # String "Second" pointer

# ==========================================
# 2. WEB3.PY COMPARISON TEST
# ==========================================

try:
    from web3 import Web3
    from eth_abi import encode as abi_encode

    print("\n--- Web3.py Comparison Tests (Extended) ---")

    w3 = Web3()

    # List of (function_signature, args)
    test_vectors = [
        # Static-only
        ("setConfig(uint256,bool,address)", [50, True, "0x" + "1" * 40]),
        ("flip(bool)", [False]),
        ("setOwner(address)", ["0x" + "2" * 40]),
        ("setPair(address,address)", ["0x" + "3" * 40, "0x" + "4" * 40]),
        ("setUint(uint256)", [2**255]),

        # Dynamic values
        ("createUser(uint256,string,bool)", [1, "Alice", True]),
        ("note(string)", ["hello"]),
        ("submitProof(bytes)", [bytes.fromhex("deadbeef")]),
        ("blob(bytes)", [b"\x00" * 33]),

        # Dynamic arrays (NOTE: array arg must be a SINGLE list inside args)
        ("whitelist(address[])", [["0x" + "a" * 40, "0x" + "b" * 40]]),
        ("setIds(uint256[])", [[1, 2, 3, 99999]]),
        ("setFlags(bool[])", [[True, False, True, True]]),

        # Multi-dynamic / offset stress
        ("multi(string,uint256[],string)", ["First", [10, 20], "Second"]),
        ("register(string,uint256[],address)", [
            "Mastering Ethereum",
            [101, 202, 303, 99999],
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        ]),
        ("doubleBytes(bytes,bytes)", [b"\x01\x02", b"\x03" * 64]),
        ("mixed(address[],string,bytes)", [["0x" + "c" * 40], "hi", b"\xff" * 5]),
    ]

    passed = 0
    failed = 0

    for func_sig, args in test_vectors:
        # A) Your custom code
        custom_hex = build_contract_tx_data(func_sig, args)

        # B) Web3 selector + eth_abi arguments
        selector_bytes = w3.keccak(text=func_sig)[:4]

        types_str = func_sig[func_sig.find("(") + 1 : func_sig.rfind(")")]
        arg_types = [] if not types_str.strip() else [t.strip() for t in types_str.split(",")]

        encoded_args_bytes = abi_encode(arg_types, args)
        web3_hex = "0x" + selector_bytes.hex() + encoded_args_bytes.hex()

        # C) Compare
        ok = custom_hex.lower() == web3_hex.lower()
        print("\n" + "-" * 70)
        print(f"Scenario: {func_sig}")
        print(f"Args: {args}")
        print(f"Custom: {custom_hex[:60]}... (len: {len(custom_hex)})")
        print(f"Web3:   {web3_hex[:60]}... (len: {len(web3_hex)})")

        if ok:
            print("✅ MATCH")
            passed += 1
        else:
            print("❌ MISMATCH")
            failed += 1

            # Find first mismatch index (character index in the hex string)
            m = None
            n = min(len(custom_hex), len(web3_hex))
            for i in range(n):
                if custom_hex[i].lower() != web3_hex[i].lower():
                    m = i
                    break
            if m is None and len(custom_hex) != len(web3_hex):
                m = n

            if m is not None:
                print(f"First mismatch at index {m}")
                # show a small window around the mismatch
                lo = max(0, m - 32)
                hi = min(max(len(custom_hex), len(web3_hex)), m + 32)
                print(f"Custom[{lo}:{hi}]: {custom_hex[lo:hi]}")
                print(f"Web3  [{lo}:{hi}]: {web3_hex[lo:hi]}")

    print("\n" + "=" * 70)
    print(f"Summary: {passed} passed, {failed} failed, total {passed + failed}")

except ImportError as e:
    print("\n[!] Missing dependency:", e)
    print("    Install with: pip install web3 eth-abi")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\n[!] An error occurred during Web3 comparison: {e}")
'''
