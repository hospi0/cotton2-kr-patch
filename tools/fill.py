# -*- coding: utf-8 -*-
r"""번역 되채움: work/text/vs_ko.tsv(id \t 번역) → 규칙 검사(rules.validate) 통과분만 work/text/vs_ja.tsv 번역 칸에 씀.
  python tools/fill.py   — 막힌 줄은 안 써지고 목록을 찍는다(종료 코드 1).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import rules

JA = os.path.join(ROOT, 'work', 'text', 'vs_ja.tsv')
KO = os.path.join(ROOT, 'work', 'text', 'vs_ko.tsv')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print(rules.BANNER)
    lines = open(JA, encoding='utf-8').read().splitlines()
    head, body = lines[0], [l.split('\t') for l in lines[1:]]
    B = rules.budget([(r[0], r[1], r[2], r[3]) for r in body])
    ko = {}
    for n, l in enumerate(open(KO, encoding='utf-8').read().splitlines(), 1):
        if not l.strip() or l.startswith('#'):
            continue
        i, _, t = l.partition('\t')
        if not (len(i) == 3 and i.isdigit()):
            sys.exit('vs_ko.tsv %d줄: id 로 시작 안 함 → %r' % (n, l[:30]))
        ko[i] = rules.squeeze(t.strip())
    nbad = 0; nok = 0
    for r in body:
        i, pos, sp, ja = r[:4]
        if i not in ko:
            continue
        w, h = B[(pos.split(':')[0], sp)]
        bad, warn = rules.validate(ja, ko[i], w, h)
        for x in warn:
            print('  경고', i, x)
        if bad:
            nbad += 1
            print('⛔', i, '(폭%d·%d줄)' % (w, h), '; '.join(bad))
            continue
        while len(r) < 5:
            r.append('')
        r[4] = ko[i]; nok += 1
    open(JA, 'w', encoding='utf-8').write(head + '\n' + '\n'.join('\t'.join(r[:5]) for r in body) + '\n')
    left = sum(1 for r in body if len(r) < 5 or not r[4])
    print('씀 %d · 막힘 %d · 남은 미번역 %d / %d' % (nok, nbad, left, len(body)))
    sys.exit(1 if nbad else 0)


if __name__ == '__main__':
    main()
