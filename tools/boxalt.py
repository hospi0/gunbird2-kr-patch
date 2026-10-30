# -*- coding: utf-8 -*-
"""창 하나를 다른 줄 수로 그려 보기 — python tools/boxalt.py 이름 창번호 → work/shot/boxalt.png (칸 수의 약수 R 전부)"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgsheet
nm, k = sys.argv[1], int(sys.argv[2]); lay = msgsheet.layout()[nm]; T = msgtile.load(nm)
s = sum(R * C for R, C in lay[:k]); n = lay[k][0] * lay[k][1]
rows = []
for R in range(1, 7):
    if n % R or n // R > 40: continue
    im = msgsheet.box_img(T, s, R, n // R); c = Image.new('L', (im.width + 60, im.height + 4), 40)
    ImageDraw.Draw(c).text((2, 2), '%dx%d' % (R, n // R), fill=200); c.paste(im, (60, 0)); rows.append(c)
W = max(r.width for r in rows); out = Image.new('L', (W, sum(r.height for r in rows)), 20); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.resize((out.width * 2, out.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'shot', 'boxalt.png'))
