# -*- coding: utf-8 -*-
r"""코튼2(코튼 부메랑 같은 엔진) .MF 묶음과 SPT 스프라이트 표.
  MF 항목 = [u32 전체 크기][이름 16B][u32 0][u32 데이터 크기][u32 체크섬?][u32 0] + 데이터(+0x20)
  SPT = 항목 나열: 머리 0x20 [u16 종류?][u16 ?][u16 가로][u16 세로][u32 데이터 크기][0…] + 데이터(4bpp 16×16 글자 = 0x80)
  python tools/mf.py <파일.MF>   → 항목 목록, SPT 항목 요약
"""
import struct, sys


def entries(b):
    out = []; off = 0
    while off + 0x20 <= len(b):
        tot, = struct.unpack_from('>I', b, off)
        name = b[off + 4:off + 20].split(b'\0')[0].decode('latin1')
        sz, = struct.unpack_from('>I', b, off + 0x14)
        if not name or tot == 0:
            break
        out.append((name, off, off + 0x20, sz))
        off += tot
    return out


def spt_items(s):
    """[(번호, SPT 안 오프셋(머리), 종류, 가로, 세로, 크기)]"""
    out = []; p = 0; k = 0
    while p + 0x20 <= len(s):
        t, u, w, h, sz = struct.unpack_from('>HHHHI', s, p)
        if sz == 0 or p + 0x20 + sz > len(s):
            break
        out.append((k, p, t, w, h, sz)); p += 0x20 + sz; k += 1
    return out, p


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    b = open(sys.argv[1], 'rb').read()
    for name, off, d, sz in entries(b):
        print('%-16s @%06X 데이터 %06X 크기 %d' % (name, off, d, sz))
        if name.endswith('.SPT'):
            items, end = spt_items(b[d:d + sz])
            print('  SPT 항목 %d개 (끝 %X / %X)' % (len(items), end, sz))
            import collections
            c = collections.Counter((w, h) for _, _, _, w, h, _ in items)
            print('  크기 분포', c.most_common(8))
