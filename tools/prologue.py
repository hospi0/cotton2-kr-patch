# -*- coding: utf-8 -*-
r"""오프닝 스크롤 글(CHR_TTL.MF SPT 0·1·2 = 352×224 8bpp LZ00, 세로로 이어진 한 장 352×672) 한글로 다시 그리기.
  글 = 팔레트 0번에서 R ≥ 100 인 흰·회색 색(1‥16·19·24), 칸 x 40‥312 · 줄 y = 112 + 24n (19줄, 글자 높이 15, 폭 256 = 16자).
  지우기: 글 화소 + 둘레 1px → 주변 바탕 RGB 평균으로 안쪽까지 메움(반복) → 글 색 아닌 팔레트 색으로.
  쓰기: 나눔고딕 Bold 15px 흰 글자(안티에일리어싱) 를 바탕과 섞어 가장 가까운 팔레트 색.
  python tools/prologue.py  → work/build_gfx/ttl_{0,1,2}.raw + work/view/prologue_ko.png (원본|한글)
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, lz00
from PIL import Image, ImageDraw, ImageFont

FONT = r'C:\claude\utils\font\nanum-gothic\NanumGothicBold.ttf'
W, H = 352, 672
X0, X1 = 48, 304          # 글 칸(256px)
Y0, PITCH = 112, 24
NLINE = 19
SIZE = 15

TEXT = [
    '　요정의 나라 필라멘트에서 멀리 남쪽에 있는 펌프킨 왕국에서는, 마력을 품은 국보 「물의윌로」의 힘으로 사람들이 모두 평화롭게 살고 있었습니다.',
    '　그러던 어느 날, 왕실 제일의 말괄량이 아가씨 「아프리」는 「물의윌로」의 마력으로 자기 소원을 이루려고, 한밤중에 몰래 성에서 가지고 나와 버렸습니다.',
    '　그런데 갑자기 불어온 회오리바람에 아프리는 「물의윌로」와 함께 마을 밖 숲까지 날려 가 버렸습니다. 게다가 정신을 차려 보니 손에 있던 물의윌로가 사라져 버린 게 아니겠어요! 이런, 큰일! 아프리는 허둥지둥 「물의윌로」를 찾기 시작했습니다. 그때・・・',
]


def load():
    b = open(os.path.join(ROOT, 'work', 'disc', 'CHR_TTL.MF'), 'rb').read()
    E = {n.split('.')[-1]: (o, d, sz) for n, o, d, sz in mf.entries(b)}
    o, d, sz = E['SPT']; s = b[d:d + sz]; items, _ = mf.spt_items(s)
    o2, d2, _ = E['SPL']; spl = b[d2:d2 + 512]
    pal = [struct.unpack_from('>H', spl, 2 * i)[0] for i in range(256)]
    pal = [((v & 31) * 8, ((v >> 5) & 31) * 8, ((v >> 10) & 31) * 8) for v in pal]
    raw = b''
    for k in (0, 1, 2):
        _, p, t, w, h, z = items[k]
        raw += lz00.decompress(s[p + 0x20:p + 0x20 + z])
    return pal, bytearray(raw)


def wrap(font):
    lines = []
    for para in TEXT:
        words = para.split(' '); cur = ''
        for w in words:
            cand = (cur + ' ' + w) if cur else w
            if font.getlength(cand) <= X1 - X0:
                cur = cand
            else:
                if font.getlength(w) > X1 - X0:
                    sys.exit('낱말이 한 줄보다 김: ' + w)
                lines.append(cur); cur = w
        lines.append(cur)
    return lines


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    pal, raw = load(); orig = bytes(raw)
    TEXTC = {i for i in range(256) if pal[i][0] >= 100}
    BG = [i for i in range(1, 256) if i not in TEXTC]

    def near(rgb, cands):
        return min(cands, key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i], rgb)))
    cache = {}

    def nearbg(rgb):
        k = tuple(c // 4 for c in rgb)
        if k not in cache:
            cache[k] = near(rgb, BG)
        return cache[k]

    # 1) 지우기 마스크
    mask = set()
    for y in range(Y0 - 3, Y0 + PITCH * NLINE):
        if y >= H:
            break
        for x in range(X0 - 8, X1 + 8):
            if raw[y * W + x] in TEXTC:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        mask.add((x + dx, y + dy))
    rgb = {(x, y): pal[raw[y * W + x]] for y in range(H) for x in range(W)}
    todo = set(mask)
    while todo:
        done = {}
        for (x, y) in todo:
            nb = [rgb[(x + dx, y + dy)] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))
                  if (x + dx, y + dy) in rgb and (x + dx, y + dy) not in todo]
            if len(nb) >= 2:
                done[(x, y)] = tuple(sum(c[i] for c in nb) // len(nb) for i in range(3))
        if not done:
            break
        for k, v in done.items():
            rgb[k] = v; todo.discard(k)
    for (x, y) in mask:
        raw[y * W + x] = nearbg(rgb[(x, y)])
        rgb[(x, y)] = pal[raw[y * W + x]]
    # 2) 한글 쓰기
    font = ImageFont.truetype(FONT, SIZE)
    lines = wrap(font)
    print('줄 %d / %d' % (len(lines), NLINE))
    for l in lines:
        print('  ', l)
    if len(lines) > NLINE:
        sys.exit('⛔ 줄 수 넘침')
    alpha = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(alpha)
    for n, l in enumerate(lines):
        dr.text((X0, Y0 + PITCH * n - 1), l, font=font, fill=255)
    A = alpha.load()
    for y in range(H):
        for x in range(W):
            a = A[x, y]
            if a < 24:
                continue
            bg = pal[raw[y * W + x]]
            c = tuple(int(bg[i] + (248 - bg[i]) * a / 255) for i in range(3))
            raw[y * W + x] = near(c, list(TEXTC) + [raw[y * W + x]]) if a > 200 else near(c, range(1, 256))
    out = os.path.join(ROOT, 'work', 'build_gfx'); os.makedirs(out, exist_ok=True)
    for k in range(3):
        open(os.path.join(out, 'ttl_%d.raw' % k), 'wb').write(bytes(raw[k * W * 224:(k + 1) * W * 224]))
    im = Image.new('RGB', (W * 2 + 8, H))
    a = Image.new('RGB', (W, H)); a.putdata([pal[x] for x in orig]); im.paste(a, (0, 0))
    c = Image.new('RGB', (W, H)); c.putdata([pal[x] for x in raw]); im.paste(c, (W + 8, 0))
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'view', 'prologue_ko.png'))


if __name__ == '__main__':
    main()
