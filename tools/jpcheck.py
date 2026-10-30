# -*- coding: utf-8 -*-
"""원문 받아쓰기(work/text/jp_strips.tsv) 검산 — 띠마다 줄 수·칸 수가 그림과 같고, 「　」 자리 = 빈 칸, 그 밖 = 글자 칸인지.
   줄 끝 빈칸은 적지 않아도 됨(채워서 비교). 창 나누기(cuts)는 창 폭 = 가장 긴 줄 규칙: 창마다 어느 줄은 마지막 칸까지 글자여야(경계 바로 앞 칸 비면 경고).
   python tools/jpcheck.py"""
import os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgpat


def load():
    return list(csv.DictReader(open(os.path.join(ROOT, 'work', 'text', 'jp_strips.tsv'), encoding='utf-8'), delimiter='\t'))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    bad = 0; pats = {}
    for r in load():
        nm, k = r['file'], int(r['strip'])
        if nm not in pats: pats[nm] = msgpat.pattern(nm)
        R, C, prow = pats[nm][k]
        rows = [t + '　' * (C - len(t)) if len(t) < C else t for t in r['rows'].split('／')]   # 줄 끝 빈칸은 생략 가능
        err = []
        if len(rows) != R: err.append('줄 수 %d≠%d' % (len(rows), R))
        if nm.startswith('END6'):                         # 모리간 엔딩 = 좁은 글꼴(칸≠글자) → 줄 수만
            if err: bad += 1; print(nm, k, *err)
            continue
        for i, (t, p) in enumerate(zip(rows, prow)):
            if len(t) != C: err.append('%d줄 길이 %d≠%d' % (i + 1, len(t), C)); continue
            q = ''.join('.' if ch == '　' else 'X' for ch in t)
            if q != p: err.append('%d줄 모양\n     그림 %s\n     받아 %s' % (i + 1, p, q))
        cuts = [int(x) for x in r['cuts'].split(',') if x]      # 띠 끝 빈 열은 허용(마지막 창 뒤)
        a = 0
        for b in cuts:
            if not any(len(t) == C and t[b - 1] != '　' for t in rows): err.append('창 %d~%d 마지막 칸이 모두 빔' % (a, b - 1))
            a = b
        if err: bad += 1; print(nm, k, *err, sep='\n  ')
    print('검사', len(load()), '띠, 오류', bad)


if __name__ == '__main__':
    main()
