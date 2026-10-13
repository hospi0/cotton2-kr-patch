# -*- coding: utf-8 -*-
r"""오프닝 그림(work/build_gfx/ttl_{0,1,2}.raw) → LZ00 압축해 CHR_TTL.MF SPT 0·1·2(오프닝)·6·10(캐릭터 소개) 자리에 «원래 크기 안에» 넣음.
  항목 머리·크기 칸 그대로, 압축 데이터 뒤는 0(풀기는 머리의 풀린 크기에서 멈춤) → MF 크기·오프셋 불변.
  python tools/build_ttl.py  → work/build/CHR_TTL.MF
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, lz00


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    b = bytearray(open(os.path.join(ROOT, 'work', 'disc', 'CHR_TTL.MF'), 'rb').read())
    E = {n.split('.')[-1]: (o, d, sz) for n, o, d, sz in mf.entries(b)}
    o, d, sz = E['SPT']; items, _ = mf.spt_items(bytes(b[d:d + sz]))
    for k in (0, 1, 2, 6, 10):
        _, p, t, w, h, z = items[k]
        raw = open(os.path.join(ROOT, 'work', 'build_gfx', 'ttl_%d.raw' % k), 'rb').read()
        c = lz00.compress(raw)
        assert lz00.decompress(c) == raw
        if len(c) > z:
            sys.exit('⛔ TTL %d 압축 %d > 자리 %d' % (k, len(c), z))
        at = d + p + 0x20
        b[at:at + z] = c + b'\0' * (z - len(c))
        assert lz00.decompress(bytes(b[at:at + z])) == raw
        print('TTL %d 압축 %d / 자리 %d' % (k, len(c), z))
    os.makedirs(os.path.join(ROOT, 'work', 'build'), exist_ok=True)
    open(os.path.join(ROOT, 'work', 'build', 'CHR_TTL.MF'), 'wb').write(b)


if __name__ == '__main__':
    main()
