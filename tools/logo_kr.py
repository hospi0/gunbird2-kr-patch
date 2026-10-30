# -*- coding: utf-8 -*-
r"""타이틀 로고 읽기 줄 「ガンバード2」 → 「건버드 2」(2026-10-30) — OPEN.004(머리 32 B, 칸 = ARGB1555 16×16 트위들+뒤집기)
  타이틀 화면 = 칸 334~633(15줄×20열 = 320×240, 화면에서 2배), 열 단위·아래 줄부터
  앞쪽 4~213(10줄×21열)·214~333(10줄×12열) 블록에도 같은 로고 한 벌 — 읽기 줄은 214 블록 맨 아랫줄
  글자 자리 = 노랑 그라데이션 + 체크 디더 → 지운 화소는 같은 줄의 같은 홀짝 자리 화소로 메움(디더 유지)
  python tools/logo_kr.py [--build]  → work/shot/logo.png, --build 면 work/build/OPEN.004"""
import os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile

FONT = r'C:\claude\utils\font\nanum-gothic\NanumGothicExtraBold.ttf'
TEXT = '건버드 2'
BLOCKS = [(334, 15, 20), (214, 10, 12)]             # (첫 칸, 줄, 열)
KANA_REF = (129, 169, 200, 181)                     # 타이틀 화면(334 블록) 읽기 줄 잉크 x0 y0 x1 y1(끝 미포함)


class BuildError(Exception): pass


A = np.array([msgtile.addr(x, y) for y in range(16) for x in range(16)])
INV = np.argsort(A)


def get(P, b, R, C):
    im = np.zeros((R * 16, C * 16), np.uint16)
    for g in range(R * C):
        c, r = g // R, R - 1 - g % R; im[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = P[b + g]
    return im


def put(P, b, R, C, im):
    for g in range(R * C):
        c, r = g // R, R - 1 - g % R; P[b + g] = im[r * 16:r * 16 + 16, c * 16:c * 16 + 16]


def rgb(v):
    return np.stack([(v >> 10 & 31) * 8, (v >> 5 & 31) * 8, (v & 31) * 8], -1).astype(np.uint8)


def navy_of(im):
    R, G, B = (im >> 10 & 31), (im >> 5 & 31), (im & 31)
    return (R < 8) & (G < 8) & (B >= 6)


def redo(im, box, navy_col):
    x0, y0, x1, y1 = box
    nv = navy_of(im); out = im.copy()
    c = lambda v: np.array([(v >> 10 & 31), (v >> 5 & 31), (v & 31)], np.float32)
    for y in range(y0 - 1, y1 + 1):                    # 상자 전체를 줄마다 좌우 바탕 사이 보간(홀짝 디더 따로)
        for par in (0, 1):
            L = next(xx for xx in range(x0 - 2, -1, -1) if (xx + y) % 2 == par and not nv[y, xx])
            Rr = next((xx for xx in range(x1 + 1, im.shape[1]) if (xx + y) % 2 == par and not nv[y, xx]), None)
            xs = [xx for xx in range(x0 - 1, x1 + 1) if (xx + y) % 2 == par]
            if Rr is None or nv[y, x1 + 1:Rr].any(): Rr = L                 # 오른쪽이 «2» 남색 테두리면 왼쪽 값으로
            cl, cr = c(int(im[y, L])), c(int(im[y, Rr]))
            for xx in xs:
                t = 0 if Rr == L else (xx - L) / (Rr - L)
                v = np.clip(np.rint(cl * (1 - t) + cr * t), 0, 31).astype(int)
                out[y, xx] = 0x8000 | v[0] << 10 | v[1] << 5 | v[2]
    # 글자
    h = y1 - y0
    for size in range(20, 8, -1):
        f = ImageFont.truetype(FONT, size)
        t = Image.new('L', (200, 40), 0); ImageDraw.Draw(t).text((2, 2), TEXT, font=f, fill=255)
        t = t.crop(t.getbbox())
        if t.height <= h: break
    a = np.asarray(t) >= 110
    a[:, 1:] |= a[:, :-1]                              # 원본 가나처럼 굵게(가로 1px)
    w = a.shape[1]
    if w > x1 - x0 + 6: raise BuildError('로고 글자 폭 넘침 %d' % w)
    gx = x0 + (x1 - x0 - w) // 2; gy = y0 + (h - a.shape[0]) // 2
    out[gy:gy + a.shape[0], gx:gx + w][a] = navy_col
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    path = os.path.join(ROOT, 'work', 'disc', 'OPEN.004'); d = open(path, 'rb').read()
    P = np.frombuffer(d[32:], dtype='<u2').reshape(-1, 256)[:, A].reshape(-1, 16, 16).copy(); P0 = P.copy()
    ref = get(P, *BLOCKS[0]); x0, y0, x1, y1 = KANA_REF
    patch = navy_of(ref)[y0:y1, x0:x1].astype(np.float32)
    navy_col = int(np.bincount(ref[y0:y1, x0:x1][navy_of(ref)[y0:y1, x0:x1]]).argmax())
    pv = []
    for b, R, C in BLOCKS:
        im = get(P, b, R, C)
        res = cv2.matchTemplate(navy_of(im).astype(np.float32), patch, cv2.TM_SQDIFF)
        mn, _, loc, _ = cv2.minMaxLoc(res)
        if mn > 4: raise BuildError('블록 %d 읽기 줄 못 찾음(%.0f)' % (b, mn))
        box = (loc[0], loc[1], loc[0] + x1 - x0, loc[1] + y1 - y0)
        new = redo(im, box, navy_col); put(P, b, R, C, new)
        bx0, by0 = max(0, box[0] - 30), max(0, box[1] - 20)
        crop = lambda v: rgb(v)[by0:box[3] + 12, bx0:box[2] + 30]
        pv.append(np.concatenate([crop(im), np.full((4, crop(im).shape[1], 3), 80, np.uint8), crop(new)], 0))
        print('블록 %d 읽기 줄 %s' % (b, box))
    full = rgb(get(P, *BLOCKS[0]))
    W = max(p.shape[1] for p in pv)
    sheet = np.concatenate([np.pad(p, ((0, 6), (0, W - p.shape[1]), (0, 0)), constant_values=80) for p in pv], 0)
    Image.fromarray(sheet).resize((W * 6, sheet.shape[0] * 6), Image.NEAREST).save(os.path.join(ROOT, 'work', 'shot', 'logo_zoom.png'))
    Image.fromarray(np.concatenate([rgb(get(P0, *BLOCKS[0])), full], 1)).resize((1280, 480), Image.NEAREST).save(os.path.join(ROOT, 'work', 'shot', 'logo.png'))
    ch = np.flatnonzero((P != P0).reshape(len(P), -1).any(1)); print('바뀐 칸 %d개' % len(ch))
    if '--build' in sys.argv:
        out = bytearray(d)
        for t in ch: out[32 + t * 512:32 + (t + 1) * 512] = P[t].reshape(256)[INV].astype('<u2').tobytes()
        open(os.path.join(ROOT, 'work', 'build', 'OPEN.004'), 'wb').write(bytes(out)); print('→ work/build/OPEN.004')


if __name__ == '__main__':
    main()
