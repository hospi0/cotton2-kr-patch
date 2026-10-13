# -*- coding: utf-8 -*-
r"""대화 장면 한글 빌드: CHR_VS*.MF(SCH 글 구역 다시 쓰기 + SPT 재배치) · VS*.BIN(상자 머리 포인터).
  입력: work/disc 원본 · work/text/vs_ja.tsv 번역 칸(fill.py 통과분)
  출력: work/build/CHR_VS*.MF · work/build/VS*.BIN (디스크 이미지는 안 건드림)

  SCH: 크기·항목 수 그대로. 명령 블록·초상화 자리 불변, 글 구역 [T, Z) 만 다시 씀.
       상자는 원래 머리 번호에 두고(남는 칸 = ED 복사본, 안 읽힘), 앞 상자가 길어 밀리면 뒤로 — 밀린 상자는 VS*.BIN 포인터를 고침.
       명령 칸 항목 = 그 장면 명령 블록 항목 바이트 그대로, 글자 항목 = 그 장면 원래 글자 항목 꼴(팔레트·x·y) + 새 SPT 오프셋.
  SPT: 글 구역에서만 쓰던 항목을 빼고 나머지는 원래 순서·바이트 그대로, 한글 글자 항목을 끝에 붙임 → SCH 오프셋 전부 다시 맞춤.
       MF 가 원래 크기를 넘으면 드물게 쓰는 글자부터 LZ00 압축 항목(종류 1)으로 바꿔 원래 크기 이하로.
  python tools/build_vs.py
"""
import os, struct, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, vsdec, vsasm, kfont, lz00, vstext, rules

DISC = os.path.join(ROOT, 'work', 'disc')
OUT = os.path.join(ROOT, 'work', 'build')
BASE = 0x0606E000
BIN_OF = {'VS70': 'VS7'}
GFX_SCENES = {'VS0', 'VS7', 'VS70'}


def translations():
    rows = [l.split('\t') for l in open(os.path.join(ROOT, 'work', 'text', 'vs_ja.tsv'), encoding='utf-8').read().splitlines()[1:]]
    B = rules.budget([(r[0], r[1], r[2], r[3]) for r in rows])
    ko = {}
    for r in rows:
        i, pos, sp, ja, k = (r + [''])[:5]
        w, h = B[(pos.split(':')[0], sp)]
        bad, _ = rules.validate(ja, k, w, h)
        if bad:
            sys.exit('⛔ 번역 %s 규칙 위반: %s' % (i, '; '.join(bad)))
        for p in pos.split(','):
            sc, a = p.split(':'); ko[(sc, int(a))] = rules.squeeze(k)
    return ko


def jp_glyphs():
    out, glyphs = vsdec.decode(); inv = {v: k for k, v in glyphs.items()}
    jp = {}
    for g, c in vstext.chars().items():
        if g in inv:
            jp.setdefault(c, inv[g])
    return out, jp


