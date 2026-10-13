# -*- coding: utf-8 -*-
r"""한글 대사 글자 그림(16×16 4bpp, 원본 글자판 꼴): Galmuri11 BDF 획 = 색 4, 8방향 둘레 1px = 색 2, 바탕 0.
  원본 글자는 (1,1)부터 약 13×13 칸(획 11~12px + 둘레). 문장부호·괄호는 원본 일본어 글자 그림을 그대로 쓴다(JP_REUSE).
  python tools/kfont.py  → work/view/kfont_preview.png (원본 상자 010 과 한글 번역 나란히)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
BDF = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11.bdf'
# 원본 그림을 그대로 쓰는 부호(glyph_chars.tsv 의 글자 → 그 그림)
JP_REUSE = set('！？‼⁉…「」（）〜ー　、。')
ALIAS = {' ': '　'}   # 반각 공백 = 원본 빈 칸 그림

_bdf = None


def bdf():
    global _bdf
    if _bdf is None:
        _bdf = {}; cur = None
        for l in open(BDF, encoding='latin1'):
            p = l.split()
            if not p:
                continue
            if p[0] == 'ENCODING':
                cur = {'enc': int(p[1])}
            elif p[0] == 'DWIDTH' and cur is not None:
                cur['dw'] = int(p[1])
            elif p[0] == 'BBX' and cur is not None:
                cur['bbx'] = tuple(map(int, p[1:5]))
            elif p[0] == 'BITMAP' and cur is not None:
                cur['rows'] = []
            elif p[0] == 'ENDCHAR' and cur is not None:
                _bdf[chr(cur['enc'])] = cur; cur = None
            elif cur is not None and 'rows' in cur:
                cur['rows'].append(int(p[0], 16) << (8 * ((len(p[0]) + 1) // 2) - len(p[0]) * 4 if False else 0))
                cur.setdefault('hexlen', len(p[0]))
    return _bdf


def ink(ch):
    """→ set((x, y)) 11px 칸 기준 좌표(기준선 위 ascent 11)"""
    g = bdf()[ch]; w, h, xo, yo = g['bbx']; bits = g.get('hexlen', 0) * 4
    pts = set()
    top = 11 - (h + yo) - 1 + 1   # 한글 BBX 11 11 0 0 → top 0
    for r, v in enumerate(g['rows']):
        for c in range(w):
            if v >> (bits - 1 - c) & 1:
                pts.add((xo + c, top + r))
    return pts


def render(ch, ox=2, oy=2):
    """→ 16×16 값 배열(0 바탕 · 2 둘레 · 4 획)"""
    a = [[0] * 16 for _ in range(16)]
    for x, y in ink(ch):
        X, Y = x + ox, y + oy
        if 0 <= X < 16 and 0 <= Y < 16:
            a[Y][X] = 4
    for y in range(16):
        for x in range(16):
            if a[y][x] == 0 and any(0 <= y + dy < 16 and 0 <= x + dx < 16 and a[y + dy][x + dx] == 4
                                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                a[y][x] = 2
    return a


def pack(a):
    return bytes((a[y][x] << 4) | a[y][x + 1] for y in range(16) for x in range(0, 16, 2))


def unpack(b):
    return [[(b[(y * 16 + x) // 2] >> (4 if x % 2 == 0 else 0)) & 15 for x in range(16)] for y in range(16)]


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    from PIL import Image
    import vsdec, vstext
    out, glyphs = vsdec.decode(); inv = {v: k for k, v in glyphs.items()}
    ch2g = {}
    for g, c in vstext.chars().items():
        ch2g.setdefault(c, g)
    PAL = {0: (16, 24, 120), 1: (40, 40, 160), 2: (30, 60, 200), 3: (150, 200, 255), 4: (230, 250, 255)}

    def cell(c):
        if c in JP_REUSE and c in ch2g:
            return unpack(inv[ch2g[c]])
        return render(c)

    lines = ['アプリ、何か企んでる', 'みたいだわさ。', '아프리가 뭔가', '꾸미는 것 같다구.',
             '쳇！이 녀석이 보윌로를', '갖고 있는 줄 알았는데…', '「보윌로」를 찾아내야 한다구！']
    img = Image.new('RGB', (16 + 13 * 20, 16 + 16 * len(lines)), PAL[0])
    for li, s in enumerate(lines):
        for ci, c in enumerate(s):
            if c == ' ':
                continue
            a = cell(c)
            for y in range(16):
                for x in range(16):
                    if a[y][x]:
                        img.putpixel((8 + ci * 13 + x, 8 + li * 16 + y), PAL[min(a[y][x], 4)])
    img = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
    img.save(os.path.join(ROOT, 'work', 'view', 'kfont_preview.png'))


def glyph_bytes(c, jp):
    """c → 128B 4bpp 그림. jp = {일본어 글자: 원본 그림 128B} (부호·빈 칸 재사용)"""
    c = ALIAS.get(c, c)
    if c in JP_REUSE and c in jp:
        return jp[c]
    return pack(render(c))
