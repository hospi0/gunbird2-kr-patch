# -*- coding: utf-8 -*-
"""건버드 2 대사 그림 STG?DEMOMSG.0xx 풀기(2026-10-30 조사)
  머리 32 B(u16 BE 0x0010 · u16 BE 데이터 u16 개수 ·0…) 뒤 16×16 칸이 이어짐, 칸 = 256 화소 × u16 LE ARGB4444
  칸 안 주소 비트: 표준 트위들(b0=x0 b1=Y0 … b7=Y3), Y = 15−y(위아래 뒤집힘) — 1스테이지 클리어 스샷 36칸 화소 대조로 확정(256 주소 전부 일치)
  칸 배치: 창(R줄×C칸)마다 열 단위, 열 안은 아래 줄부터(= 뒤집힌 그림의 위부터)
   — 매끄러움 점수로 비트 순열 40,320개를 전수 비교(전치 쌍 동점 중 글자가 바로 선 쪽)
  화면 배치는 아직 추정: 13칸 × 줄
  python tools/msgtile.py <파일…> → work/shot/msg/<이름>.png (4배)"""
import os, sys, struct
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def addr(x, y):
    y = 15 - y                          # 그림이 위아래 뒤집혀 저장(칸 순서도 아래 줄부터) — 스샷 대조로 확정
    return (x & 1) | (y & 1) << 1 | (x >> 1 & 1) << 2 | (y >> 1 & 1) << 3 | (x >> 2 & 1) << 4 | (y >> 2 & 1) << 5 | (x >> 3 & 1) << 6 | (y >> 3 & 1) << 7


def tiles(d):
    P = struct.unpack('<%dH' % ((len(d) - 32) // 2), d[32:32 + (len(d) - 32) // 2 * 2])
    return [P[i:i + 256] for i in range(0, len(P) - 255, 256)]


def load(nm):
    """이름 → 칸 목록. «파일@시작칸» 이면 그림 묶음(머리 32 B) 안 글자 구간(시작칸~끝) — END*.CHR·STG?.0xx 보스 대사"""
    f, _, a = nm.partition('@')
    d = open(os.path.join(ROOT, 'work', 'disc', f), 'rb').read()
    if len(d) % 512 == 0:                                 # 머리 없는 CHR(MENU·SYSTEM 등) — 칸이 0 B 부터
        d = bytes(32) + d
    T = tiles(d)
    return T[int(a):] if a else T


def render(d, cols=13):
    T = tiles(d); rows = (len(T) + cols - 1) // cols
    im = Image.new('RGB', (cols * 16, rows * 16), (20, 20, 40))
    for g, t in enumerate(T):
        for y in range(16):
            for x in range(16):
                v = t[addr(x, y)]
                if v: im.putpixel((g % cols * 16 + x, g // cols * 16 + y), tuple(((v >> s) & 15) * 17 for s in (8, 4, 0)))
    return im


if __name__ == '__main__':
    out = os.path.join(ROOT, 'work', 'shot', 'msg'); os.makedirs(out, exist_ok=True)
    for p in sys.argv[1:]:
        im = render(open(p, 'rb').read())
        im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(out, os.path.basename(p) + '.png'))
