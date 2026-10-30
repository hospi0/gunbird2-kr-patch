# -*- coding: utf-8 -*-
"""띠 나누기 후보 자동 나열 — 띠 1~3개(이웃 띠 줄 수 다름, R 1~3, 띠 폭 ≥3) 전부를 벌점순으로 그려 봄 → work/shot/cand.png
   벌점: 줄 머리 빈칸(내용 있는 줄) · 띠 첫 열 통째 빈칸.  python tools/msgcand.py STG6DEMOMSG.003 [개수]"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgsheet
nm = sys.argv[1]; top = int(sys.argv[2]) if len(sys.argv) > 2 else 10
T = msgtile.load(nm); n = len(T)
blank = [not any(t) for t in T]


def cost(lay):
    s = 0; c = 0
    for R, C in lay:
        for r in range(R):
            row = [blank[s + k * R + (R - 1 - r)] for k in range(C)]
            if all(row): continue
            if row[0]: c += 2
            gaps = sum(1 for a, b in zip(row, row[1:]) if a and not b)
            c += gaps * 0.5
        if all(blank[s + i] for i in range(R)): c += 3
        s += R * C
    return c + len(lay) * 1.5


def gen(left, prevR, depth=3):
    if left == 0: yield []; return
    if depth == 0: return
    for R in (1, 2, 3):
        if R == prevR: continue
        for C in range(3, left // R + 1):
            for rest in gen(left - R * C, R, depth - 1):
                yield [(R, C)] + rest


cands = sorted({tuple(l) for l in gen(n, 0)}, key=cost)[:top]
rows = []
for lay in cands:
    s = 0; ims = []
    for R, C in lay: ims.append(msgsheet.box_img(T, s, R, C)); s += R * C
    W = sum(i.width + 8 for i in ims); H = max(i.height for i in ims)
    im = Image.new('L', (W + 120, H + 4), 40); x = 120
    ImageDraw.Draw(im).text((2, 2), ','.join('%dx%d' % b for b in lay), fill=200)
    for i in ims: im.paste(i, (x, 0)); x += i.width + 8
    rows.append(im)
W = max(r.width for r in rows); out = Image.new('L', (W, sum(r.height + 4 for r in rows)), 20); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height + 4
out.save(os.path.join(ROOT, 'work', 'shot', 'cand.png'))
print(n, len(cands))
