# -*- coding: utf-8 -*-
r"""데모 노란 외침 그림(CHR_VS0 SPT 46 = «お前だっ!!» 232×48, 100 = «いっくぽ〜ん!!» 248×48, 4bpp LZ00) 한글로.
  색(색 뱅크 0x30F0): 1‥6 크림→갈색(밝은 테두리) · 7‥12 노랑→진갈색(몸통 위→아래) · 0 투명.
  몸통 = 위→아래 7‥10 그러데이션, 오른쪽·아래 가장자리 12, 오른쪽 아래 1‥2px 돌출 그림자 11, 왼쪽 위 가장자리 2.
  python tools/shout.py → work/build_gfx/vs0_46.raw · vs0_100.raw (4bpp) + work/view/shout_ko.png
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont

FONT = r'C:\claude\utils\font\logo\BlackHanSans.ttf'
PAL = [(0, 0, 60), (248, 248, 232), (232, 224, 192), (224, 200, 160), (208, 184, 120), (200, 160, 88), (184, 136, 48),
       (248, 240, 24), (224, 208, 24), (208, 168, 16), (184, 136, 16), (168, 96, 8), (144, 64, 8)]
ITEMS = {46: ('바로 너야!!', 232), 100: ('가자뿅~!!', 248)}


def draw(text, w, h=48, hl=2):
    size = 44
    while True:
        f = ImageFont.truetype(FONT, size)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= w - 6 and bb[3] - bb[1] <= h - 6:
            break
        size -= 1
    m = Image.new('1', (w, h), 0); dr = ImageDraw.Draw(m)
    x = (w - 3 - (bb[2] - bb[0])) // 2 - bb[0]; y = (h - 3 - (bb[3] - bb[1])) // 2 - bb[1]
    dr.text((x, y), text, font=f, fill=1)
    M = m.load(); top = min(yy for yy in range(h) for xx in range(w) if M[xx, yy]); bot = max(yy for yy in range(h) for xx in range(w) if M[xx, yy])
    px = [[0] * w for _ in range(h)]
    inside = lambda xx, yy: 0 <= xx < w and 0 <= yy < h and M[xx, yy]
    for yy in range(h):
        for xx in range(w):
            if inside(xx, yy):
                t = (yy - top) / max(1, bot - top)
                c = 7 + min(3, int(t * 4))
                if not inside(xx + 1, yy) or not inside(xx, yy + 1):
                    c = 12
                elif not inside(xx - 1, yy) or not inside(xx, yy - 1):
                    c = hl
                px[yy][xx] = c
            elif inside(xx - 1, yy - 1) or inside(xx - 2, yy - 2) or inside(xx - 1, yy - 2):
                px[yy][xx] = 11
    return px


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    out = os.path.join(ROOT, 'work', 'build_gfx'); os.makedirs(out, exist_ok=True)
    sheet = Image.new('RGB', (250, 100), PAL[0])
    for j, (k, (text, w)) in enumerate(ITEMS.items()):
        px = draw(text, w)
        raw = bytes((px[y][x] << 4) | px[y][x + 1] for y in range(48) for x in range(0, w, 2))
        open(os.path.join(out, 'vs0_%d.raw' % k), 'wb').write(raw)
        im = Image.new('RGB', (w, 48)); im.putdata([PAL[c] for row in px for c in row]); sheet.paste(im, (0, j * 50))
    sheet.resize((750, 300), Image.NEAREST).save(os.path.join(ROOT, 'work', 'view', 'shout_ko.png'))


if __name__ == '__main__':
    main()
