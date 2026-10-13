# -*- coding: utf-8 -*-
r"""엔딩 스태프 롤(CHR_VS7/VS70.MF SPT 166‥220, w×16 4bpp LZ00, 대사 글꼴 13px) + 엔딩 외침 164(272×48) 한글로.
  직함·회사명만 옮기고 사람 이름(한자·가나)은 원래 그림 그대로 둔다(예외: 201 «M.D.S.-자키★사사오카»).
  CRED: 항목 → [(지울 x0, x1, 쓸 한글)] — x0‥x1 열을 지우고 x0 부터 한글(띄어쓰기 6px).
  python tools/credits.py → work/build_gfx/vs7_<k>.raw · vs70_<k>.raw (build_vs 가 교체) + work/view/credits_ko.png
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vsdec, lz00, kfont, build_vs, shout
from PIL import Image

SPACE = 6
COMMON = {
    166: [(0, None, '캐스트')],
    167: [(0, 130, '코튼')],
    168: [(0, 130, '아프리')],
    169: [(0, None, '협력 （유）켄 프로덕션')],
    173: [(0, None, '치프 프로그래머')],
    175: [(0, None, '알고리즘·보스 프로그램')],
    177: [(0, None, '적 캐릭터 프로그램')],
    179: [(0, None, '비주얼 프로그램')],
    182: [(0, None, '치프 디자이너')],
    184: [(0, None, '캐릭터 디자인')],
    186: [(0, None, '몬스터 디자인')],
    188: [(0, None, '배경 디자인')],
    190: [(0, None, '배경 협력')],
    192: [(0, None, '（유）이시가키 프로덕션')],
    194: [(0, None, '뮤직 컴포저')],
    196: [(0, None, '홍보')],
    199: [(0, None, '협력')],
    202: [(0, None, '스페셜 땡스')],
    211: [(0, None, '프로듀서')],
}
CRED_OFF = {
    'VS7': {**COMMON, **{201: [(61, None, '자키★사사오카')], 220: [(0, None, '스태프')]}},
    'VS70': {**COMMON, **{220: [(0, None, '새턴판 스태프')]}},
}
CRED = {'VS7': {}, 'VS70': {}}   # 2026-10-13 사용자: 스태프 롤은 안 함 → 외침 164 만
SHOUT = (164, '맛이 문제가 아니잖아!!', 272)


def unpack4(x, w, h):
    return [[((x[(y * w + c) // 2] >> 4) if c % 2 == 0 else x[(y * w + c) // 2] & 15) for c in range(w)] for y in range(h)]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    _, jp = build_vs.jp_glyphs()
    out = os.path.join(ROOT, 'work', 'build_gfx')
    prev = []; err = []
    for sc, spec in CRED.items():
        b, e, offs, ents, s, items = vsdec.load(sc)
        for k, ops in spec.items():
            _, p, t, w, h, z = items[k]
            x = s[p + 0x20:p + 0x20 + z]; x = lz00.decompress(x) if x[:4] == b'LZ00' else x
            px = unpack4(x, w, h)
            for x0, x1, text in ops:
                x1 = w if x1 is None else x1
                for y in range(h):
                    for c in range(x0, x1):
                        px[y][c] = 0
                cx = x0
                for ch in text:
                    if ch in ' 　':
                        cx += SPACE; continue
                    if cx + 16 > x1 + 3 and cx + 13 > x1:
                        err.append('%s %d 넘침: %s' % (sc, k, text)); break
                    g = kfont.unpack(kfont.glyph_bytes(ch, jp))
                    for y in range(16):
                        for c in range(16):
                            v = g[y][c]; X = cx + c - 1
                            if v and 0 <= X < w and y - 1 >= 0 and v >= px[y - 1][X]:
                                px[y - 1][X] = v
                    cx += 13
            raw = bytes((px[y][c] << 4) | px[y][c + 1] for y in range(h) for c in range(0, w, 2))
            open(os.path.join(out, '%s_%d.raw' % (sc.lower(), k)), 'wb').write(raw)
            prev.append((sc, k, w, h, px))
        k, text, w = SHOUT
        spx = shout.draw(text, w, hl=7)
        open(os.path.join(out, '%s_%d.raw' % (sc.lower(), k)), 'wb').write(
            bytes((spx[y][c] << 4) | spx[y][c + 1] for y in range(48) for c in range(0, w, 2)))
        if sc == 'VS7':
            prev.append((sc, k, w, 48, spx))
    if err:
        print('\n'.join(err)); sys.exit(1)
    H = sum(h + 4 for *_, h, _ in prev)
    sheet = Image.new('RGB', (280, H), (20, 20, 40)); Y = 0
    pal = shout.PAL + [(255, 0, 255)] * 3
    gpal = [(0, 0, 40), (60, 60, 120), (40, 80, 200), (150, 200, 255), (230, 250, 255)] + [(255, 0, 255)] * 11
    for sc, k, w, h, px in prev:
        im = Image.new('RGB', (w, h)); im.putdata([(pal if h == 48 else gpal)[v] for r in px for v in r]); sheet.paste(im, (0, Y)); Y += h + 4
    sheet.resize((560, H * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'view', 'credits_ko.png'))


if __name__ == '__main__':
    main()
