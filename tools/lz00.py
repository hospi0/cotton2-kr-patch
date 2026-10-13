# -*- coding: utf-8 -*-
r"""코튼2 «LZ00» 압축(SPT 종류 1 그림) 풀기·싸기.
  머리 «LZ00» + u32 BE 풀린 크기, 그 뒤 토큰:
    c < 0x10        : 다음 c+1 바이트를 그대로
    c ≥ 0x10, n     : (c − 0x0F) 바이트 앞에서 n+3 바이트 복사(거리 1‥240, 길이 3‥258; 거리 1 = 반복)
  ✅ CHR_TTL.MF SPT 0번 → 스테이트 VDP1 프롤로그 그림(352×224 8bpp)과 78,848 B 전부 일치(2026-10-12).
"""
import struct


def decompress(b):
    assert b[:4] == b'LZ00', b[:4]
    size, = struct.unpack_from('>I', b, 4)
    c = b[8:]; o = bytearray(); i = 0
    while len(o) < size:
        t = c[i]
        if t < 0x10:
            n = t + 1; o += c[i + 1:i + 1 + n]; i += 1 + n
        else:
            n = c[i + 1] + 3; d = t - 0x0F
            for _ in range(n):
                o.append(o[-d])
            i += 2
    return bytes(o[:size])


def compress(data):
    """탐욕 압축(같은 형식) — 해시 체인으로 거리 1‥240 안에서 가장 긴 일치"""
    out = bytearray(b'LZ00' + struct.pack('>I', len(data)))
    lit = bytearray(); i = 0; n = len(data)

    def flush():
        nonlocal lit
        while lit:
            ch = lit[:16]; out.append(len(ch) - 1); out.extend(ch); lit = lit[16:]
    while i < n:
        best = 0; bd = 0
        for d in range(1, min(240, i) + 1):
            L = 0
            while L < 258 and i + L < n and data[i + L] == data[i + L - d]:
                L += 1
            if L > best:
                best, bd = L, d
                if L == 258:
                    break
        if best >= 3:
            flush(); out.append(bd + 0x0F); out.append(best - 3); i += best
        else:
            lit.append(data[i]); i += 1
    flush()
    return bytes(out)