def build_scene(sc, toks, ko, jp):
    b, e, offs, ents, s, items = vsdec.load(sc)
    zs = [i for i, t in enumerate(toks) if t == ('c', 'z')]; T = zs[0] + 1; Z = zs[-1]
    # 명령 이름 → 명령 블록 안 SCH 자리
    ctrl = {}
    for i in range(T):
        t = toks[i]
        if t and t[0] == 'c':
            ctrl.setdefault(t[1], i)
    # 원래 글자 항목 꼴
    tmpl = next(ents[i] for i in range(T, Z) if toks[i][0] == 'g')
    eds = [i for i, t in enumerate(toks) if t == ('c', 'ED')]
    boxes = []
    for a, bb in zip(eds, eds[1:]):
        if bb < T or a >= Z:
            continue
        head = max(a + 1, T); orig = toks[head:bb + 1]
        for t in orig:
            if t[0] == 'x':
                sys.exit('%s 상자 %d 에 알 수 없는 항목 %r' % (sc, a, t))
        k = ko.get((sc, a))
        if k is None:   # 부호만 있는 상자(예 VS4 «…………。») — 원문 그대로 다시 조립
            k = ''.join(vstext.chars()[t[1]] for t in orig if t[0] == 'g') if all(
                t[0] != 'g' or t[1] in vstext.chars() for t in orig) else None
            k = '/'.join(x for x in [k] if x)
        new = vsasm.assemble(orig, k)
        skip = 0
        while orig[skip] == ('c', 'z'):
            skip += 1
        boxes.append((head, len(orig), new, skip))
    # 자리 배치
    # 앞→뒤: 원래 머리 이상, 앞 상자 끝 이상 / 뒤→앞: 다음 상자 시작(마지막은 Z) 안에 들도록 당김
    ats = []; pos = T
    for head, olen, new, skip in boxes:
        at = max(pos, head); ats.append(at); pos = at + len(new)
    lim = Z
    for n in range(len(boxes) - 1, -1, -1):
        ats[n] = min(ats[n], lim - len(boxes[n][2])); lim = ats[n]
    if ats and ats[0] < T:
        sys.exit('%s 글 구역 넘침 (필요 %d > %d)' % (sc, sum(len(x[2]) for x in boxes), Z - T))
    place = {}; seq = {}
    for (head, olen, new, skip), at in zip(boxes, ats):
        place[head + skip] = at + skip
        for j, t in enumerate(new):
            seq[at + j] = t
    # 한글 글자 목록(빈도 순)
    freq = collections.Counter(t[1] for t in seq.values() if t[0] == 'k')
    chars = sorted(freq, key=lambda c: (-freq[c], c))
    # SPT 재배치
    used = collections.defaultdict(set)
    for i, en in enumerate(ents):
        if len(en) >= 4:
            used[struct.unpack_from('>I', en, 0)[0]].add(T <= i < Z)
    keep = []
    for k, p, t, w, h, z in items:
        if used.get(p) == {True}:
            continue
        blob = s[p:p + 0x20 + z]
        gfx = os.path.join(ROOT, 'work', 'build_gfx', '%s_%d.raw' % (sc.lower(), k))
        if sc in GFX_SCENES and os.path.exists(gfx):   # 그림 글(외침) 교체 — tools/shout.py
            raw = open(gfx, 'rb').read(); assert len(raw) == w * h // 2, gfx
            dd = lz00.compress(raw); assert lz00.decompress(dd) == raw
            dd += bytes(-len(dd) % 4)
            hh = bytearray(blob[:0x20]); struct.pack_into('>I', hh, 8, len(dd)); blob = bytes(hh) + dd
            print('  %s 그림 %d 교체 (%d → %d B)' % (sc, k, z, len(dd)))
        keep.append((p, blob))
    sptlen_orig = e['SPT'][1]
    hdr0 = next(s[p:p + 0x20] for k, p, t, w, h, z in items if (t, w, h, z) == (0, 16, 16, 128))
    raw = {c: kfont.glyph_bytes(c, jp) for c in chars}
    comp = set()

    def gitem(c):
        if c in comp:
            d = lz00.compress(raw[c]); assert lz00.decompress(d) == raw[c]
            d += b'\0' * (-len(d) % 4)
            h = bytearray(hdr0); struct.pack_into('>I', h, 8, len(d))   # 종류 칸(0 = 4bpp)은 그대로, 압축은 «LZ00» 머리로 판별
            return bytes(h) + d
        return hdr0 + raw[c]

    while True:
        spt = bytearray(); remap = {}
        for p, blob in keep:
            remap[p] = len(spt); spt += blob
        goff = {}
        for c in chars:
            goff[c] = len(spt); spt += gitem(c)
        if len(spt) <= sptlen_orig:
            break
        cand = [c for c in reversed(chars) if c not in comp]
        if not cand:
            sys.exit('%s SPT 를 원래 크기로 못 맞춤 %d > %d' % (sc, len(spt), sptlen_orig))
        comp.add(cand[0])
    # 항목 끝에 원래처럼 0 이 남는지(spt_items 끝 판정용): 원래 SPT 꼬리 패딩 유지
    spt += b'\0' * (sptlen_orig - len(spt))   # SPT·MF 크기를 원래와 똑같이(뒤는 0 = spt_items 끝)
    # SCH 다시 쓰기
    d, sz = e['SCH']; sch = bytearray(b[d:d + sz])
    for i, o in enumerate(offs):
        if o == 0xFFFFFFFF:
            continue
        en = bytearray(sch[o:o + 20])
        if T <= i < Z:
            t = seq.get(i, ('c', 'ED'))
            if t[0] == 'c':
                en = bytearray(ents[ctrl[t[1]]])
                po, = struct.unpack_from('>I', en, 0); struct.pack_into('>I', en, 0, remap[po])
            else:
                en = bytearray(tmpl); struct.pack_into('>I', en, 0, goff[t[1]])
        else:
            po, = struct.unpack_from('>I', en, 0); struct.pack_into('>I', en, 0, remap[po])
        sch[o:o + 20] = en
    # MF 다시 묶기
    outb = bytearray()
    for name, off, dd, ssz in mf.entries(b):
        h = bytearray(b[off:off + 0x20])
        body = bytes(sch) if name.endswith('.SCH') else bytes(spt) if name.endswith('.SPT') else b[dd:dd + ssz]
        tot, = struct.unpack_from('>I', b, off)
        if len(body) != ssz:
            sys.exit('%s %s 크기 바뀜' % (sc, name))
        outb += b[off:off + 0x20] + body + b[dd + ssz:off + tot]   # 머리·4B 맞춤 채움 원래 그대로
    tail = b[sum(struct.unpack_from('>I', b, off)[0] for _, off, _, _ in mf.entries(b)):]
    outb += tail
    return bytes(outb), place, T, Z, len(chars), len(comp), len(b)


