# -*- coding: utf-8 -*-
"""창 하나(표의 마지막 창 등)를 글자 사전으로 1~3 조각 나누기 후보 — python tools/boxsplit.py 이름 창번호 [개수]
   (이름 = work/msg_strips_fix.json 의 키, 예 END02.CHR@1405)"""
import os, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import msgocr, msgtile, msgsheet


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    nm, k = sys.argv[1], int(sys.argv[2]); top = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    dic, big = msgocr.build(); lay = msgsheet.layout()[nm]
    ch = msgocr.read(msgtile.load(nm), dic)
    s = sum(R * C for R, C in lay[:k]); n = lay[k][0] * lay[k][1]
    res = []

    def gen(left, prev, depth):
        if left == 0: yield []; return
        if depth == 0: return
        for R in (1, 2, 3, 4, 5):
            if R == prev: continue
            for C in range(1, left // R + 1):
                for rest in gen(left - R * C, R, depth - 1): yield [(R, C)] + rest
    for l in gen(n, 0, 3):
        a = s; sc = -len(l) * 2
        for R, C in l: sc += msgocr.score_rows(msgocr.strip_rows(ch, a, R, C), big); a += R * C
        res.append((sc, l))
    res.sort(key=lambda x: -x[0])
    for sc, l in res[:top]:
        print(sc, l); a = s
        for R, C in l:
            print('    ' + ' / '.join(msgocr.strip_rows(ch, a, R, C))); a += R * C


if __name__ == '__main__':
    main()
