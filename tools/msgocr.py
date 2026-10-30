# -*- coding: utf-8 -*-
"""칸 → 글자 사전(받아쓴 대사 그림에서) + 사전으로 읽어 띠 나누기 자동 선택 (2026-10-30)
  사전: work/text/jp_strips.tsv 의 띠마다 칸 바이트(512 B) → 그 자리 글자. 같은 글꼴·같은 색이라 같은 글자는 같은 바이트.
  읽기: 모르는 칸 = ？(전각 물음표와 구별해 '〓'), 빈 칸 =
  나누기: 띠(R 1~3, 이웃 띠 R 다름)마다 줄을 읽어 «받아쓴 말뭉치에 있는 두 글자 이음» 수로 점수 — 동적 계획
  python tools/msgocr.py 이름…   (이름 = 파일 또는 «파일@시작칸») → 표준 출력 + work/msg_strips.json 갱신(--save)"""
import os, sys, json, collections
from functools import lru_cache
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgpat, jpcheck, msgsheet

UNK = '〓'


def build():
    lay = msgsheet.layout(); dic = {}; corpus = []
    for r in jpcheck.load():
        nm, k = r['file'], int(r['strip'])
        T = msgtile.load(nm); s = sum(R * C for R, C in lay[nm][:k]); R, C = lay[nm][k]
        rows = [t + '　' * (C - len(t)) for t in r['rows'].split('／')]
        for c in range(C):
            for rr in range(R):
                ch = rows[rr][c]
                if ch != '　': dic[bytes(struct_tile(T[s + c * R + (R - 1 - rr)]))] = ch
        corpus += rows
    big = collections.Counter()
    for t in corpus:
        for a, b in zip(t, t[1:]):
            if a != '　' and b != '　': big[a + b] += 1
    return dic, big


def struct_tile(t):
    import struct
    return struct.pack('<256H', *t)


def read(T, dic):
    return ['　' if not any(t) else dic.get(struct_tile(t), UNK) for t in T]


def strip_rows(chars, s, R, C):
    return [''.join(chars[s + c * R + (R - 1 - r)] for c in range(C)) for r in range(R)]


def score_rows(rows, big):
    v = 0
    for t in rows:
        for a, b in zip(t, t[1:]):
            if a in '　' + UNK or b in '　' + UNK: continue
            v += 1 if big.get(a + b) else 0           # 말뭉치가 작아 «없는 이음»은 벌점 없음
    return v


def segment(chars, big):
    n = len(chars)

    @lru_cache(None)
    def best(s, prevR):
        if s == n: return (0, ())
        res = (-10 ** 9, ())
        for R in (1, 2, 3, 4, 5, 6):                       # 7스테이지 선택지 = 5줄 창(빈 줄 끼움)
            if R == prevR: continue
            for C in range(2, (n - s) // R + 1):
                b = best(s + R * C, R)
                if b[0] <= -10 ** 9: continue
                v = score_rows(strip_rows(chars, s, R, C), big) - 3 + b[0]
                if v > res[0]: res = (v, ((R, C),) + b[1])
        return res
    sys.setrecursionlimit(100000)
    return best(0, 0)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    dic, big = build()
    names = [a for a in sys.argv[1:] if not a.startswith('--')]
    js = os.path.join(ROOT, 'work', 'msg_strips.json'); allj = json.load(open(js))
    print('사전 칸', len(dic), '이음', len(big))
    for nm in names:
        T = msgtile.load(nm); ch = read(T, dic)
        if '--skip' in sys.argv:                          # 글자 구간 시작이 어긋났을 때: 앞 칸 k 개 건너뛴 경우 중 최고점
            best_k = max(range(0, 80), key=lambda k: segment(ch[k:], big)[0] + 0.0)
            print('   앞', best_k, '칸 건너뜀')
            f, _, a = nm.partition('@'); nm = '%s@%d' % (f, int(a or 0) + best_k); T = msgtile.load(nm); ch = read(T, dic)
        known = sum(1 for c in ch if c not in '　' + UNK); tot = sum(1 for c in ch if c != '　')
        spec = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--lay=')]
        if spec:                                          # 손으로 준 나누기(마지막 띠는 남은 칸 전부, C=0 이면 자동)
            lay = []; left = len(T)
            for b in spec[0].split(','):
                if b == '*':                              # 나머지는 자동
                    lay += list(segment(ch[len(T) - left:], big)[1]); left = 0; break
                R, C = (int(v) for v in b.split('x')); C = C or left // R; lay.append((R, C)); left -= R * C
            assert left == 0, ('칸 남음', left)
            sc = sum(score_rows(strip_rows(ch, sum(r * c for r, c in lay[:i]), R, C), big) for i, (R, C) in enumerate(lay))
        else:
            sc, lay = segment(ch, big)
        print('==', nm, '칸', len(T), '아는 글자 %d/%d' % (known, tot), '점수', sc, lay)
        s = 0
        for R, C in lay:
            for t in strip_rows(ch, s, R, C): print('   ', t.rstrip('　'))
            print('   --'); s += R * C
        if '--save' in sys.argv: allj[nm] = [list(x) for x in lay]
    if '--save' in sys.argv: json.dump(allj, open(js, 'w'), indent=0)


if __name__ == '__main__':
    main()