def patch_bin(sc, place, T, Z):
    d = bytearray(open(os.path.join(DISC, '%s.BIN' % sc), 'rb').read())
    # 글 구역을 덮는 연속 번호 나열 찾기
    runs = []
    i = 0
    while i < len(d) - 4:
        v, = struct.unpack_from('>H', d, i); n = 1
        while i + 2 * n + 2 <= len(d) and struct.unpack_from('>H', d, i + 2 * n)[0] == v + n:
            n += 1
        if v <= T and v + n - 1 >= Z - 1 and n > 50:
            runs.append((i, v, n))
        i += 2 * n if n > 1 else 2
    if not runs:
        sys.exit('%s 글 구역을 덮는 번호 나열 없음' % sc)
    ro, rv, rn = min(runs, key=lambda r: r[2])   # 공용 225칸 표보다 짧은 장면 전용 나열
    refs = collections.defaultdict(list)
    for o in range(0, len(d) - 4, 2):
        p = struct.unpack_from('>I', d, o)[0] - BASE
        if ro <= p < ro + 2 * rn and (p - ro) % 2 == 0:
            refs[rv + (p - ro) // 2].append(o)
    moved = 0
    for head, at in place.items():
        if head == at:
            continue
        if not refs.get(head):
            sys.exit('%s 상자 머리 %d 가 밀렸는데(%d) 가리키는 포인터가 없음' % (sc, head, at))
        for o in refs[head]:
            struct.pack_into('>I', d, o, BASE + ro + 2 * (at - rv)); moved += 1
    return bytes(d), moved


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(OUT, exist_ok=True)
    ko = translations(); out, jp = jp_glyphs()
    places = {}
    for sc in vsdec.SCENES:
        mfb, place, T, Z, nch, ncomp, olen = build_scene(sc, out[sc], ko, jp)
        open(os.path.join(OUT, 'CHR_%s.MF' % sc), 'wb').write(mfb)
        places[sc] = (place, T, Z)
        print('%-5s MF %d → %d (%+d) · 한글 %d자(압축 %d) · 밀린 상자 %d' % (
            sc, olen, len(mfb), len(mfb) - olen, nch, ncomp, sum(1 for h, a in place.items() if h != a)))
    if places['VS7'][0] != places['VS70'][0]:
        sys.exit('VS7 / VS70 상자 배치가 다름 — VS7.BIN 을 같이 못 씀')
    for sc in ['VS0', 'VS1', 'VS2', 'VS3', 'VS4', 'VS5', 'VS6', 'VS7']:
        place, T, Z = places[sc]
        binb, moved = patch_bin(sc, place, T, Z)
        open(os.path.join(OUT, '%s.BIN' % sc), 'wb').write(binb)
        print('%-5s BIN 포인터 %d 곳 고침' % (sc, moved))


if __name__ == '__main__':
    main()
