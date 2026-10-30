# -*- coding: utf-8 -*-
"""창 나누기 후보 그려 보기 — python tools/msgtry.py STG1DEMOMSG.014 "3x7,2x1" "2x10,3x1" … → work/shot/try.png"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgsheet
nm = sys.argv[1]; T = msgtile.load(nm)
rows = []
for spec in sys.argv[2:]:
    lay = [tuple(int(v) for v in b.split('x')) for b in spec.split(',')]
    assert sum(r * c for r, c in lay) == len(T), (spec, len(T))
    s = 0; ims = []
    for R, C in lay: ims.append(msgsheet.box_img(T, s, R, C)); s += R * C
    W = sum(i.width + 8 for i in ims); H = max(i.height for i in ims)
    im = Image.new('L', (W + 80, H + 4), 40); x = 80; ImageDraw.Draw(im).text((2, 2), spec, fill=200)
    for i in ims: im.paste(i, (x, 0)); x += i.width + 8
    rows.append(im)
W = max(r.width for r in rows); out = Image.new('L', (W, sum(r.height + 4 for r in rows)), 20); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height + 4
out.resize((out.width * 2, out.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'shot', 'try.png'))
print(len(T))
