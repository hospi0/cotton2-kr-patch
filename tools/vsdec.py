# -*- coding: utf-8 -*-
r"""대화 장면 CHR_VS*.MF 의 SCH 를 «글자/명령» 스크립트로 풀기.
  명령 칸(34개)은 VS1 SPT 0‥33 그림 바이트로 판정. 글자(16×16)는 전 장면 공통 그림 번호 G### 로.
  python tools/vsdec.py  → work/text/vs_script.txt, work/text/glyphs.bin(고유 글자 그림 나열, 128B씩)
"""
import os, struct, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mf, vsscan, lz00
DISC = os.path.join(ROOT, 'work', 'disc')
SCENES = ['VS0', 'VS1', 'VS2', 'VS3', 'VS4', 'VS5', 'VS6', 'VS7', 'VS70']

LAB = {0: 'A', 1: 'CL', 2: 'C', 3: 'ED', 15: 'M', 16: 'N', 18: 'P', 19: '○', 20: 'S', 32: 'W', 17: 'n', 26: 's', 33: 'z'}
for i in range(4, 9): LAB[i] = 'd%d' % (i - 4)
for i, v in zip(range(9, 15), '_aiueo'): LAB[i] = v
for i in range(21, 26): LAB[i] = 'e%d' % (i - 21)
for i in range(27, 32): LAB[i] = 'w%d' % (i - 27)
MOUTH = set('_aiueo')


def load(scene):
    b = open(os.path.join(DISC, 'CHR_%s.MF' % scene), 'rb').read()
    e, offs, ents = vsscan.sch_table(b)
    d, sz = e['SPT']; s = b[d:d + sz]
    items, _ = mf.spt_items(s)
    return b, e, offs, ents, s, items


def ctrl_map():
    b, e, offs, ents, s, items = load('VS1')
    return {s[p + 0x20:p + 0x20 + z]: LAB[k] for k, p, t, w, h, z in items[:34]}


def decode():
    cm = ctrl_map(); glyphs = {}; out = {}
    for sc in SCENES:
        b, e, offs, ents, s, items = load(sc)
        byp = {}
        for k, p, t, w, h, z in items:
            data = s[p + 0x20:p + 0x20 + z]
            if data[:4] == b'LZ00':
                data = lz00.decompress(data)
            byp[p] = (k, w, h, data)
        toks = []
        for i, en in enumerate(ents):
            if len(en) < 4:
                toks.append(None); continue
            so, = struct.unpack_from('>I', en, 0)
            k, w, h, data = byp.get(so, (-1, 0, 0, b''))
            if data in cm:
                toks.append(('c', cm[data]))
            elif (w, h) == (16, 16):
                g = glyphs.setdefault(data, len(glyphs)); toks.append(('g', g))
            else:
                toks.append(('x', k))
        out[sc] = toks
    return out, glyphs


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out, glyphs = decode()
    with open(os.path.join(ROOT, 'work', 'text', 'vs_script.txt'), 'w', encoding='utf-8') as f:
        for sc, toks in out.items():
            f.write('#### %s\n' % sc); line = []
            for i, t in enumerate(toks):
                if t is None: continue
                s = '<%s>' % t[1] if t[0] == 'c' and t[1] not in MOUTH else (t[1] if t[0] == 'c' else ('[G%d]' % t[1] if t[0] == 'g' else '{%d}' % t[1]))
                if t == ('c', 'ED'): f.write('%d:%s\n' % (i, ''.join(line))); line = []
                line.append(s)
            f.write('%d:%s\n' % (i, ''.join(line)))
    open(os.path.join(ROOT, 'work', 'text', 'glyphs.bin'), 'wb').write(b''.join(sorted(glyphs, key=glyphs.get)))
    print('고유 글자', len(glyphs))
