# -*- coding: utf-8 -*-
r"""일러스트 갤러리 메뉴 한글화(2026-10-30) — GALLERY.CHR(머리 없음, 칸 = ARGB1555 16×16, 대사와 같은 트위들·뒤집기)
  화면 640×480 = 칸 0~1199: 열 블록 3개(0~15열 기점 0 · 16~30열 기점 480 · 31~39열 기점 930), 블록 안은 위·아래 15줄 띠,
    띠 안은 열 단위·아래 줄부터 — 칸 = 기점 + 띠×15×블록폭 + 15×(열−블록시작) + (14 − 줄%15)
    (일러스트갤러리 스샷과 1,200자리 대조, 선택된 «マリオン» 띠 자리 빼고 전부 일치)
  칸 1200~1469 = 선택 항목 덧그림 9개(항목마다 2줄×15열, 열 단위·아래 줄부터), 파란 띠 + 흰 글씨
  글자 지우기 = 글자 색 화소만 골라(회색·흰 글씨, 파란 바탕 위 그림자) 주변에서 메움(cv2 inpaint) — 검정 띠 위 검은 그림자는 안 보이니 둠
  python tools/gallery_menu_kr.py [--build]  → work/shot/gallery_menu/*.png 미리보기, --build 면 work/build/GALLERY.CHR"""
import os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile

SERIF = r'C:\claude\utils\font\nanum-myeongjo\NanumMyeongjoExtraBold.ttf'
BLOCKS = [(0, 16, 0), (16, 15, 480), (31, 9, 930)]
SEL_BASE = 1200
TITLE = '건버드 2  일러스트 갤러리'          # ガンバード２　イラストギャラリー
TITLE_BOX = (25, 28, 530, 68)                 # x0 y0 x1 y1 (지울 범위)
NAMES = ['마리온', '알카드', '타비아', '발피로', '헤이코브', '아인', '모리건', 'Q 파이레츠', '스페셜 일러스트']
ITEM_Y = [(123, 146), (159, 183), (193, 218), (225, 253), (267, 290), (304, 326), (338, 362), (375, 399), (411, 434)]   # 회색 글자 화소 줄 범위 ±2
ITEM_X1 = [158, 192, 144, 168, 162, 142, 168, 208, 278]      # 항목마다 지울 오른쪽 끝(글자 끝 + 그림자) — 넘으면 캐릭터 그림을 지움
LIST_X0 = 52
ROBOT = (422, 34, 452, 70)                                  # 제목 «ラ» 밑 로봇 원통 머리 — 아주 흰 글자 화소만 지움
NAME_COL = (112, 128, 144)
NAME_END_SEL = [100, 140, 90, 110, 110, 90, 110, 160, 230]   # 선택 덧그림 안 가나 글자 오른쪽 끝(이 너머는 캐릭터 그림)
NAME_SIZE = 24                                # 원본 가나 잉크 높이 20px 에 맞춤
SHADOW_COL = (24, 16, 40)


class BuildError(Exception): pass


A = np.array([msgtile.addr(x, y) for y in range(16) for x in range(16)])
INV = np.argsort(A)


def load():
    d = open(os.path.join(ROOT, 'work', 'disc', 'GALLERY.CHR'), 'rb').read()
    n = len(d) // 512
    P = np.frombuffer(d, dtype='<u2').reshape(n, 256)[:, A].reshape(n, 16, 16).copy()
    return d, P


