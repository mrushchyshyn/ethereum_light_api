import json
import urllib.request
import struct

def eth_rpc_request(url, method, params=None):
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

def encode_function_call(signature, args):
    sig_bytes = keccak_256(signature.encode("ascii"))
    selector = sig_bytes[:4]
    encoded_args = b""
    for arg in args:
        if isinstance(arg, int):
            encoded_args += arg.to_bytes(32, "big")
        elif isinstance(arg, str):
            if arg.startswith("0x") and len(arg) == 42:
                encoded_args += int(arg[2:], 16).to_bytes(32, "big")
            elif arg.startswith("0x"):
                data_bytes = bytes.fromhex(arg[2:])
                encoded_args += data_bytes.rjust(32, b"\x00")
            else:
                raise ValueError("string args must be hex or addresses")
        elif isinstance(arg, bytes):
            encoded_args += arg.rjust(32, b"\x00")
        else:
            raise TypeError("unsupported arg type")
    return "0x" + (selector + encoded_args).hex()

def eth_call_contract(url, to_addr, signature, args=None, from_addr=None, block="latest"):
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
    if args is None:
        args = []
    return encode_function_call(signature, args)

'''
RPC = ""
token = "0x6B175474E89094C44Da98b954EedeAC495271d0F"  # DAI
addr = "0x77134cbC06cB00b66F4c7e623D5fdBF6777635EC"

result = eth_call_contract(
    RPC,
    to_addr=token,
    signature="balanceOf(address)",
    args=[addr]
)
print("Raw result:", result)
print("Balance:", int(result, 16) / 1e18)

data = build_contract_tx_data(
    "transfer(address,uint256)",
    ["0x00112233445566778899aabbccddeeff00112233", 1234567890000000000]
)
print("Call data for tx:", data)
'''