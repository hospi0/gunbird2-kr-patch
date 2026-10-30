# -*- coding: utf-8 -*-
r"""캐릭터 선택 별칭·이름 한글화(2026-10-30) — 공통 머리 칸 84~239(8파일 같은 내용: DCINFO01·23·4, INFO01·23·4, DCSELECT, SELECT)
  띠 = 84번부터 2줄×78열(열 단위·아래 줄부터, 칸 = ARGB1555 16×16 트위들+뒤집기), «별칭(흰) 이름(노랑)» 6쌍, 낱말마다 열이 따로
  글자 모양 = 글자 + 1px 검은 테두리 + 오른쪽 아래 그림자(불투명 0x8000), 그 밖은 투명 0. 세로판 사본 없음(8파일 회전 검색 0)
  모리건 선택 이름·「小さな」는 이 띠에 없음(노란 글자 색 전 CHR 검색 0) — 띠에는 «大魔法使い»만
  python tools/info_kr.py [--build]  → work/shot/info/strip.png, --build 면 work/build/ 에 8파일"""
import os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile

FILES = ['DCINFO01', 'DCINFO23', 'DCINFO4', 'INFO01', 'INFO23', 'INFO4', 'DCSELECT', 'SELECT']
BASE, COLS = 84, 78
GOTHIC = r'C:\claude\utils\font\nanum-gothic\NanumGothicExtraBold.ttf'
# (원문, 한글, 열 시작, 열 끝, 종류)
WORDS = [
    ('孤高の吸血鬼', '고고한 흡혈귀', 0, 6, 'nick'), ('アルカード', '알카드', 7, 13, 'name'),
    ('大魔法使い', '대마법사', 14, 19, 'nick'), ('マリオン', '마리온', 21, 26, 'name'),
    ('軍用ロボット', '군용 로봇', 27, 32, 'nick'), ('バルピロ', '발피로', 33, 39, 'name'),
    ('空飛ぶ優等生', '하늘을 나는 우등생', 40, 46, 'nick'), ('タビア', '타비아', 47, 51, 'name'),
    ('褐色の肥満体', '갈색 뚱보', 52, 58, 'nick'), ('ヘイコブ', '헤이코브', 59, 65, 'name'),
    ('炎熱はだか侍', '염열 알몸 무사', 66, 72, 'nick'), ('アイン', '아인', 73, 77, 'name'),
]
SIZE = {'nick': 15, 'name': 22}


class BuildError(Exception): pass


A = np.array([msgtile.addr(x, y) for y in range(16) for x in range(16)])
INV = np.argsort(A)


def load(f):
    d = open(os.path.join(ROOT, 'work', 'disc', f + '.CHR'), 'rb').read()
    return d, np.frombuffer(d, dtype='<u2').reshape(-1, 256)[:, A].reshape(-1, 16, 16).copy()


def get(P):
    im = np.zeros((32, COLS * 16), np.uint16)
    for g in range(2 * COLS):
        c, r = g // 2, 1 - g % 2; im[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = P[BASE + g]
    return im


def put(P, im):
    for g in range(2 * COLS):
        c, r = g // 2, 1 - g % 2; P[BASE + g] = im[r * 16:r * 16 + 16, c * 16:c * 16 + 16]


def rgb(v):
    return np.stack([(v >> 10 & 31) * 8, (v >> 5 & 31) * 8, (v & 31) * 8], -1).astype(np.uint8)