def pid(r, c):
    for c0, w, base in BLOCKS:
        if c0 <= c < c0 + w: return base + (r // 15) * 15 * w + 15 * (c - c0) + (14 - r % 15)


def to_rgb(P):
    return np.stack([(P >> 10 & 31) * 8, (P >> 5 & 31) * 8, (P & 31) * 8], -1).astype(np.uint8)


def to_1555(rgb):
    r, g, b = [(rgb[..., i].astype(np.int32) + 4).clip(0, 255) >> 3 for i in range(3)]
    return (0x8000 | r.clip(0, 31) << 10 | g.clip(0, 31) << 5 | b.clip(0, 31)).astype(np.uint16)


def screen(P):
    S = np.zeros((480, 640), np.uint16)
    for r in range(30):
        for c in range(40): S[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = P[pid(r, c)]
    return S


def unscreen(P, S):
    for r in range(30):
        for c in range(40): P[pid(r, c)] = S[r * 16:r * 16 + 16, c * 16:c * 16 + 16]


def sel_get(P, i):
    S = np.zeros((32, 240), np.uint16)
    for g in range(30):
        c, r = g // 2, 1 - g % 2; S[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = P[SEL_BASE + 30 * i + g]
    return S


def sel_put(P, i, S):
    for g in range(30):
        c, r = g // 2, 1 - g % 2; P[SEL_BASE + 30 * i + g] = S[r * 16:r * 16 + 16, c * 16:c * 16 + 16]


def text_mask(rgb, box, bright):
    """글자 색 화소만: bright=True 면 흰·회색 글씨(+파란 바탕 위 그림자), 상자 밖은 안 건드림"""
    x0, y0, x1, y1 = box
    R, G, B = [rgb[..., i].astype(np.int32) for i in range(3)]
    m = (R > 40) | (G > 40) | (((B - R) < 30) & (np.maximum(np.maximum(R, G), B) >= 20)) | ((R >= 24) & (R >= G))   # 끝 = 보라 반투명 그림자
    if bright: m = (R > 80) & (G > 80)
    out = np.zeros(m.shape, bool); out[y0:y1, x0:x1] = m[y0:y1, x0:x1]
    return cv2.dilate(out.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & box_mask(m.shape, box)


def box_mask(shape, box):
    x0, y0, x1, y1 = box; b = np.zeros(shape, bool); b[y0:y1, x0:x1] = True; return b


def erase(rgb, mask):
    return cv2.inpaint(rgb, mask.astype(np.uint8), 3, cv2.INPAINT_TELEA)


def render(text, size, shear=0.0, ss=4):
    """글자 알파(0~1) — ss배로 그려 줄임. 반환 (alpha, 왼쪽 위 잉크 기준 오프셋)"""
    f = ImageFont.truetype(SERIF, size * ss)
    w = int(f.getlength(text)) + size * ss * 2; h = size * ss * 2
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).text((size * ss // 2, size * ss // 4), text, font=f, fill=255)
    if shear: im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * h * 0.6, 0, 1, 0), Image.BICUBIC)
    bb = im.getbbox(); im = im.crop(bb)
    im = im.resize((max(1, im.width // ss), max(1, im.height // ss)), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def blend(rgb, alpha, x, y, col, op=1.0):
    h, w = alpha.shape
    if x < 0 or y < 0 or y + h > rgb.shape[0] or x + w > rgb.shape[1]: raise BuildError('그림 밖 (%d,%d %dx%d)' % (x, y, w, h))
    reg = rgb[y:y + h, x:x + w].astype(np.float32); a = (alpha * op)[..., None]
    rgb[y:y + h, x:x + w] = (reg * (1 - a) + np.array(col, np.float32) * a).clip(0, 255).astype(np.uint8)


def ink_box(mask):
    ys, xs = np.nonzero(mask); return xs.min(), ys.min(), xs.max(), ys.max()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d, P = load(); P0 = P.copy()
    od = os.path.join(ROOT, 'work', 'shot', 'gallery_menu'); os.makedirs(od, exist_ok=True)
    rgb0 = to_rgb(screen(P)); rgb = rgb0.copy()
    # 제목 — 흰 글자 + 바로 옆 검은 그림자만, 금색·로봇 원통은 보호
    R, G, B = [rgb0[..., i].astype(np.int32) for i in range(3)]
    tb = box_mask(R.shape, TITLE_BOX); rb = box_mask(R.shape, ROBOT)
    mn, mx = np.minimum(np.minimum(R, G), B), np.maximum(np.maximum(R, G), B)
    core = tb & (mn >= 150) & (mx - mn < 45) & ~(rb & (mn < 225))
    tx0, ty0, tx1, ty1 = ink_box(core & (mn >= 215))
    k = lambda n: np.ones((n, n), np.uint8)
    near = cv2.dilate(core.astype(np.uint8), k(7)).astype(bool)
    shadow = near & tb & (mx < 40)
    m = cv2.dilate(core.astype(np.uint8), k(3)).astype(bool) | shadow
    m &= ~((R - B > 60) & (R > 120))
    rgb = erase(rgb, m)
    a = render(TITLE, 34, shear=0.22)
    if a.shape[1] > TITLE_BOX[2] - tx0: raise BuildError('제목 폭 넘침 %d' % a.shape[1])
    ty = ty0 + (ty1 - ty0 - a.shape[0]) // 2
    blend(rgb, a, tx0 + 2, ty + 2, (0, 0, 0), 0.85); blend(rgb, a, tx0, ty, (240, 240, 248))
    # 목록
    for (y0, y1), ex, ko in zip(ITEM_Y, ITEM_X1, NAMES):
        box = (LIST_X0, y0, ex, y1 + 4)
        core = (rgb0[..., 1] > 90) & box_mask(rgb.shape[:2], box)
        if not core.any(): raise BuildError('목록 글자 없음 %d' % y0)
        x0, iy0, x1, iy1 = ink_box(core)
        rgb = erase(rgb, text_mask(rgb, box, False))
        a = render(ko, NAME_SIZE)
        y = iy0 + (iy1 - iy0 - a.shape[0]) // 2
        blend(rgb, a, x0 + 3, y + 3, SHADOW_COL, 0.7); blend(rgb, a, x0, y, NAME_COL)
    S = to_1555(rgb)
    unscreen(P, S)
    pv = np.concatenate([rgb0, np.full((480, 6, 3), 80, np.uint8), rgb], 1)
    Image.fromarray(pv).save(os.path.join(od, 'screen.png'))
    # 선택 덧그림
    sheets = []
    for i, ko in enumerate(NAMES):
        s0 = to_rgb(sel_get(P, i)); s = s0.copy()
        sR, sG, sB = [s[..., j].astype(np.int32) for j in range(3)]
        smn = np.minimum(np.minimum(sR, sG), sB)
        core = (smn > 150) & (np.abs(sR - sB) < 40)                 # 흰 글씨(캐릭터 그림은 오른쪽 — 글자 칸 범위로 자름)
        core[:, NAME_END_SEL[i]:] = False
        x0, iy0, x1, iy1 = ink_box(core)
        mm = cv2.dilate(((smn > 70) & (np.abs(sR - sB) < 60)).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        mm[:, x1 + 4:] = False
        s = erase(s, mm)
        a = render(ko, NAME_SIZE)
        y = iy0 + (iy1 - iy0 - a.shape[0]) // 2
        if x0 + a.shape[1] > 240: raise BuildError('선택 폭 넘침 %s' % ko)
        blend(s, a, x0 + 2, y + 2, (0, 0, 40), 0.6); blend(s, a, x0, y, (248, 248, 248))
        sel_put(P, i, to_1555(s))
        sheets.append(np.concatenate([s0, np.full((32, 4, 3), 80, np.uint8), s], 1))
    Image.fromarray(np.concatenate([np.pad(x, ((0, 4), (0, 0), (0, 0)), constant_values=80) for x in sheets], 0)).resize((484 * 2, 36 * 9 * 2), Image.NEAREST).save(os.path.join(od, 'selected.png'))
    ch = sorted(set(np.flatnonzero((P != P0).reshape(len(P), -1).any(1)).tolist()))
    print('바뀐 칸 %d개' % len(ch))
    if '--build' in sys.argv:
        out = bytearray(d)
        for t in ch: out[t * 512:(t + 1) * 512] = P[t].reshape(256)[INV].astype('<u2').tobytes()
        os.makedirs(os.path.join(ROOT, 'work', 'build'), exist_ok=True)
        open(os.path.join(ROOT, 'work', 'build', 'GALLERY.CHR'), 'wb').write(bytes(out)); print('→ work/build/GALLERY.CHR')
    print('미리보기 →', od)


if __name__ == '__main__':
    main()
