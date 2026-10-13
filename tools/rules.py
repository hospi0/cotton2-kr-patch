# -*- coding: utf-8 -*-
r"""코튼2 번역 규칙 — 되채움기(fill.py)와 빌더가 같이 쓴다. 쓰는 순간 막는다.
  칸: 글자 하나 = 16×16 그림 한 칸(한글·부호·공백 모두 1칸, 13px 간격).
  예산: «장면 × 화자» 상자별 원문 최대 줄 칸 수(W)·쪽당 줄 수(H). / = 줄바꿈 · ¶ = 쪽 넘김.
  막음: 줄 칸 초과 · 쪽당 줄 수 초과 · 「」 개수 다름 · 반각 문자/제어용 < > { } [ ] 혼입 · 이름 표기 위반.
  고침(자동): 문장부호 뒤 공백 1칸 지움(squeeze).
"""
import re

BANNER = r"""
==== 코튼2 번역 규칙 ====
 1) 한 줄 칸 수 ≤ 상자 폭(장면×화자 원문 최대) · 쪽당 줄 수 ≤ 원문 최대 — 넘치면 ¶ 로 쪽을 늘린다(내용 깎지 말 것)
 2) 줄바꿈은 공백·문장부호 뒤에서만 (낱말 한복판 금지)
 3) 문장부호 뒤 공백은 자동으로 지운다
 4) 원문 「」 는 그대로 「」
 5) 이름: 코튼 · 아프리 · 니들 · 실크 · 물의윌로(水ウィロー) · 윌로 · 펌프킨 왕국 · 필라멘트 · 모킨 산맥
=========================
"""

PUNCT = ',.!?:;)]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥‼⁉'
NAME_BAD = {
    '코톤': '코튼', '콧톤': '코튼', '고튼': '코튼', '아푸리': '아프리', '아플리': '아프리', '니도루': '니들', '니드루': '니들',
    '시루쿠': '실크', '보위로': '물의윌로', '보우이로': '물의윌로', '보윌로': '물의윌로', '수윌로': '물의윌로', '판푸킨': '펌프킨', '팜킨': '펌프킨',
    '휘라멘트': '필라멘트', '못킨': '모킨',
}


def squeeze(t):
    return re.sub('([' + re.escape(PUNCT) + '])[ 　](?![ 　])', r'\1', t)


def budget(rows):
    """rows: [(id, 자리, 화자, 원문)] → {(장면, 화자): (W, H)}"""
    W = {}; H = {}
    for i, pos, sp, ja in rows:
        k = (pos.split(':')[0], sp)
        for p in ja.split('¶'):
            ls = p.split('/')
            W[k] = max(W.get(k, 0), max(map(len, ls))); H[k] = max(H.get(k, 0), len(ls))
    return {k: (W[k], H[k]) for k in W}


def validate(ja, ko, w, h):
    """→ (막을 것 목록, 경고 목록)"""
    bad = []; warn = []
    if not ko:
        return ['빈 번역'], []
    if '\n' in ko or '\t' in ko:
        bad.append('실개행/탭')
    if re.search(r'[<>{}\[\]\\]', ko):
        bad.append('제어용 기호 < > { } [ ] \\')
    if re.search(r'[A-Za-z0-9]', ko):
        warn.append('반각 영숫자 — 글꼴 그림으로 그려야 함')
    for p in ko.split('¶'):
        ls = p.split('/')
        if len(ls) > h:
            bad.append('쪽당 %d줄 > %d' % (len(ls), h))
        for x in ls:
            if len(x) > w:
                bad.append('줄 %d칸 > %d: %s' % (len(x), w, x))
            if x.startswith(' ') or x.endswith(' '):
                warn.append('줄 앞뒤 공백: «%s»' % x)
    for a, b in ('「」', '『』'):
        if ja.count(a) != ko.count(a) or ja.count(b) != ko.count(b):
            bad.append('%s%s 개수 다름' % (a, b))
    for k, v in NAME_BAD.items():
        if k in ko:
            bad.append('이름 «%s» → «%s»' % (k, v))
    return bad, warn
