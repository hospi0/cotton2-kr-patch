# -*- coding: utf-8 -*-
r"""초기 조사 — 디스크 전 파일을 work/disc/ 로 꺼내고, 파일별 SJIS 평문(가나 포함 4자 이상) 분량을 센다.
  python tools/scan.py  → work/scan.txt
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import disc

SJ = re.compile(rb'(?:[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]|[\x20-\x7e]){4,}')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = disc.Disc(disc.ROM)
    out = []
    for p, l, s in sorted(d.walk(), key=lambda x: x[1]):
        b = d.read(l, s)
        dst = os.path.join(disc.OUT, p); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(b)
        n = c = 0; ex = []
        for m in SJ.finditer(b):
            try:
                t = m.group(0).decode('cp932')
            except UnicodeDecodeError:
                continue
            if len(re.findall('[ぁ-んァ-ヶ]', t)) < 2:
                continue
            n += 1; c += len(t)
            if len(ex) < 3:
                ex.append(t[:40])
        if n:
            out.append((c, n, p, s, ex))
    out.sort(reverse=True)
    lines = ['%7d자 %5d개 %-16s %9d %s' % (c, n, p, s, ' | '.join(ex)) for c, n, p, s, ex in out]
    open(os.path.join(ROOT, 'work', 'scan.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:40]))
    print('합계 %d자' % sum(x[0] for x in out))


if __name__ == '__main__':
    main()
