# -*- coding: utf-8 -*-
"""RESOURCE.BIN 스프라이트 정의 표 → 글자 창 경계 (2026-10-30 확인)
  기록 12 B: [?][칸 lo][칸 hi][x:u16=0][y][07][00][?][00][?][02|82] — 칸 번호 = VRAM 전역(대사 0x1000+, 보스 0x1100+, 엔딩 0+)
  글자 창 기록은 x=0·y=a0~f0 이고 12 B 간격으로 이어진 묶음 = 한 장면의 창 목록(시작 칸 순서).
  검증: STG1 대사 002=0·24, 003=0·20, 004=0·26·50 — 판독으로 정한 창 경계와 같음.
  창 칸 수 = 다음 시작 − 이 시작(마지막은 파일 끝). 줄 수 R 은 칸 수의 약수 중 글자 사전(tools/msgocr)으로 가장 잘 읽히는 것.
  python tools/restab.py 파일@시작 […]  → 창별 R×C 와 읽은 글 (시작 = 색으로 찾은 글자 구간 시작, work/end_regions.txt)
  python tools/restab.py --save 파일…  → work/msg_strips_fix.json 에 «파일@첫창» 띠 목록 저장"""
import os, sys, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgocr


def runs():
    d = open(os.path.join(ROOT, 'work', 'disc', 'RESOURCE.BIN'), 'rb').read()
    recs = []
    for m in re.finditer(rb'(?=(...\x00\x00[\xa0-\xf0]\x07\x00.\x00[\x00-\x05][\x02\x82]))', d, re.S):
        a = m.start(); recs.append((a, d[a + 1] + d[a + 2] * 256))
    out = []; cur = [recs[0]]
    for r in recs[1:]:
        if r[0] - cur[-1][0] == 12: cur.append(r)
        else: out.append(cur); cur = [r]
    out.append(cur)
    return [[t for _, t in r] for r in out]


def cands_for(ntiles, start, base=0):
    out = []
    for r in runs():
        rel = [t - base for t in r]
        if not all(0 <= t < ntiles for t in rel): continue
        if min(abs(t - start) for t in rel) > 8: continue
        out.append([t for t in rel if t >= start - 8])
    return out


def layout_of(ch, big, starts, n):
    lay = []; tot = 0
    for a, e in zip(starts, starts[1:] + [n]):
        cnt = e - a
        cands = [(R, cnt // R) for R in (1, 2, 3, 4, 5, 6) if cnt % R == 0 and cnt // R <= 30] or [(1, cnt)]
        sc = lambda rc: msgocr.score_rows(msgocr.strip_rows(ch, a, rc[0], rc[1]), big) + (0.1 if rc[0] in (2, 3) else 0)
        R, C = max(cands, key=sc); lay.append((a, R, C)); tot += sc((R, C))
    return tot, lay


def boxes_for(fname, ntiles, start, base=0):
    """글자 구간 시작 칸(start, 색 판정)에 가장 가까운 칸(±8)을 품은 묶음 — 같은 칸 번호가 다른 엔딩 표에도 있어
       «가장 가까움 → 마지막 창이 파일 끝에 가장 가까움» 순으로 고르고 start−8 이상인 시작 칸들"""
    best = None
    for r in runs():
        rel = [t - base for t in r]
        if not all(0 <= t < ntiles for t in rel): continue
        dd = min(abs(t - start) for t in rel)
        if dd > 8: continue
        key = (dd, ntiles - max(rel))
        if best is None or key < best[0]: best = (key, [t for t in rel if t >= start - 8])
    return best[1] if best else None


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    dic, big = msgocr.build()
    save = '--save' in sys.argv
    fx = os.path.join(ROOT, 'work', 'msg_strips_fix.json'); fixj = json.load(open(fx))
    for arg in [a for a in sys.argv[1:] if not a.startswith('--')]:   # 인자 = «파일@글자구간시작»
        f, _, st = arg.partition('@')
        T = msgtile.load(f); n = len(T)
        ch = msgocr.read(T, dic)
        cs = cands_for(n, int(st))                         # 같은 칸 번호 표가 여러 엔딩에 있음 → 사전으로 가장 잘 읽히는 표
        if not cs: print('==', f, '표 없음'); continue
        starts = max(cs, key=lambda c: layout_of(ch, big, c, n)[0])
        print('==', f, '칸', n, '창 시작', starts)
        lay = []
        ends = starts[1:] + [n]
        for a, e in zip(starts, ends):
            cnt = e - a
            cands = [(R, cnt // R) for R in (1, 2, 3, 4, 5, 6) if cnt % R == 0 and cnt // R <= 30]
            if not cands: cands = [(1, cnt)]
            sc = lambda rc: msgocr.score_rows(msgocr.strip_rows(ch, a, rc[0], rc[1]), big) + (0.1 if rc[0] in (2, 3) else 0)
            R, C = max(cands, key=sc)
            rows = msgocr.strip_rows(ch, a, R, C)
            print('  @%d %dx%d' % (a, R, C), ' / '.join(t.rstrip('　') for t in rows))
            lay.append([R, C])
        if save:
            fixj['%s@%d' % (f, starts[0])] = lay
    if save: json.dump(fixj, open(fx, 'w'), indent=0)


if __name__ == '__main__':
    main()
