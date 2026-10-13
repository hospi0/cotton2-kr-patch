# -*- coding: utf-8 -*-
r"""대화 장면(VS*.BIN + CHR_VS*.MF) 글 상자 전수.
  VS*.BIN 적재 0x0606E000(VS0 스테이트 확인). 글 상자 레코드 = [u32 포인터 → u16 자리 번호 나열][i16 x][i16 y] …
  포인터가 가리키는 곳 = 0‥N 오름 번호표 안. 상자 길이 = 다음 상자 시작 번호까지(같은 번호표 안 정렬 기준), 마지막은 SCH 끝까지.
  자리 번호 → CHR_VS*.SCH 항목(u32 = SPT 안 그림 머리 오프셋) → 16×16 그림.
  python tools/vsscan.py  → work/text/boxes.tsv (장면·상자·레코드 위치·x·y·시작 번호·길이·그림 오프셋 나열)
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf
BASE = 0x0606E000
DISC = os.path.join(ROOT, 'work', 'disc')


def sch_table(b):
    e = {n.split('.')[-1]: (d, sz) for n, o, d, sz in mf.entries(b)}
    d, sz = e['SCH']; s = b[d:d + sz]
    first, = struct.unpack_from('>I', s, 0)
    offs = [struct.unpack_from('>I', s, 4 * i)[0] for i in range(first // 4)]
    ents = [s[o:o + 20] for o in offs]
    return e, offs, ents


def scene_boxes(vs, mfname):
    v = open(os.path.join(DISC, vs), 'rb').read()
    b = open(os.path.join(DISC, mfname), 'rb').read()
    e, offs, ents = sch_table(b)
    ncode = len(offs)
    recs = []
    for o in range(0, len(v) - 8, 2):
        p, = struct.unpack_from('>I', v, o)
        if not (BASE <= p < BASE + len(v)) or (p - BASE) % 2:
            continue
        t = p - BASE
        # 포인터 대상이 «오름 번호표» 인지: 대상 앞뒤로 +1 씩 이어짐
        try:
            seq = struct.unpack_from('>8H', v, t)
        except struct.error:
            continue
        if not all(seq[i + 1] == seq[i] + 1 for i in range(7)):
            continue
        x, y = struct.unpack_from('>hh', v, o + 4)
        if not (-200 < x < 200 and -150 < y < 150):
            continue
        recs.append((o, p, x, y, seq[0]))
    starts = sorted({r[4] for r in recs})
    out = []
    for o, p, x, y, st in recs:
        nxt = [s for s in starts if s > st]
        end = nxt[0] if nxt else ncode
        glyph = [struct.unpack_from('>I', ents[c], 0)[0] if c < ncode and len(ents[c]) >= 4 else None for c in range(st, end)]
        out.append((o, x, y, st, end - st, glyph))
    return out, e


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(os.path.join(ROOT, 'work', 'text'), exist_ok=True)
    w = open(os.path.join(ROOT, 'work', 'text', 'boxes.tsv'), 'w', encoding='utf-8')
    w.write('장면\t레코드\tx\ty\t시작\t길이\t그림오프셋\n')
    for k in range(8):
        vs = 'VS%d.BIN' % k
        for mfn in (['CHR_VS%d.MF' % k] + (['CHR_VS70.MF'] if k == 7 else [])):
            if not os.path.exists(os.path.join(DISC, vs)):
                continue
            boxes, _ = scene_boxes(vs, mfn)
            print(vs, mfn, '상자', len(boxes), [(hex(o), x, y, hex(st), n) for o, x, y, st, n, g in boxes])
            for o, x, y, st, n, g in boxes:
                w.write('%s\t%05X\t%d\t%d\t%X\t%d\t%s\n' % (mfn, o, x, y, st, n, ' '.join('%X' % q if q is not None else '-' for q in g)))
