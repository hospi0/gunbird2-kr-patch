# -*- coding: utf-8 -*-
"""대사 그림 띠 나누기(2026-10-30) — 파일 = 줄 수(R) 가 같은 «띠» 몇 개. 띠 안은 화자별 창이 빈틈없이 가로로 이어 붙음
   (창 폭 = 그 창 가장 긴 줄, 예: STG1DEMOMSG.004 = 2줄 띠 38칸 = 13+12+13).
   띠 경계는 줄 수가 바뀌는 곳 — 줄 머리 빈칸·문장 안 끊김 벌점이 가장 작은 나누기(동적 계획).
   python tools/msgseg.py → work/msg_strips.json {파일: [[R, C], …]}"""
import os, sys, json, glob
from functools import lru_cache
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile


def seg(T):
    blank = [not any(t) for t in T]; n = len(T)

    def cost(s, R, C):                                    # 창(≤15칸) 단위 벌점 — 끝나면 같은 R 창끼리 합쳐 띠로
        c = 6
        for r in range(R):
            row = [blank[s + k * R + (R - 1 - r)] for k in range(C)]
            if all(row): continue                             # 통째 빈 줄(아랫줄만 쓰는 창)
            if row[0]: c += 3                                 # 줄 머리 빈칸
            seen = False
            for b in row:
                if b: seen = True
                elif seen: c += 1; seen = False
        if all(blank[s + (C - 1) * R + i] for i in range(R)): c += 2
        return c

    @lru_cache(None)
    def best(s):
        if s == n: return (0, ())
        res = (10 ** 9, ())
        for R in (1, 2, 3):
            for C in range(1, min(15, (n - s) // R) + 1):
                b = best(s + R * C)
                if b[0] >= 10 ** 9: continue
                v = cost(s, R, C) + b[0]
                if v < res[0]: res = (v, ((R, C),) + b[1])
        return res
    return best(0)


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    js = os.path.join(ROOT, 'work', 'msg_strips.json')
    out = json.load(open(js)) if os.path.exists(js) else {}
    names = sys.argv[1:] or [os.path.basename(q) for q in sorted(glob.glob(os.path.join(ROOT, 'work', 'disc', 'STG*DEMOMSG.*')))]
    for nm in names:                                       # 인자 = «파일@시작칸» 글자 구간도 됨(msgtile.load)
        T = msgtile.load(nm); m = []
        for R, C in seg(T)[1]:
            if m and m[-1][0] == R: m[-1][1] += C
            else: m.append([R, C])
        out[nm] = m
    json.dump(out, open(js, 'w'), indent=0)
    import collections
    print(len(out), collections.Counter(len(v) for v in out.values()), collections.Counter(r for v in out.values() for r, c in v))
