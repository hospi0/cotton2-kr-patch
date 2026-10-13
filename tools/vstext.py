# -*- coding: utf-8 -*-
r"""대화 장면 원문 풀기: vsdec 토큰 + work/text/glyph_chars.tsv(그림 번호 → 글자, 빈 칸 = 전각 공백).
  python tools/vstext.py [--raw]  → work/text/vs_ja.txt (상자 한 줄, / = 줄바꿈 <화자>; --raw 는 입 모양·대기까지)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vsdec


def chars():
    m = {}
    for l in open(os.path.join(ROOT, 'work', 'text', 'glyph_chars.tsv'), encoding='utf-8').read().splitlines():
        a, _, b = l.partition('\t'); m[int(a)] = b or '\u3000'
    return m


def boxes(raw=False):
    out, glyphs = vsdec.decode(); ch = chars(); res = []
    for sc, toks in out.items():
        zs = [i for i, t in enumerate(toks) if t == ('c', 'z')]; end = zs[-1] if zs else len(toks)
        line = ''; start = 0
        for i, t in enumerate(toks[:end]):
            if t is None: continue
            if t[0] == 'g': line += ch.get(t[1], '[G%d]' % t[1])
            elif t[0] == 'c':
                v = t[1]
                if v == 'ED':
                    res.append((sc, start, i, line)); line = ''; start = i; continue
                if v in vsdec.MOUTH: line += v if raw else ''
                elif v == '○': line += '/'
                elif v[0] == 'w': line += ('<%s>' % v) if raw else ''
                else: line += '<%s>' % v
            else: line += '{%d}' % t[1]
        res.append((sc, start, end, line))
    return res


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raw = '--raw' in sys.argv
    with open(os.path.join(ROOT, 'work', 'text', 'vs_ja%s.txt' % ('_raw' if raw else '')), 'w', encoding='utf-8') as f:
        for sc, a, b, line in boxes(raw):
            f.write('%s\t%d\t%d\t%s\n' % (sc, a, b, line))
