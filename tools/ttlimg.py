# -*- coding: utf-8 -*-
r"""CHR_TTL.MF 그림 k 번 풀기: (raw 8bpp 352×224, 팔레트 RGB 256) — 팔레트 번호 = SCH 항목 바이트 4 u16 / 0x10."""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, lz00


def load(k, path=None):
    b = open(path or os.path.join(ROOT, 'work', 'disc', 'CHR_TTL.MF'), 'rb').read()
    E = {n.split('.')[-1]: (o, d, sz) for n, o, d, sz in mf.entries(b)}
    o, d, sz = E['SCH']; s = b[d:d + sz]
    en = s[struct.unpack_from('>I', s, 4 * k)[0]:][:20]
    pn = struct.unpack_from('>H', en, 4)[0] // 0x10
    o, d, sz = E['SPL']; spl = b[d + pn * 512:d + pn * 512 + 512]
    pal = [struct.unpack_from('>H', spl, 2 * i)[0] for i in range(256)]
    pal = [((v & 31) * 8, ((v >> 5) & 31) * 8, ((v >> 10) & 31) * 8) for v in pal]
    o, d, sz = E['SPT']; sp = b[d:d + sz]; items, _ = mf.spt_items(sp)
    _, p, t, w, h, z = items[k]
    return bytearray(lz00.decompress(sp[p + 0x20:p + 0x20 + z])), pal, (w, h)
