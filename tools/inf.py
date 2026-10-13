# -*- coding: utf-8 -*-
r"""백업 RAM 안내 그림(CHR_INF.MF SPT 0‥4, 4bpp LZ00) 한글로.
  0‥3: 검은 바탕(색 15) 위 회색 단계 글(1 어둠 … 4 흰색) → 바탕부터 통째로 다시 그림.
  4: 투명 바탕(0) — 위 새턴 그림(y < 145)은 두고 아래 글 줄만 지우고 다시 씀(1 흰 · 4/6/11 회색 단계).
  글꼴 나눔고딕 Bold 12px 안티에일리어싱. 압축은 원래 자리(z) 안 + 0 채움.
  python tools/inf.py → work/build/CHR_INF.MF + work/view/inf_ko.png
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, lz00
from PIL import Image, ImageDraw, ImageFont

FONT = r'C:\claude\utils\font\nanum-gothic\NanumGothicBold.ttf'
SAVE = 'L 버튼 또는 R 버튼을 누른 채 리셋 버튼을 누르면 세가새턴 본체의 저장 데이터 관리 화면으로 넘어갑니다.'
TEXT = {
    0: ['본체 RAM의 백업 준비가 아직 되어 있지 않습니다.(초기화되어 있지 않습니다)',
        '세가새턴 본체의 저장 데이터 관리 화면에서 모든 기록을 지워 주십시오.(초기화해 주십시오)', SAVE],
    1: ['카트리지 RAM의 백업 준비가 아직 되어 있지 않습니다.(초기화되어 있지 않습니다)',
        '세가새턴 본체의 저장 데이터 관리 화면에서 모든 기록을 지워 주십시오.(초기화해 주십시오)', SAVE],
    2: ['이대로 게임을 시작하면 기록을 저장할 수 없습니다.',
        '이 게임의 기록을 저장하려면 49의 빈 용량이 필요합니다.',
        '세가새턴 본체의 저장 데이터 관리 화면에서 다른 게임의 기록을 지우거나 카트리지 RAM에 복사한 뒤 게임을 다시 시작해 주십시오.',
        SAVE, '이대로 게임을 시작하려면 스타트 버튼을 눌러 주십시오.'],
    3: ['기록을 제대로 불러오지 못했습니다.'],
    4: ['가지고 계신, 또는 별매인 『확장 램 카트리지』와 함께 꽂아서 사용하면 추가 보이스를 즐길 수 있습니다.'],
}
LEVELS = {0: [15, 1, 2, 3, 4], 4: [0, 11, 6, 4, 1]}   # 알파 0‥4 단계 → 색(그림 0‥3 / 그림 4)


def wrap(font, para, width):
    out = []; cur = ''
    for w in para.split(' '):
        cand = (cur + ' ' + w) if cur else w
        if font.getlength(cand) <= width:
            cur = cand
        else:
            out.append(cur); cur = w
    out.append(cur)
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    b = bytearray(open(os.path.join(ROOT, 'work', 'disc', 'CHR_INF.MF'), 'rb').read())
    E = {n.split('.')[-1]: (o, d, sz) for n, o, d, sz in mf.entries(b)}
    o, d, sz = E['SPT']; items, _ = mf.spt_items(bytes(b[d:d + sz]))
    font = ImageFont.truetype(FONT, 12)
    sheet = Image.new('RGB', (340, 760), (255, 0, 0)); Y = 0
    for k, paras in TEXT.items():
        _, p, t, w, h, z = items[k]
        raw = lz00.decompress(bytes(b[d + p + 0x20:d + p + 0x20 + z]))
        px = [(raw[i // 2] >> 4) if i % 2 == 0 else raw[i // 2] & 15 for i in range(w * h)]
        lev = LEVELS[4 if k == 4 else 0]
        if k == 4:
            top, bottom, x0 = 145, h, 4
            for i in range(top * w, w * h):
                px[i] = 0
        else:
            top, bottom, x0 = 0, h, 6
            px = [15] * (w * h)
        lines = []
        for n, para in enumerate(paras):
            ls = wrap(font, para, w - 2 * x0)
            lines += [(l, n > 0 and i == 0) for i, l in enumerate(ls)]
        n = len(lines); gaps = sum(1 for _, g in lines if g)
        avail = bottom - top - (3 if k == 3 else 2)
        pitch = 15; gap = 3 if k != 4 else 0
        while n * pitch + gaps * gap > avail and pitch > 13:
            pitch -= 1
        if n * pitch + gaps * gap > avail:
            gap = 0
        if n * pitch + gaps * gap > avail:
            sys.exit('⛔ 그림 %d 줄 넘침 (%d줄)' % (k, n))
        y = top + (avail - (n * pitch + gaps * gap)) // 2 + 1
        a = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(a)
        for l, g in lines:
            y += gap if g else 0
            dr.text((x0, y - 1), l, font=font, fill=255); y += pitch
        A = a.load()
        for yy in range(h):
            for xx in range(w):
                v = A[xx, yy]
                if v >= 40:
                    px[yy * w + xx] = lev[min(4, 1 + v * 4 // 256)]
        raw = bytes((px[i] << 4) | px[i + 1] for i in range(0, w * h, 2))
        c = lz00.compress(raw); assert lz00.decompress(c) == raw
        if len(c) > z:
            sys.exit('⛔ 그림 %d 압축 %d > %d' % (k, len(c), z))
        at = d + p + 0x20; b[at:at + z] = c + bytes(z - len(c))
        print('그림 %d %d줄 간격 %d · 압축 %d / %d' % (k, n, pitch, len(c), z))
        g = [(0, 0, 0), (64, 64, 64), (128, 128, 128), (184, 184, 184), (248, 248, 248)] + [(0, 0, 0)] * 6 + [(56, 56, 56), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
        g4 = {0: (90, 0, 90), 1: (248, 248, 248), 4: (192, 184, 184), 6: (120, 128, 128), 11: (56, 56, 56)}
        im = Image.new('RGB', (w, h)); im.putdata([(g4.get(v, (150, 150, 150)) if k == 4 else g[v]) for v in px])
        sheet.paste(im, (0, Y)); Y += h + 4
    open(os.path.join(ROOT, 'work', 'build', 'CHR_INF.MF'), 'wb').write(b)
    sheet.resize((680, 1520), Image.NEAREST).save(os.path.join(ROOT, 'work', 'view', 'inf_ko.png'))


if __name__ == '__main__':
    main()