def alpha(text, size, ss=4):
    f = ImageFont.truetype(GOTHIC, size * ss)
    w = int(f.getlength(text)) + size * ss; h = size * ss * 2
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).text((size * ss // 4, size * ss // 4), text, font=f, fill=255)
    im = im.crop(im.getbbox())
    return np.asarray(im.resize((max(1, im.width // ss), max(1, im.height // ss)), Image.LANCZOS), np.float32) / 255


def row_colors(seg, ink):
    """원문 글자 줄마다 가장 흔한 색 — 한글 글자 높이에 맞춰 늘려 씀"""
    ys = np.flatnonzero(ink.any(1)); cols = []
    for y in range(ys.min(), ys.max() + 1):
        v = seg[y][ink[y]]
        cols.append(np.bincount(v).argmax() if len(v) else cols[-1])
    return np.array(cols, np.uint16), ys.min(), ys.max()


def draw_word(im, jp, ko, c0, c1, kind):
    x0, x1 = c0 * 16, c1 * 16 + 16
    seg = im[:, x0:x1]; ink = (seg & 0x7FFF) != 0
    cols, ytop, ybot = row_colors(seg, ink)
    xs = np.flatnonzero(ink.any(0)); ix0 = xs.min()
    for size in range(SIZE[kind], 11, -1):              # 넘치면 1px씩 줄임(최소 12px)
        a = alpha(ko, size); h, w = a.shape
        if ix0 + w + 4 <= x1 - x0: break
    else: raise BuildError('폭 넘침 «%s» %dpx (칸 %dpx, 시작 %d)' % (ko, w, x1 - x0, ix0))
    if size != SIZE[kind]: print('  «%s» %dpx 로 줄임' % (ko, size))
    y0 = max(0, ytop + (ybot - ytop + 1 - h) // 2)
    if y0 < 0 or y0 + h + 3 > 32: raise BuildError('높이 넘침 «%s»' % ko)
    new = np.zeros_like(seg)
    g = np.zeros(seg.shape, np.float32); g[y0:y0 + h, ix0:ix0 + w] = a
    core = g >= 0.45
    sh = np.zeros(seg.shape, bool)                       # 테두리 1px + 그림자 오른쪽 아래 3·2px
    cu = core.astype(np.uint8)
    sh |= cv2.dilate(cu, np.ones((3, 3), np.uint8)).astype(bool)
    for dx in range(0, 4):
        for dy in range(0, 3):
            sh[dy:, dx:] |= core[:seg.shape[0] - dy, :seg.shape[1] - dx]
    new[sh] = 0x8000
    edge = (g >= 0.2) & ~core                            # 얕은 가장자리 = 글자 색과 검정 섞음
    for y in range(seg.shape[0]):
        k = int(round((y - y0) / max(1, h - 1) * (len(cols) - 1))); k = min(max(k, 0), len(cols) - 1)
        c = int(cols[k])
        for x in np.flatnonzero(core[y]): new[y, x] = c
        for x in np.flatnonzero(edge[y]):
            t = g[y, x] / 0.45; r, gg, b = (c >> 10 & 31), (c >> 5 & 31), (c & 31)
            new[y, x] = 0x8000 | int(r * t) << 10 | int(gg * t) << 5 | int(b * t)
    im[:, x0:x1] = new


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    data = {f: load(f) for f in FILES}
    P0 = data[FILES[0]][1]
    for f in FILES[1:]:
        if not np.array_equal(data[f][1][BASE:BASE + 2 * COLS], P0[BASE:BASE + 2 * COLS]): raise BuildError('%s 띠 다름' % f)
    im0 = get(P0); im = im0.copy()
    for w in WORDS: draw_word(im, *w)
    od = os.path.join(ROOT, 'work', 'shot', 'info'); os.makedirs(od, exist_ok=True)
    a, b = rgb(im0), rgb(im); W = a.shape[1] // 2
    pv = np.concatenate([a[:, :W], b[:, :W], np.full((4, W, 3), 80, np.uint8), a[:, W:2 * W], b[:, W:2 * W]], 0)
    Image.fromarray(pv).resize((W * 2, pv.shape[0] * 2), Image.NEAREST).save(os.path.join(od, 'strip.png'))
    P = P0.copy(); put(P, im)
    ch = np.flatnonzero((P != P0).reshape(len(P), -1).any(1)); print('바뀐 칸 %d개' % len(ch))
    if '--build' in sys.argv:
        os.makedirs(os.path.join(ROOT, 'work', 'build'), exist_ok=True)
        for f in FILES:
            out = bytearray(data[f][0])
            for t in ch: out[t * 512:(t + 1) * 512] = P[t].reshape(256)[INV].astype('<u2').tobytes()
            open(os.path.join(ROOT, 'work', 'build', f + '.CHR'), 'wb').write(bytes(out))
        print('→ work/build/ %d파일' % len(FILES))
    print('미리보기 →', od)


if __name__ == '__main__':
    main()
