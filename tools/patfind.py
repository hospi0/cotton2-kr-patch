# -*- coding: utf-8 -*-
r"""자체 문자 코드 찾기 — 화면에서 읽은 문장의 «같은 글자 반복 모양»(서로 같은 글자 = 같은 코드, 다른 글자 = 다른 코드)과
  일치하는 자리를 1바이트·2바이트(BE/LE) 단위로 찾는다. 코드값 자체는 몰라도 된다.
  python tools/patfind.py <문장> <파일 또는 폴더>…
"""
import os, sys


def pattern_hits(data, text, unit, endian='big'):
    n = len(text)
    first = {}
    pat = [first.setdefault(ch, i) for i, ch in enumerate(text)]
    # 단위 배열
    if unit == 1:
        arr = data
    else:
        m = len(data) // 2
        arr = [int.from_bytes(data[2 * i:2 * i + 2], endian) for i in range(m)]
    hits = []
    L = len(arr)
    for start in range(0, L - n + 1):
        ok = True; seen = {}
        for k in range(n):
            v = arr[start + k]
            j = pat[k]
            if j == k:
                if v in seen:          # 다른 글자인데 같은 값
                    ok = False; break
                seen[v] = k
            elif arr[start + j] != v:
                ok = False; break
        if ok:
            hits.append(start * unit)
    return hits


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    text = sys.argv[1]
    files = []
    for a in sys.argv[2:]:
        if os.path.isdir(a):
            files += [os.path.join(a, f) for f in sorted(os.listdir(a))]
        else:
            files.append(a)
    for f in files:
        data = open(f, 'rb').read()
        for unit, en in ((1, 'big'), (2, 'big'), (2, 'little')):
            if unit == 2:
                for odd in (0, 1):
                    h = pattern_hits(data[odd:], text, 2, en)
                    for x in h[:5]:
                        x += odd
                        print('%s 단위%d%s @%X  %s' % (os.path.basename(f), unit, en[0], x, data[x:x + 2 * len(text)].hex()))
            else:
                h = pattern_hits(data, text, 1)
                for x in h[:5]:
                    print('%s 단위1 @%X  %s' % (os.path.basename(f), x, data[x:x + len(text)].hex()))


if __name__ == '__main__':
    main()
