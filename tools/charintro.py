# -*- coding: utf-8 -*-
r"""캐릭터 소개 그림(CHR_TTL SPT 6 = 코튼·실크, 10 = 아프리·니들) 글 한글로.
  원문 글 = 9px 높이 · 줄 간격 10 의 밝은 글씨(바탕보다 밝음). 줄 띠 안에서 «7×7 중앙값보다 밝기 합 +40 넘는 화소 + 둘레 1px» 를 지우고
  바탕 RGB 평균으로 메운 뒤 갈무리9(10px) 글씨를 흰색 85% 로 얹음(가장 가까운 팔레트 색).
  python tools/charintro.py → work/build_gfx/ttl_6.raw · ttl_10.raw + work/view/charintro_ko.png
"""
import os, sys, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ttlimg
from PIL import Image, ImageDraw, ImageFont

FONT = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri9.ttf'
W, H = 352, 224

# (줄 맨 위 y 목록, x0, x1) — 원문 실측 / 글 = (x, y, 문자열)
SPEC = {
    6: {
        'erase': [((39, 49), 112, 172),                              # コットン(루비)
                  ([53, 63, 73, 83], 40, 264), ([93, 103], 40, 230),
                  ((136, 146), 104, 160),                            # シルク
                  ([148, 158, 168, 178, 188, 198], 40, 236)],
        'text': [(None, 40, 'コ', '코튼'),
                 (44, 53, None, '본명 나타 데 코튼. 마법사.'),
                 (44, 63, None, '나이 불명. 정신 연령 5살.'),
                 (44, 73, None, '윌로를 정☆말☆정말 좋아해서'),
                 (44, 83, None, '윌로를 위해서라면 정의도 악도 상관없음.'),
                 (44, 93, None, '먹을 것에 집착하고 제멋대로에'),
                 (44, 103, None, '대충대충인 여자아이. 식욕 마왕.'),
                 (None, 137, 'シ', '실크'),
                 (44, 148, None, '요정의 나라 필라멘트의 요정.'),
                 (44, 158, None, '성실한 성격이지만 조금'),
                 (44, 168, None, '덜렁이.'),
                 (44, 178, None, '매번 코튼에게 휘둘려'),
                 (44, 188, None, '마음고생이 끊이지 않는 불쌍〜한'),
                 (44, 198, None, '18살 아가씨.')],
    },
    10: {
        'erase': [((35, 46), 120, 175),                              # アプリ
                  ([48, 58, 68, 78, 88, 98], 48, 262),
                  ((140, 150), 120, 185),                            # ニードル
                  ([155, 165, 175, 195], 48, 262), ([185], 48, 292)],
        'text': [(None, 36, 'ア', '아프리'),
                 (56, 48, None, '멋진 오빠한테는 홀딱〜'),
                 (48, 58, None, '넘어가는, 조금 지조 없는 성격에'),
                 (48, 68, None, '게다가 보통 사람과는 미적 감각이'),
                 (48, 78, None, '꽤 어긋나 있는 모양.'),
                 (48, 88, None, '기가 세고 자신감 과잉이지만, 기운'),
                 (48, 98, None, '넘치는 여자아이.'),
                 (None, 141, 'ニ', '니들'),
                 (56, 155, None, '대대로 고귀한 가문을 섬기는 성령.'),
                 (48, 165, None, '49대째인 그는 아프리의 모자에'),
                 (48, 175, None, '깃들어 아프리의 감시역을 맡고'),
                 (48, 185, None, '있다. 가족을 아끼는 좋은 아빠지만,'),
                 (48, 195, None, '조금 잔소리가 많다. 자식은 3명.')],
    },
}


def bands(spec):
    for rows, x0, x1 in spec:
        if isinstance(rows, tuple):
            yield range(rows[0], rows[1] + 1), x0, x1   # 루비 띠(길이 10 이상)
        else:
            for y in rows:
                yield range(y - 1, y + 10), x0, x1


def process(k):
    raw, pal, _ = ttlimg.load(k); orig = bytes(raw)
    L = [sum(pal[v]) for v in raw]
    sp = SPEC[k]
    mask = set(); ruby_c = {}
    for ys, x0, x1 in bands(sp['erase']):
        for y in ys:
            for x in range(x0, x1):
                nb = [L[(y + dy) * W + x + dx] for dy in range(-3, 4) for dx in range(-3, 4)]
                if L[y * W + x] - statistics.median(nb) > 40:
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            mask.add((x + dx, y + dy))
    # 루비 가운데(지우기 전 실측)
    for ys, x0, x1 in bands(sp['erase']):
        if len(ys) > 10:
            xs = [x for (x, y) in mask if y in ys and x0 <= x < x1]
            ruby_c[ys.start] = (min(xs) + max(xs)) / 2 if xs else (x0 + x1) / 2
    rgb = {(x, y): pal[raw[y * W + x]] for y in range(H) for x in range(W)}
    todo = set(mask)
    while todo:
        done = {}
        for (x, y) in todo:
            nb = [rgb[p] for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1))
                  if p in rgb and p not in todo]
            if len(nb) >= 2:
                done[(x, y)] = tuple(sum(c[i] for c in nb) // len(nb) for i in range(3))
        if not done:
            break
        for p, v in done.items():
            rgb[p] = v; todo.discard(p)
    cache = {}

    def near(c):
        key = tuple(v // 4 for v in c)
        if key not in cache:
            cache[key] = min(range(1, 256), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i], c)))
        return cache[key]
    for (x, y) in mask:
        raw[y * W + x] = near(rgb[(x, y)])
    font = ImageFont.truetype(FONT, 10)
    img = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(img)
    for x, y, rubykey, s in sp['text']:
        if rubykey:
            band = next(ys for ys, x0, x1 in bands(sp['erase']) if len(ys) > 10 and ys.start <= y < ys.stop)
            x = int(round(ruby_c[band.start] - font.getlength(s) / 2))
        lim = max(x1 for ys, x0, x1 in bands(sp['erase']) if y in ys or y + 4 in ys)
        if x + font.getlength(s) > lim + 2:
            print('⛔ 그림 %d 줄 넘침 %r (%d > %d)' % (k, s, x + font.getlength(s), lim))
        dr.text((x, y - 1), s, font=font, fill=1)
    A = img.load()
    for y in range(H):
        for x in range(W):
            if A[x, y]:
                bg = pal[raw[y * W + x]]
                raw[y * W + x] = near(tuple(int(bg[i] * 0.15 + (248, 240, 232)[i] * 0.85) for i in range(3)))
    os.makedirs(os.path.join(ROOT, 'work', 'build_gfx'), exist_ok=True)
    open(os.path.join(ROOT, 'work', 'build_gfx', 'ttl_%d.raw' % k), 'wb').write(bytes(raw))
    a = Image.new('RGB', (W, H)); a.putdata([pal[v] for v in orig])
    b = Image.new('RGB', (W, H)); b.putdata([pal[v] for v in raw])
    return a, b


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sheet = Image.new('RGB', (W * 2 + 4, H * 2 + 4))
    for j, k in enumerate((6, 10)):
        a, b = process(k)
        sheet.paste(a, (0, j * (H + 4))); sheet.paste(b, (W + 4, j * (H + 4)))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'view', 'charintro_ko.png'))


if __name__ == '__main__':
    main()
