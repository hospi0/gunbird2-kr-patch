# -*- coding: utf-8 -*-
r"""컨트롤러·메모리 카드 안내 판자 한글화(2026-10-30) — SYSTEM.CHR 2500~2551(4줄×13열, 열 단위·아래 줄부터) 나무 판자 그림
  원문 「コントローラが抜けている／か、またはメモリーカードの／認識中です。」 — 다른 파일·회전판 사본 없음
  글자 = 대사와 같은 세로 그라데이션(줄 안 행마다 원문 색), 그림자 = 오른쪽 아래 1px 나무 어둡게
  지우기 = 글자 색(흰·하늘) 화소 + 그 오른쪽 아래 그림자만 골라 나무결로 메움(cv2 inpaint)
  python tools/syspanel_kr.py [--build]  → work/shot/syspanel.png, --build 면 work/build/SYSTEM.CHR"""
import os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile

FONT = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri14.ttf'
BASE, R, C = 2500, 4, 13
LINES = ['컨트롤러가 빠져 있거나', '메모리 카드를 인식하는', '중입니다.']
X0, X1 = 16, 200                                    # 글자 칸(판자 테두리 안) — 원문 글자 시작 x 16


class BuildError(Exception): pass


A = np.array([msgtile.addr(x, y) for y in range(16) for x in range(16)])
INV = np.argsort(A)


def get(P):
    im = np.zeros((R * 16, C * 16), np.uint16)
    for g in range(R * C):
        c, r = g // R, R - 1 - g % R; im[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = P[BASE + g]
    return im


def put(P, im):
    for g in range(R * C):
        c, r = g // R, R - 1 - g % R; P[BASE + g] = im[r * 16:r * 16 + 16, c * 16:c * 16 + 16]


def rgb(v):
    return np.stack([(v >> 10 & 31) * 8, (v >> 5 & 31) * 8, (v & 31) * 8], -1).astype(np.uint8)


def to1555(a):
    a = a.astype(np.int32)
    return (0x8000 | (a[..., 0] >> 3) << 10 | (a[..., 1] >> 3) << 5 | (a[..., 2] >> 3)).astype(np.uint16)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    path = os.path.join(ROOT, 'work', 'disc', 'SYSTEM.CHR'); d = open(path, 'rb').read()
    P = np.frombuffer(d, dtype='<u2').reshape(-1, 256)[:, A].reshape(-1, 16, 16).copy(); P0 = P.copy()
    im0 = get(P); r, g, b = (im0 >> 10 & 31).astype(int), (im0 >> 5 & 31).astype(int), (im0 & 31).astype(int)
    txt = ((b - r >= 6) & (b >= 20)) | ((r >= 26) & (g >= 26) & (b >= 26))
    txt[:, :X0 - 4] = False  # 테두리; txt[:, X1 + 12:] = False
    ys = np.flatnonzero(txt.any(1))
    # 원문 줄마다 윗줄·행 색
    rows = []; s = None
    for y in list(range(im0.shape[0])) + [None]:
        v = y is not None and txt[y].any()
        if v and s is None: s = y
        if not v and s is not None: rows.append((s, y - 1)); s = None
    if len(rows) != 3: raise BuildError('원문 줄 %d개' % len(rows))
    grad = []
    for y in range(rows[0][0], rows[0][1] + 1):
        v = im0[y][txt[y]]; grad.append(int(np.bincount(v).argmax()))
    sh = np.zeros_like(txt); sh[1:, 1:] = txt[:-1, :-1]
    mask = cv2.dilate((txt | sh).astype(np.uint8), np.ones((2, 2), np.uint8))
    base = cv2.inpaint(rgb(im0), mask, 2, cv2.INPAINT_TELEA)
    new = to1555(base); new[mask == 0] = im0[mask == 0]
    f = ImageFont.truetype(FONT, 15)
    for (top, bot), ln in zip(rows, LINES):
        w = int(f.getlength(ln))
        if X0 + w > X1 + 10: raise BuildError('폭 넘침 «%s» %dpx' % (ln, w))
        m = Image.new('1', (w + 4, 20), 0); dr = ImageDraw.Draw(m); dr.fontmode = '1'; dr.text((0, 0), ln, font=f, fill=1)
        a = np.asarray(m, bool); yy, xx = np.nonzero(a); a = a[yy.min():yy.max() + 1]
        h = a.shape[0]; y0 = top + (bot - top + 1 - h) // 2
        for y in range(h):
            for x in np.flatnonzero(a[y]):
                Y, X = y0 + y + 1, X0 + x + 1                 # 그림자
                if Y < new.shape[0]:
                    v = int(new[Y, X]); new[Y, X] = 0x8000 | ((v >> 10 & 31) // 2) << 10 | ((v >> 5 & 31) // 2) << 5 | (v & 31) // 2
        for y in range(h):
            k = min(int(y / max(1, h - 1) * (len(grad) - 1) + 0.5), len(grad) - 1)
            for x in np.flatnonzero(a[y]): new[y0 + y, X0 + x] = grad[k]
    put(P, new)
    pv = np.concatenate([rgb(im0), np.full((4, C * 16, 3), 80, np.uint8), rgb(new)], 0)
    Image.fromarray(pv).resize((C * 64, pv.shape[0] * 4), Image.NEAREST).save(os.path.join(ROOT, 'work', 'shot', 'syspanel.png'))
    ch = np.flatnonzero((P != P0).reshape(len(P), -1).any(1)); print('바뀐 칸 %d개' % len(ch))
    if '--build' in sys.argv:                           # 힌트 대사(msgbuild)가 먼저 SYSTEM.CHR 를 만들었으면 그 위에
        bp = os.path.join(ROOT, 'work', 'build', 'SYSTEM.CHR')
        out = bytearray(open(bp, 'rb').read() if os.path.exists(bp) else d)
        for t in ch: out[t * 512:(t + 1) * 512] = P[t].reshape(256)[INV].astype('<u2').tobytes()
        open(os.path.join(ROOT, 'work', 'build', 'SYSTEM.CHR'), 'wb').write(bytes(out)); print('→ work/build/SYSTEM.CHR')


if __name__ == '__main__':
    main()
