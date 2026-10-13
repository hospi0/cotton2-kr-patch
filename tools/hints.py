# -*- coding: utf-8 -*-
r"""이어하기 화면 힌트 그림(CHR_ST1‥7.MF SPT, w×32 4bpp LZ00, 대사와 같은 16×16 글자 13px 간격·줄 16px) 한글로. 띄어쓰기는 6px.
  번역 work/text/hints_ko.tsv → 글자 그림 kfont.glyph_bytes(대사와 같은 그림) → 같은 w×32 → LZ00 → 원래 자리(z) 안에 + 0 채움.
  한 줄만이면 세로 가운데(y 8). 폭 넘침·자리 넘침은 멈춤.
  python tools/hints.py → work/build/CHR_ST*.MF + work/view/hints_ko.png
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, lz00, kfont, rules, build_vs
from PIL import Image, ImageDraw

ERR = []
SPACE = 6   # 띄어쓰기 폭(글자 13px)
PAL = [(0, 0, 40), (60, 60, 120), (40, 80, 200), (150, 200, 255), (230, 250, 255)] + [(255, 0, 255)] * 11


def rows():
    for l in open(os.path.join(ROOT, 'work', 'text', 'hints_ko.tsv'), encoding='utf-8').read().splitlines():
        if l.startswith('#') or not l.strip():
            continue
        st, k, ja, ko = l.split('\t')
        yield st, int(k), ja, rules.squeeze(ko)


def render(ko, w, jp):
    lines = ko.split('/')
    px = [[0] * w for _ in range(32)]
    y0 = 8 if len(lines) == 1 else 0
    for li, line in enumerate(lines):
        xs = []; cx = 0
        for c in line:
            xs.append(cx); cx += SPACE if c in ' 　' else 13
        width = xs[-1] + (16 if line[-1] not in ' 　' else 0)
        if width > w:
            ERR.append('⛔ 폭 넘침 %dpx(최대 %d): %s' % (width, w, line)); continue
        for ci, c in enumerate(line):
            if c in ' 　':
                continue
            g = kfont.unpack(kfont.glyph_bytes(c, jp))
            for y in range(16):
                for x in range(16):
                    v = g[y][x]
                    X = xs[ci] + x
                    if v and X < w and v >= px[y0 + li * 16 + y][X]:
                        px[y0 + li * 16 + y][X] = v
    return px


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    _, jp = build_vs.jp_glyphs()
    by = {}
    for st, k, ja, ko in rows():
        by.setdefault(st, []).append((k, ja, ko))
    previews = []
    for st, lst in sorted(by.items()):
        b = bytearray(open(os.path.join(ROOT, 'work', 'disc', 'CHR_%s.MF' % st), 'rb').read())
        E = {n.split('.')[-1]: (o, d, sz) for n, o, d, sz in mf.entries(b)}
        o, d, sz = E['SPT']; items, _ = mf.spt_items(bytes(b[d:d + sz]))
        for k, ja, ko in lst:
            _, p, t, w, h, z = items[k]
            assert h == 32 and b[d + p + 0x20:d + p + 0x24] == b'LZ00', (st, k)
            px = render(ko, w, jp)
            if ERR:
                continue
            raw = bytes((px[y][x] << 4) | px[y][x + 1] for y in range(32) for x in range(0, w, 2))
            c = lz00.compress(raw); assert lz00.decompress(c) == raw
            if len(c) > z:
                sys.exit('⛔ %s %d 압축 %d > 자리 %d' % (st, k, len(c), z))
            at = d + p + 0x20; b[at:at + z] = c + bytes(z - len(c))
            previews.append((st, k, w, px))
            print('%s %3d 압축 %4d / %4d  %s' % (st, k, len(c), z, ko))
        if not ERR:
            open(os.path.join(ROOT, 'work', 'build', 'CHR_%s.MF' % st), 'wb').write(b)
    if ERR:
        print(chr(10).join(ERR)); sys.exit(1)
    sheet = Image.new('RGB', (290, 44 * len(previews)), (20, 20, 40)); dr = ImageDraw.Draw(sheet)
    for i, (st, k, w, px) in enumerate(previews):
        im = Image.new('RGB', (w, 32)); im.putdata([PAL[v] for r in px for v in r]); sheet.paste(im, (0, i * 44 + 10))
        dr.text((0, i * 44), '%s %d' % (st, k), fill=(255, 200, 0))
    sheet.resize((580, sheet.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'view', 'hints_ko.png'))


if __name__ == '__main__':
    main()
