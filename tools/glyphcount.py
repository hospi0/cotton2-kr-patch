# -*- coding: utf-8 -*-
r"""분량 조사 — 모든 .MF 의 SPT 에서 16×16 4bpp(0x80 B) 글자 그림 수·고유 모양 수, 그리고 고유 모양 시트(work/view/glyphs_<n>.png).
  (코튼2 대사 = 글자 자리마다 16×16 그림 하나 — 글자 코드 없음, docs/01)
  python tools/glyphcount.py <disc 폴더> <출력 접두>
"""
import collections, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mf


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    src, outp = sys.argv[1], sys.argv[2]
    per = collections.Counter(); uniq = collections.OrderedDict()
    for f in sorted(os.listdir(src)):
        if not f.upper().endswith('.MF'):
            continue
        b = open(os.path.join(src, f), 'rb').read()
        for name, o, d, sz in mf.entries(b):
            if not name.endswith('.SPT'):
                continue
            items, _ = mf.spt_items(b[d:d + sz])
            for k, p, t, w, h, s in items:
                if w == 16 and h == 16 and s == 0x80 and t == 0:
                    g = b[d + p + 0x20:d + p + 0xa0]
                    if not any(g):
                        continue
                    per[f] += 1
                    uniq.setdefault(g, []).append((f, k))
    print('파일별 16×16 그림 수:', dict(per.most_common()))
    print('합계 %d · 고유 모양 %d' % (sum(per.values()), len(uniq)))
    gl = list(uniq)
    cols = 32
    for s in range(0, len(gl), 32 * 24):
        part = gl[s:s + 32 * 24]
        im = Image.new('L', (cols * 18, ((len(part) + cols - 1) // cols) * 18), 40)
        for i, g in enumerate(part):
            for y in range(16):
                for x in range(16):
                    v = g[y * 8 + x // 2]; v = (v >> 4) if x % 2 == 0 else v & 15
                    if v:
                        im.putpixel((i % cols * 18 + x + 1, i // cols * 18 + y + 1), min(255, v * 40))
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save('%s_%d.png' % (outp, s // (32 * 24)))


if __name__ == '__main__':
    main()
