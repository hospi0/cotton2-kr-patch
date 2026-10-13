# -*- coding: utf-8 -*-
r"""한글 상자 → SCH 토큰 조립(원문 상자의 명령 배치를 규칙으로 옮김).
  원문 상자 = [화자 명령 … ED]. <CL> 로 쪽을 나누고, 쪽마다
    머리(첫 글자 앞 명령) · 첫 글자 뒤 명령(<e#> <n> 등) · 꼬리(마지막 글자 뒤 대기·○·<s><n><d1>) 를 따로 떼어 둔다.
  한글 쪽 k 는 원문 쪽 min(k, 끝) 의 머리·첫 뒤를, 꼬리는 «한글 마지막 쪽 = 원문 마지막 쪽 꼬리», 그 밖 쪽 = 원문 같은 번호 쪽 꼬리
  (원문보다 쪽이 많으면 중간 쪽 꼬리는 <w4>).
  줄바꿈 / = ○ (원문 상자가 <d0> 를 쓰면 셋째 줄부터 ○ 뒤 <d0>). 글자 뒤 입 모양 = 모음(ㅏ a · ㅣ i · ㅜㅡ u · ㅐㅔ e · ㅗㅓ o),
  부호 뒤 '_'(원문 상자에 입 모양이 없으면 안 붙임), 쉼표 뒤 <w2>, 쪽 안 문장 끝 부호 뒤 <w3>. 원문 쪽 가운데 <s> 는 한글 쪽 마지막 글자 앞에.
  토큰 꼴: ('c', 명령이름) · ('k', 한글 글자)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vsdec

MOUTH = vsdec.MOUTH
COMMA = set(',、')
STOP = set('.。！？‼⁉…')
NOMOUTH = set(' 　〜ー「」（）')
V = {}
for i, j in enumerate('ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'):
    V[i] = {'ㅏ': 'a', 'ㅑ': 'a', 'ㅘ': 'a', 'ㅐ': 'e', 'ㅒ': 'e', 'ㅔ': 'e', 'ㅖ': 'e', 'ㅙ': 'e', 'ㅚ': 'e', 'ㅞ': 'e',
            'ㅓ': 'o', 'ㅕ': 'o', 'ㅗ': 'o', 'ㅛ': 'o', 'ㅝ': 'o', 'ㅜ': 'u', 'ㅠ': 'u', 'ㅡ': 'u', 'ㅟ': 'i', 'ㅢ': 'i', 'ㅣ': 'i'}[j]


def mouth(ch):
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3:
        return V[(o - 0xAC00) // 28 % 21]
    if ch in NOMOUTH:
        return None
    return '_'


def split_pages(toks):
    """원문 상자 토큰(머리 화자 명령 다음부터 ED 앞까지) → 쪽 목록 [토큰…], 쪽 구분 = CL"""
    pages = [[]]
    for t in toks:
        if t == ('c', 'CL'):
            pages.append([])
        else:
            pages[-1].append(t)
    return pages


def page_parts(p):
    gi = [i for i, t in enumerate(p) if t[0] == 'g']
    if not gi:
        return p, [], [], False, False
    f, l = gi[0], gi[-1]
    head = p[:f]
    j = f + 1
    while j < len(p) and p[j][0] == 'c' and p[j][1] in MOUTH:
        j += 1
    after = []
    while j < len(p) and p[j][0] == 'c' and p[j][1] not in MOUTH and p[j][1] != '○' and not p[j][1].startswith('w'):
        after.append(p[j]); j += 1
    k = l + 1
    while k < len(p) and p[k][0] == 'c' and p[k][1] in MOUTH:
        k += 1
    tail = p[k:]
    mid_s = any(t == ('c', 's') for t in p[j:l])
    uses_d0 = any(t == ('c', 'd0') for t in p)
    return head, after, tail, mid_s, uses_d0


def assemble(orig, ko):
    """orig: 원문 상자 토큰(화자 명령 … ED 포함), ko: 번역(/ ¶) → 토큰 목록"""
    assert orig[-1] == ('c', 'ED'), orig[-1]
    spk = orig[0]; body = orig[1:-1]
    opages = [page_parts(p) for p in split_pages(body)]
    d0 = any(x[4] for x in opages)
    has_mouth = any(t[0] == 'c' and t[1] in MOUTH for t in body)
    kpages = ko.split('¶')
    out = [spk]
    for k, kp in enumerate(kpages):
        o = opages[min(k, len(opages) - 1)]
        head, after, _, mid_s, _ = o
        if k == len(kpages) - 1:
            tail = opages[-1][2]
        elif k < len(opages) - 1 or k < len(opages):
            tail = opages[k][2] if k < len(opages) - 1 else [('c', 'w4')]
        if k > 0:
            out.append(('c', 'CL'))
        out += head
        chars = [(li, c) for li, line in enumerate(kp.split('/')) for c in line]
        glyph_idx = [n for n, (li, c) in enumerate(chars)]
        last = len(chars) - 1
        first = True; prev_li = 0
        for n, (li, c) in enumerate(chars):
            if li != prev_li:
                out.append(('c', '○'))
                if d0 and li >= 2:
                    out.append(('c', 'd0'))
                prev_li = li
            if mid_s and n == last and last > 0:
                out.append(('c', 's'))
            out.append(('k', c))
            m = mouth(c) if has_mouth else None
            if m:
                out.append(('c', m))
            if first and c not in ' 　':
                out += after; first = False
            if n < last:
                nxt = chars[n + 1][1]
                if c in COMMA:
                    out.append(('c', 'w2'))
                elif c in STOP and nxt not in STOP:
                    out.append(('c', 'w3'))
        if not chars:
            pass
        out += tail
    out.append(('c', 'ED'))
    return out
