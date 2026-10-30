# -*- coding: utf-8 -*-
"""띠별 빈칸 모양 출력(판독 보조) — X=글자 칸 .=빈칸. python tools/msgpat.py STG1 → 표준 출력"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgsheet


def pattern(nm):
    T = msgtile.load(nm); s = 0; out = []
    for R, C in msgsheet.layout()[nm]:
        rows = [''.join('.' if not any(T[s + k * R + (R - 1 - r)]) else 'X' for k in range(C)) for r in range(R)]
        out.append((R, C, rows)); s += R * C
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for nm in sorted(n for n in msgsheet.layout() if n.startswith(sys.argv[1] + 'DEMOMSG')):
        for i, (R, C, rows) in enumerate(pattern(nm)):
            print('%s #%d %dx%d' % (nm[-3:], i, R, C)); [print('   ' + r) for r in rows]
