def pkey_to_addr(priv_hex_or_bytes):
    P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    A = 0
    B = 7
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
    G = (Gx, Gy)

    def _to_bytes_from_hexlike(h):
        import binascii
        if isinstance(h, (bytes, bytearray)):
            b = bytes(h)
            if len(b) != 32:
                raise ValueError("private key bytes must be 32 bytes")
            return b
        if not isinstance(h, str):
            raise TypeError("private key must be hex string or 32-byte bytes")
        s = h.lower().strip()
        if s.startswith("0x"):
            s = s[2:]
        if len(s) < 64:
            s = s.rjust(64, "0")
        if len(s) != 64:
            raise ValueError("private key hex must represent 32 bytes (64 hex characters)")
        try:
            b = binascii.unhexlify(s)
        except Exception as e:
            raise ValueError("invalid hex for private key") from e
        return b

    def _egcd_inv(a, m):
        if a == 0:
            raise ZeroDivisionError("inverse of 0")
        a = a % m
        lm, hm = 1, 0
        low, high = a, m
        while low > 1:
            r = high // low
            nm = hm - lm * r
            new = high - low * r
            hm, lm = lm, nm
            high, low = low, new
        return lm % m

    def _ec_add(p1, p2):
        if p1 is None:
            return p2
        if p2 is None:
            return p1
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2:
            if (y1 + y2) % P == 0:
                return None
            lam_num = (3 * x1 * x1 + A) % P
            lam_den = (2 * y1) % P
            lam = (lam_num * _egcd_inv(lam_den, P)) % P
        else:
            lam_num = (y2 - y1) % P
            lam_den = (x2 - x1) % P
            lam = (lam_num * _egcd_inv(lam_den, P)) % P
        x3 = (lam * lam - x1 - x2) % P
        y3 = (lam * (x1 - x3) - y1) % P
        return (x3, y3)

    def _scalar_mult(k, point=G):
        if k % N == 0 or point is None:
            return None
        if k < 0:
            return _scalar_mult(-k, (point[0], (-point[1]) % P))
        result = None
        addend = point
        while k:
            if k & 1:
                result = _ec_add(result, addend)
            addend = _ec_add(addend, addend)
            k >>= 1
        return result

    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
        0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
        0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
        0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
        0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
        0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
        0x8000000000008080, 0x0000000080000001, 0x8000000080008008
    ]

    r = [
        [0, 36, 3, 41, 18],
        [1, 44, 10, 45, 2],
        [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56],
        [27, 20, 39, 8, 14]
    ]

    def _rotl(x, n):
        n %= 64
        return ((x << n) & ((1 << 64) - 1)) | (x >> (64 - n))

    def _keccak_f(st):
        for rnd in range(24):
            C = [st[x] ^ st[x + 5] ^ st[x + 10] ^ st[x + 15] ^ st[x + 20] for x in range(5)]
            D = [C[(x - 1) % 5] ^ _rotl(C[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    st[x + 5 * y] ^= D[x]
            B = [0] * 25
            for x in range(5):
                for y in range(5):
                    B[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl(st[x + 5 * y], r[x][y])
            for x in range(5):
                for y in range(5):
                    st[x + 5 * y] = B[x + 5 * y] ^ ((~B[((x + 1) % 5) + 5 * y]) & B[((x + 2) % 5) + 5 * y])
            st[0] ^= RC[rnd]

    def _keccak_256(d):
        rate = 136
        st = [0] * 25
        p = bytearray(d)
        p.append(0x01)
        while (len(p) % rate) != (rate - 1):
            p.append(0x00)
        p.append(0x80)
        for off in range(0, len(p), rate):
            b = p[off:off + rate]
            for i in range(rate // 8):
                st[i] ^= int.from_bytes(b[i * 8:(i + 1) * 8], "little")
            _keccak_f(st)
        out = bytearray()
        for i in range(4):
            out += st[i].to_bytes(8, "little")
        return bytes(out[:32])

    def _to_checksum_address(a):
        h = _keccak_256(a.encode("ascii")).hex()
        o = []
        for i, c in enumerate(a):
            if c in "0123456789":
                o.append(c)
            else:
                o.append(c.upper() if int(h[i], 16) >= 8 else c.lower())
        return "0x" + "".join(o)

    priv = _to_bytes_from_hexlike(priv_hex_or_bytes)
    d = int.from_bytes(priv, "big")
    if not (1 <= d < N):
        raise ValueError("private key integer is out of valid range")
    pub = _scalar_mult(d, G)
    if pub is None:
        raise ValueError("invalid key")
    x, y = pub
    xb = x.to_bytes(32, "big")
    yb = y.to_bytes(32, "big")
    pub64 = xb + yb
    h = _keccak_256(pub64)
    addr_bytes = h[-20:]
    addr_hex = addr_bytes.hex()
    checksum = _to_checksum_address(addr_hex)
    return checksum

'''
address = pkey_to_addr('0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
print(address)
'''