# -*- coding: utf-8 -*-
r"""빌드 검산: work/build/CHR_VS*.MF · VS*.BIN 을 다시 풀어
  1) 글 구역 밖 SCH 항목이 원본과 «같은 그림·같은 항목 바이트(오프셋 빼고)»인지
  2) 명령 블록·SAN·SPL·SIF 바이트 불변
  3) 상자 레코드 포인터 → 번호 나열 → SCH 를 ED 까지 따라 읽은 글이 번역문(조판 기호 포함)과 같은지
  4) 한글 글자 그림(압축 항목은 풀어서)이 kfont 그림과 같은지
  python tools/verify_vs.py
"""
import os, struct, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, vsdec, vsscan, lz00, kfont, build_vs

DISC = os.path.join(ROOT, 'work', 'disc'); OUT = os.path.join(ROOT, 'work', 'build')


def parse(b):
    e = {n.split('.')[-1]: (d, sz) for n, o, d, sz in mf.entries(b)}
    d, sz = e['SCH']; s = b[d:d + sz]
    first, = struct.unpack_from('>I', s, 0)
    offs = [struct.unpack_from('>I', s, 4 * i)[0] for i in range(first // 4)]
    ents = [s[o:o + 20] if o != 0xFFFFFFFF else b'' for o in offs]
    d, sz = e['SPT']; spt = b[d:d + sz]
    items, _ = mf.spt_items(spt)
    data = {}
    for k, p, t, w, h, z in items:
        x = spt[p + 0x20:p + 0x20 + z]
        data[p] = lz00.decompress(x) if x[:4] == b'LZ00' else x
        data[p] = (t, w, h, data[p])
    return e, ents, data


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ko = build_vs.translations(); out, jp = build_vs.jp_glyphs()
    nbad = 0
    for sc in vsdec.SCENES:
        ob = open(os.path.join(DISC, 'CHR_%s.MF' % sc), 'rb').read()
        nb = open(os.path.join(OUT, 'CHR_%s.MF' % sc), 'rb').read()
        oe, oents, odata = parse(ob); ne, nents, ndata = parse(nb)
        toks = out[sc]; zs = [i for i, t in enumerate(toks) if t == ('c', 'z')]; T = zs[0] + 1; Z = zs[-1]
        bad = []
        if len(oents) != len(nents):
            bad.append('SCH 항목 수 다름')
        for i in range(len(oents)):
            if T <= i < Z or not oents[i]:
                continue
            oo, = struct.unpack_from('>I', oents[i], 0); no, = struct.unpack_from('>I', nents[i], 0)
            gfx = os.path.join(ROOT, 'work', 'build_gfx', '%s_%d.raw' % (sc.lower(), i))
            if sc in build_vs.GFX_SCENES and os.path.exists(gfx):
                if ndata[no][3] != open(gfx, 'rb').read():
                    bad.append('그림 %d 교체본 다름' % i)
                continue
            if oents[i][4:] != nents[i][4:] or odata[oo] != ndata[no]:
                bad.append('SCH %d 바뀜' % i)
        for k in ('SPL', 'SAN', 'SIF'):
            if ob[oe[k][0]:oe[k][0] + oe[k][1]] != nb[ne[k][0]:ne[k][0] + ne[k][1]]:
                bad.append(k + ' 바뀜')
        # 명령 그림 → 이름
        cm = vsdec.ctrl_map()
        g2c = {}
        rev = {}
        for (sc2, a), k in ko.items():
            pass
        # 글자 그림 → 글자: kfont 로 역산
        allk = set(''.join(v for (s2, a), v in ko.items() if s2 == sc)) - set('/¶')
        for c in allk | {'　', '…', '。'}:
            rev.setdefault(kfont.glyph_bytes(c, jp), c)
        # 상자 따라 읽기
        binname = build_vs.BIN_OF.get(sc, sc)
        bb = open(os.path.join(OUT, '%s.BIN' % binname), 'rb').read()
        heads = sorted(a for (s2, a) in ko if s2 == sc)
        place_ok = 0
        eds_o = [i for i, t in enumerate(toks) if t == ('c', 'ED')]
        for a in heads:
            want = ko[(sc, a)]
            # 새 SCH 에서 이 상자 찾기: 원래 머리 자리를 가리키던 포인터 값(밀렸으면 고쳐진 값)
            ob_bin = open(os.path.join(DISC, '%s.BIN' % binname), 'rb').read()
            head = max(a + 1, T)
            while toks[head] == ('c', 'z'):
                head += 1
            ptrs = find_ptrs(ob_bin, head, T, Z)
            if not ptrs:
                continue   # 포인터 없이 이어 읽히는 상자(검산 생략)
            o = ptrs[0]
            pnew, = struct.unpack_from('>I', bb, o)
            idx = run_value(bb, pnew - build_vs.BASE)
            text = ''; i = idx; lines = []
            while True:
                en = nents[i]; po, = struct.unpack_from('>I', en, 0); t, w, h, dat = ndata[po]
                if dat in cm:
                    nm = cm[dat]
                    if nm == 'ED':
                        break
                    if nm == '○':
                        text += '/'
                    elif nm == 'CL':
                        text += '¶'
                elif (w, h) == (16, 16):
                    c = rev.get(dat)
                    if c is None:
                        bad.append('상자 %d: 모르는 글자 그림' % a); break
                    text += c
                i += 1
            norm = lambda x: x.replace(' ', '　').replace('/¶', '¶').replace('¶/', '¶').strip('/¶')
            if norm(text) != norm(want):
                bad.append('상자 %d 글 다름:\n   읽음 %s\n   번역 %s' % (a, text, want))
            else:
                place_ok += 1
        print('%-5s %s · 상자 읽기 일치 %d/%d' % (sc, '✅' if not bad else '⛔', place_ok, len(heads)))
        for x in bad[:10]:
            print('   ', x)
        nbad += len(bad)
    sys.exit(1 if nbad else 0)


def find_ptrs(binb, head, T, Z):
    for o in range(0, len(binb) - 4, 2):
        pass
    runs = []
    i = 0
    while i < len(binb) - 4:
        v, = struct.unpack_from('>H', binb, i); n = 1
        while i + 2 * n + 2 <= len(binb) and struct.unpack_from('>H', binb, i + 2 * n)[0] == v + n:
            n += 1
        if v <= T and v + n - 1 >= Z - 1 and n > 50:
            runs.append((i, v, n))
        i += 2 * n if n > 1 else 2
    ro, rv, rn = min(runs, key=lambda r: r[2])
    tgt = build_vs.BASE + ro + 2 * (head - rv)
    return [o for o in range(0, len(binb) - 4, 2) if struct.unpack_from('>I', binb, o)[0] == tgt]


def run_value(binb, off):
    v, = struct.unpack_from('>H', binb, off); return v


if __name__ == '__main__':
    main()
