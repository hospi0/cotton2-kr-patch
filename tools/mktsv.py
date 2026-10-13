# -*- coding: utf-8 -*-
r"""번역 TSV 만들기: work/text/vs_ja.txt → work/text/vs_ja.tsv
  원문 표기: / = 줄바꿈(○) · ¶ = 쪽 넘김(<CL>). VS70 은 VS7 과 같은 대사 → 같은 id 공유(자리 칸에 둘 다).
  화자: A アプリ · C コットン · N ニードル · S シルク · W 내레이션/마녀 · M 대신? · P 왕?
"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {'A': 'アプリ', 'C': 'コットン', 'N': 'ニードル', 'S': 'シルク', 'W': 'W', 'M': 'M', 'P': 'P'}
rows = {}; order = []
for l in open(os.path.join(ROOT, 'work', 'text', 'vs_ja.txt'), encoding='utf-8').read().splitlines():
    sc, a, b, t = l.split('\t')
    t = re.sub(r'^.*<z>', '', t)
    if not re.search(r'[\u3040-\u9fff]', t):
        continue
    m = re.match(r'<([ACNSWMP])>', t); sp = SP[m.group(1)] if m else ''
    ja = t.replace('<CL>', '¶')
    ja = re.sub(r'<[^>]*>', '', ja)
    ja = re.sub(r'/*¶/*', '¶', ja); ja = re.sub(r'/+', '/', ja).strip('/')
    key = (sp, ja)
    if key in rows:
        rows[key][1].append('%s:%s' % (sc, a))
    else:
        rows[key] = [sc, ['%s:%s' % (sc, a)]]; order.append(key)
with open(os.path.join(ROOT, 'work', 'text', 'vs_ja.tsv'), 'w', encoding='utf-8') as f:
    f.write('id\t자리\t화자\t원문\t번역\n')
    for i, k in enumerate(order):
        f.write('%03d\t%s\t%s\t%s\t\n' % (i, ','.join(rows[k][1]), k[0], k[1]))
print(len(order), '상자 ·', sum(len(k[1].replace('/', '').replace('¶', '')) for k in order), '자')
