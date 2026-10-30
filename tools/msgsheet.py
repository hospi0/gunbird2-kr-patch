# -*- coding: utf-8 -*-
"""대사 그림 판독용 낱장 — work/msg_strips.json(띠 나누기, tools/msgseg.py + 손 고침 work/msg_strips_fix.json) 으로
   스테이지마다 파일·창을 늘어놓은 그림 → work/shot/sheet/STGn_k.png
   python tools/msgsheet.py [스테이지…]"""
import os, sys, json, glob
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'work'))
import msgtile


def layout():
    lay = json.load(open(os.path.join(ROOT, 'work', 'msg_strips.json')))
    fx = os.path.join(ROOT, 'work', 'msg_strips_fix.json')
    if os.path.exists(fx): lay.update(json.load(open(fx)))
    return lay


def box_img(T, s, R, C):
    im = Image.new('L', (C * 16, R * 16), 0)
    for g in range(R * C):
        t = T[s + g]; c, r = g // R, R - 1 - g % R
        for y in range(16):
            for x in range(16):
                if t[msgtile.addr(x, y)]: im.putpixel((c * 16 + x, r * 16 + y), 255)
    return im


def main():
    lay = layout()
    out = os.path.join(ROOT, 'work', 'shot', 'sheet'); os.makedirs(out, exist_ok=True)
    stages = sys.argv[1:] or [str(i) for i in range(1, 8)]
    for st in stages:
        names = sorted(n for n in lay if n.startswith('STG%sDEMOMSG' % st if st.isdigit() else st))
        per = 12 if st.isdigit() else 3
        for k in range(0, len(names), per):
            rows = []
            for nm in names[k:k + per]:
                T = msgtile.load(nm); s = 0
                for b, (R, C) in enumerate(lay[nm]):
                    rows.append(('%s #%d %dx%d' % (nm[-3:], b, R, C), box_img(T, s, R, C))); s += R * C
            H = sum(max(20, im.height + 4) for _, im in rows); W = max(im.width for _, im in rows) + 70
            sh = Image.new('L', (W, H), 40); d = ImageDraw.Draw(sh); y = 0
            for lab, im in rows:
                d.text((2, y + 2), lab, fill=200); sh.paste(im, (70, y)); y += max(20, im.height + 4)
            sh.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(out, '%s_%d.png' % ('STG' + st if st.isdigit() else st.replace('.', '_'), k // per + 1)))


if __name__ == '__main__':
    main()
