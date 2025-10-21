def create_raw_tx(nonce, gas_price, gas_limit, to_addr, value, data, chain_id, priv_key):
    import os, hashlib

    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    A = 0
    B = 7
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
    G = (Gx, Gy)

    def modinv(a, n):
        lm, hm = 1, 0
        low, high = a % n, n
        while low > 1:
            r = high // low
            nm, new = hm - lm * r, high - low * r
            hm, lm, high, low = lm, nm, low, new
        return lm % n

    def ec_add(p1, p2):
        if p1 is None: return p2
        if p2 is None: return p1
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2:
            if (y1 + y2) % P == 0: return None
            m = (3 * x1 * x1) * modinv(2 * y1, P) % P
        else:
            m = (y2 - y1) * modinv((x2 - x1) % P, P) % P
        x3 = (m * m - x1 - x2) % P
        y3 = (m * (x1 - x3) - y1) % P
        return (x3, y3)

    def scalar_mult(k, p=G):
        res = None
        add = p
        while k:
            if k & 1: res = ec_add(res, add)
            add = ec_add(add, add)
            k >>= 1
        return res

    RC = [
        0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
        0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
        0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
        0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
        0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
        0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008
    ]
    r = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
    def rotl(x,n): n%=64; return ((x<<n)&((1<<64)-1))|(x>>(64-n))
    def keccak_f(st):
        for rnd in range(24):
            C=[st[x]^st[x+5]^st[x+10]^st[x+15]^st[x+20]for x in range(5)]
            D=[C[(x-1)%5]^rotl(C[(x+1)%5],1)for x in range(5)]
            for x in range(5):
                for y in range(5): st[x+5*y]^=D[x]
            B=[0]*25
            for x in range(5):
                for y in range(5): B[y+5*((2*x+3*y)%5)]=rotl(st[x+5*y],r[x][y])
            for x in range(5):
                for y in range(5): st[x+5*y]=B[x+5*y]^((~B[((x+1)%5)+5*y])&B[((x+2)%5)+5*y])
            st[0]^=RC[rnd]
    def keccak_256(data):
        rate=136;st=[0]*25;p=bytearray(data);p.append(0x01)
        while(len(p)%rate)!=(rate-1):p.append(0)
        p.append(0x80)
        for o in range(0,len(p),rate):
            b=p[o:o+rate]
            for i in range(rate//8): st[i]^=int.from_bytes(b[i*8:(i+1)*8],"little")
            keccak_f(st)
        out=bytearray()
        for i in range(4): out+=st[i].to_bytes(8,"little")
        return bytes(out[:32])

    def rlp_encode(x):
        if isinstance(x, bytes):
            if len(x)==1 and x[0]<0x80: return x
            l=len(x)
            if l<=55: return bytes([0x80+l])+x
            l_bytes=len(l.to_bytes((l.bit_length()+7)//8,'big'))
            return bytes([0xb7+l_bytes])+l.to_bytes(l_bytes,'big')+x
        elif isinstance(x, int):
            if x==0: return b'\x80'
            return rlp_encode(x.to_bytes((x.bit_length()+7)//8 or 1,'big'))
        elif isinstance(x, list):
            out=b''.join(rlp_encode(i) for i in x)
            l=len(out)
            if l<=55: return bytes([0xc0+l])+out
            l_bytes=len(l.to_bytes((l.bit_length()+7)//8,'big'))
            return bytes([0xf7+l_bytes])+l.to_bytes(l_bytes,'big')+out
        else:
            raise TypeError

    def sign(msg_hash, priv):
        d = int.from_bytes(priv, 'big')
        if not (1 <= d < N):
            raise ValueError("invalid privkey")
        z = int.from_bytes(msg_hash, 'big') % N
        while True:
            k = int.from_bytes(os.urandom(32), 'big') % N
            R = scalar_mult(k, G)
            if R is None: continue
            r_ = R[0] % N
            if r_ == 0: continue
            s_ = (modinv(k, N) * (z + r_ * d)) % N
            if s_ == 0: continue
            if s_ > N // 2: s_ = N - s_
            return (r_, s_)

    if isinstance(priv_key, str):
        if priv_key.startswith("0x"):
            priv_key = bytes.fromhex(priv_key[2:])
        else:
            priv_key = bytes.fromhex(priv_key)

    to_bytes = bytes.fromhex(to_addr[2:]) if to_addr else b""
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) and data.startswith("0x") else (data or b"")

    tx = [
        nonce,
        gas_price,
        gas_limit,
        to_bytes,
        value,
        data_bytes,
        chain_id, 0, 0
    ]

    rlp_unsigned = rlp_encode(tx)
    tx_hash = keccak_256(rlp_unsigned)
    r, s = sign(tx_hash, priv_key)
    v = chain_id * 2 + 35 + (0 if s <= N//2 else 1)
    raw_tx = rlp_encode([nonce, gas_price, gas_limit, to_bytes, value, data_bytes, v, r, s])
    return "0x" + raw_tx.hex()

'''
raw = create_raw_tx(
    nonce=0,
    gas_price=1000000000,
    gas_limit=21000,
    to_addr="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    value=10000000000000000,
    data=b"",
    chain_id=1,
    priv_key="0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)
print(raw)

raw = create_raw_tx(
    nonce=5,
    gas_price=2000000000,
    gas_limit=100000,
    to_addr="0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF",
    value=0,
    data="0xa9059cbb00000000000000000000000000112233445566778899aabbccddeeff0011223344556677",
    chain_id=1,
    priv_key="0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)
print(raw)
'''