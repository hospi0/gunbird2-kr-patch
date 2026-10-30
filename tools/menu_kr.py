# -*- coding: utf-8 -*-
r"""메뉴 설명 한글화(2026-10-30) — MENU.CHR(머리 없음, 칸 = ARGB1555 16×16, 대사와 같은 트위들·뒤집기)
  띠 A = 2214~ 3줄×76열(모드 설명 5개: ORIGINAL1·2·ARCADE·GALLERY·INTERNET, 왼쪽 맞춤)
  띠 B = 2481~ 3줄×40열(옵션 설명 3개: OPTION·RANKING·EXIT, 가운데 맞춤, «難易度» 노랑 0xFF40)
  (RESOURCE.BIN 기록 2213·2481 — 띠 A 는 3의 배수 어긋남이라 2214 로 그리면 줄이 맞음)
  글자 = 흰색 0xFFFE(1555), 원문 글자 화소(0xFFFE·0xFF40)만 지우고 다시 그림 — 같은 띠의 메뉴 그림 조각(EXIT 등)은 안 건드림
  설명마다 x 범위 = 원문 글자가 있던 칸 열 안(조각 경계 몰라 보수적으로), 넘치면 빌드 에러. 글꼴 갈무리11(12px)
  python tools/menu_kr.py [--build]   → work/shot/menu/*.png 미리보기, --build 면 work/build/MENU.CHR"""
import os, sys, struct
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile
FONT = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11.ttf'
WHITE, YELLOW = 0xFFFE, 0xFF40
TXT = {WHITE, YELLOW}
STRIPS = [  # (시작 칸, 열, 맞춤, [번역 줄들…] 설명 순서)
    (2214, 76, 'left', [
        ['가로 화면, 세로 스크롤의', '오리지널 모드입니다.'],
        ['가로 화면으로 아케이드판 게임 밸런스를', '재현한 모드입니다. 자기 기체 위치에', '따라 화면이 위아래로 스크롤됩니다.'],
        ['아케이드판 이식 모드입니다.', '(세로 화면, 세로 스크롤)'],
        ['일러스트와 설정 자료를', '즐길 수 있습니다.'],
        ['인터넷에 접속할 수 있습니다.'],
    ]),
    (2481, 40, 'center', [
        ['각종 설정을', '바꿀 수 있습니다.'],
        ['랭킹을 표시합니다.', '랭킹 화면에서는 방향 버튼 좌우로', '{난이도}별 표시를 고를 수 있습니다.'],
        ['모드 선택으로', '돌아갑니다.'],
    ]),
]


# 모드 안내 띠 2442~ 3줄×14열(마지막 열 = 옵션 띠 2481 첫 열과 같은 칸). 아이콘(A·✚·Y)은 그림 — 상자 안은 안 건드림
#   (x, 잉크 윗줄 y, 글꼴, [(글, 색)…]) — 원문 글자 위치 그대로. 셋째 줄은 갈무리11 로 254px 라 같은 높이 좁은꼴
CYAN = 0xA3FF
FONT_C = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11-Condensed.ttf'
GUIDE = (2442, 14, [(0, 0, 22, 20), (86, 0, 104, 20), (6, 20, 21, 36)], [
    (22, 5, FONT, [(':시작', WHITE)]),
    (105, 5, FONT, [(':좌우로 ', WHITE), ('난이도', YELLOW), (' 선택', WHITE)]),
    (22, 24, FONT_C, [(':2캐릭터 모드(1P용)', CYAN)]),
    (32, 35, FONT_C, [('혼자서 2인 플레이', YELLOW), (' 스토리를 즐길 수 있습니다', CYAN)]),     # 원본도 «1人で2人プレイ»만 노랑
])


# 세로 화면(TATE)판 — 칸마다 시계 방향 90° 돌린 사본. 3줄×14칸 띠: 세로판 칸 = 기점 + (2−줄)×14 + (13−열)
#   안내 띠 2442 → 2640(원본 42칸 전부 검산), 옵션 설명 = 2682·2724·2766(세로판만 있는 별도 줄 배치, 가운데 맞춤)
#   모드 설명 5개는 세로판 없음(MENU.CHR 전체 글자 모양 검색 0)
TATE_GUIDE = 2640
TATE_OPT = [
    (2682, [None, '각종 설정을 바꿀 수 있습니다.', None]),
    (2724, ['랭킹을 표시합니다.', '랭킹 화면에서는 방향 버튼 좌우로', '{난이도}별 표시를 고를 수 있습니다.']),
    (2766, [None, '모드 선택으로 돌아갑니다.', None]),
]
# 키 설정 낱말 — 4288~ 1줄 띠, 같은 배치 3벌(1,504px 간격: 회색·흰색·주황). 낱말마다 칸이 따로라 칸 범위 안 가운데.
#   (원문 잉크 x0, x1 — 첫 벌 기준, 세로판 K: 세로판 칸 = K − 가로 칸, 벌마다 +194)
KEY_BASE, KEY_PERIOD, KEY_TATE_STEP, KEY_TOP = 4288, 1504, 194, 4
KEY_COLORS = [0xDADB, 0xFFFF, 0xFF08]
KEY_WORDS = [(1218, 1252, 7913), (1266, 1287, 7918), (1298, 1347, 7924), (1362, 1422, 7932), (1457, 1480, 7942), (1553, 1602, 7956)]
KEY_KO = ['샷', '폭탄', '근접 공격', '샷 연사', '진동', '초기 설정']     # ショット ボム 接近攻撃 ショット連射 振動 初期設定
# 키 설정 왼쪽 목록(회색) — 9줄×4열 블록(열 단위·아래 줄부터, 줄 = A B X Y R L 振動 初期設定 EXIT 의 거꾸로), P1 4223 · P2 4259
#   (아래에서 몇째 줄, 열 수, 한글, 세로판 칸 = 세로판 기점 + 오프셋 − 열) — 세로판 기점 P1 3400 · P2 3440
LABEL_BLOCKS = [(4223, 3400), (4259, 3440)]
LABEL_LINES = [(1, 4, '초기 설정', 3), (2, 2, '진동', 11)]


class BuildError(Exception): pass


T0 = None                                               # 원본 칸(검산용)


def tile_of(T, t):
    return get(T, t, 1, 1)


def set_tile(T, t, g):
    put(T, t, 1, 1, g)


def rot_cw(g):
    return [list(r) for r in zip(*g[::-1])]


def rot_ccw(g):
    return [list(r) for r in zip(*g)][::-1]


def tate_get(T, base):
    img = [[0] * 224 for _ in range(48)]
    for r in range(3):
        for c in range(14):
            g = rot_ccw(tile_of(T, base + (2 - r) * 14 + 13 - c))
            for y in range(16): img[r * 16 + y][c * 16:c * 16 + 16] = g[y]
    return img


def tate_put(T, a, R, C, base, img, check=None):
    assert (R, C) == (3, 14)
    if check is not None:                               # 원본 가로판 ↔ 세로판 검산
        for r in range(3):
            for c in range(14):
                h = [row[c * 16:c * 16 + 16] for row in check[r * 16:r * 16 + 16]]
                if rot_cw(h) != tile_of(T0, base + (2 - r) * 14 + 13 - c): raise BuildError('세로판 어긋남 %d (%d,%d)' % (base, r, c))
    for r in range(3):
        for c in range(14):
            h = [row[c * 16:c * 16 + 16] for row in img[r * 16:r * 16 + 16]]
            set_tile(T, base + (2 - r) * 14 + 13 - c, rot_cw(h))


def draw_text(img, fn, text, col, x, ytop):
    """{…} 노랑. x=None 이면 가운데. ytop = 잉크 윗줄(‘가’ 기준)"""
    f = ImageFont.truetype(fn, 12); top = f.getbbox('가')[1]
    parts = []; t = text
    while '{' in t:
        a, _, rest = t.partition('{'); b, _, t = rest.partition('}'); parts += [(a, col), (b, YELLOW)]
    parts.append((t, col))
    W = len(img[0]); w = int(f.getlength(''.join(p for p, _ in parts)))
    if x is None: x = (W - w) // 2
    if x < 1 or x + w > W - 1: raise BuildError('폭 넘침 «%s» %dpx (칸 %dpx)' % (text, w, W))
    for p, c in parts:
        pw = int(f.getlength(p))
        im = Image.new('1', (pw + 2, 20), 0); ImageDraw.Draw(im).text((0, 0), p, font=f, fill=1)
        for yy in range(20):
            for xx in range(im.width):
                if im.getpixel((xx, yy)):
                    Y = ytop + yy - top
                    if not 0 <= Y < len(img): raise BuildError('높이 넘침 «%s»' % text)
                    img[Y][x + xx] = c
        x += pw


def render_center(img, lines):
    tops = []
    for r in range(3):
        ys = [y for y in range(r * 16, r * 16 + 16) if any(v in TXT for v in img[y])]
        tops.append(min(ys) if ys else None)
    for y in range(len(img)):
        for x in range(len(img[0])):
            if img[y][x] in TXT: img[y][x] = 0
    for r, ln in enumerate(lines):
        if ln is None: continue
        if tops[r] is None: raise BuildError('세로판 원문 줄 없음 %d' % r)
        draw_text(img, FONT, ln, WHITE, None, tops[r])
    return img


def sheet(pairs, path, scale):
    W = max(o.width for o, _ in pairs); H = sum(o.height * 2 + 8 for o, _ in pairs)
    pv = Image.new('RGB', (W, H), (80, 80, 80)); y = 0
    for o, n in pairs:
        pv.paste(o, (0, y)); pv.paste(n, (0, y + o.height + 2)); y += o.height * 2 + 8
    pv.resize((W * scale, H * scale), Image.NEAREST).save(path)


def render_guide(img, W, icons, items):
    inicon = lambda x, y: any(a <= x < c and b <= y < d for a, b, c, d in icons)
    for y in range(len(img)):
        for x in range(W):
            if img[y][x] in (WHITE, YELLOW, CYAN) and not inicon(x, y): img[y][x] = 0
    for x, ytop, fn, parts in items:
        f = ImageFont.truetype(fn, 12); top = f.getbbox('가')[1]
        for p, col in parts:
            pw = int(f.getlength(p))
            im = Image.new('1', (pw + 2, 20), 0); ImageDraw.Draw(im).text((0, 0), p, font=f, fill=1)
            for yy in range(20):
                for xx in range(im.width):
                    if not im.getpixel((xx, yy)): continue
                    X, Y = x + xx, ytop + yy - top
                    if not (0 <= X < W and 0 <= Y < len(img)) or inicon(X, Y): raise BuildError('안내 넘침 «%s» (%d,%d)' % (p, X, Y))
                    img[Y][X] = col
            x += pw
    return img


def load():
    d = open(os.path.join(ROOT, 'work', 'disc', 'MENU.CHR'), 'rb').read()
    return d, [list(struct.unpack_from('<256H', d, g * 512)) for g in range(len(d) // 512)]


def get(T, a, R, C):
    img = [[0] * (C * 16) for _ in range(R * 16)]
    for g in range(R * C):
        c, r = g // R, R - 1 - g % R; t = T[a + g]
        for y in range(16):
            for x in range(16): img[r * 16 + y][c * 16 + x] = t[msgtile.addr(x, y)]
    return img


def put(T, a, R, C, img):
    for g in range(R * C):
        c, r = g // R, R - 1 - g % R
        for y in range(16):
            for x in range(16): T[a + g][msgtile.addr(x, y)] = img[r * 16 + y][c * 16 + x]


def extents(img, W):
    col = [any(img[y][x] in TXT for y in range(len(img))) for x in range(W)]
    segs = []; s = None
    for x, v in enumerate(col + [False]):
        if v and s is None: s = x
        if not v and s is not None: segs.append([s, x - 1]); s = None
    m = []
    for sg in segs:
        if m and sg[0] - m[-1][1] < 14: m[-1][1] = sg[1]
        else: m.append(sg)
    return [g for g in m if g[1] - g[0] >= 20 and g[0] > 0]      # 앞 띠에서 넘어온 글자 조각(x0~) 제외


def line_rows(img, x0, x1):
    ys = [y for y in range(len(img)) if any(img[y][x] in TXT for x in range(x0, x1 + 1))]
    return ys


def render(img, W, align, texts):
    f = ImageFont.truetype(FONT, 12)
    ex = extents(img, W)
    if len(ex) != len(texts): raise BuildError('설명 개수 %d≠%d %s' % (len(ex), len(texts), ex))
    for i, ((x0, x1), lines) in enumerate(zip(ex, texts)):
        lo = x0 // 16 * 16; hi = (x1 // 16 + 1) * 16 - 1        # 원문 글자가 있던 «칸 열» 안만(스프라이트 조각 경계 모름 — 보수적으로)
        ys = line_rows(img, x0, x1); ytop, ybot = min(ys), max(ys)
        for y in range(len(img)):                       # 원문 글자 화소만 지움
            for x in range(x0, x1 + 1):
                if img[y][x] in TXT: img[y][x] = 0
        n = len(lines); h = 16 if n == 3 else 16
        y0 = (ytop + ybot) // 2 - (n * h) // 2 + 1
        cx = (x0 + x1) // 2
        wmax = max(int(f.getlength(ln.replace('{', '').replace('}', ''))) for ln in lines)
        xl = max(lo, min(x0, hi + 1 - wmax))                # 왼쪽 맞춤은 설명 안 모든 줄이 같은 시작 x
        for k, ln in enumerate(lines):
            parts = []; t = ln
            while '{' in t:
                a, _, rest = t.partition('{'); b, _, t = rest.partition('}'); parts += [(a, WHITE), (b, YELLOW)]
            parts.append((t, WHITE))
            plain = ''.join(p for p, _ in parts)
            w = int(f.getlength(plain))
            x = xl if align == 'left' else cx - w // 2
            x = min(max(x, lo), hi + 1 - w)
            if x < lo or x + w > hi + 1: raise BuildError('폭 넘침 «%s» %dpx > %dpx' % (plain, w, hi - x))
            for p, col in parts:
                im = Image.new('1', (int(f.getlength(p)) + 2, 16), 0); ImageDraw.Draw(im).text((0, 0), p, font=f, fill=1)
                pw = int(f.getlength(p))
                for yy in range(16):
                    for xx in range(im.width):
                        if im.getpixel((xx, yy)) and 0 <= y0 + k * h + yy < len(img): img[y0 + k * h + yy][x + xx] = col
                x += pw
    return img


def to_rgb(img):
    im = Image.new('RGB', (len(img[0]), len(img)), (0, 60, 0))
    for y, row in enumerate(img):
        for x, v in enumerate(row):
            if v: im.putpixel((x, y), ((v >> 10 & 31) * 8, (v >> 5 & 31) * 8, (v & 31) * 8))
    return im


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    global T0
    d, T = load(); T0 = load()[1]
    od = os.path.join(ROOT, 'work', 'shot', 'menu'); os.makedirs(od, exist_ok=True)
    a, C, icons, items = GUIDE
    img = get(T, a, 3, C); o = to_rgb(img)
    img = render_guide([row[:] for row in img], C * 16, icons, items); n = to_rgb(img)
    pv = Image.new('RGB', (o.width, o.height * 2 + 6), (80, 80, 80)); pv.paste(o, (0, 0)); pv.paste(n, (0, o.height + 6))
    pv.resize((pv.width * 4, pv.height * 4), Image.NEAREST).save(os.path.join(od, 'guide_%d.png' % a))
    put(T, a, 3, C, img)
    tate_put(T, a, 3, C, TATE_GUIDE, img, check=get(load()[1], a, 3, C))
    for a, C, align, texts in STRIPS:
        img = get(T, a, 3, C); o = to_rgb(img)
        img = render([row[:] for row in img], C * 16, align, texts); n = to_rgb(img)
        pv = Image.new('RGB', (o.width, o.height * 2 + 6), (80, 80, 80)); pv.paste(o, (0, 0)); pv.paste(n, (0, o.height + 6))
        pv.resize((pv.width * 2, pv.height * 2), Image.NEAREST).save(os.path.join(od, 'strip_%d.png' % a))
        put(T, a, 3, C, img)
    pv = []                                             # 세로판 옵션 설명(3줄×14칸, 가운데 맞춤 — 줄은 세로판 원문 줄 수대로)
    for base, lines in TATE_OPT:
        img = tate_get(T, base); o = to_rgb(img)
        img = render_center(img, lines); pv.append((o, to_rgb(img)))
        tate_put(T, base, 3, 14, base, img)
    sheet(pv, os.path.join(od, 'tate_opt.png'), 3)
    pv = []                                             # 키 설정 낱말(1줄 띠 3벌 + 낱말별 세로판)
    for cp, col in enumerate(KEY_COLORS):
        for (x0, x1, K), ko in zip(KEY_WORDS, KEY_KO):
            t0, t1 = KEY_BASE + (x0 + cp * KEY_PERIOD) // 16, KEY_BASE + (x1 + cp * KEY_PERIOD) // 16
            n = t1 - t0 + 1; K += cp * KEY_TATE_STEP
            for t in range(t0, t1 + 1):                 # 세로판 짝 검산(원본 기준)
                if rot_cw(tile_of(T0, t)) != tile_of(T0, K - t): raise BuildError('키 세로판 어긋남 %d↔%d' % (t, K - t))
            img = get(T, t0, 1, n); o = to_rgb(img)
            img = [[0] * (n * 16) for _ in range(16)]
            draw_text(img, FONT, ko, col, None, KEY_TOP)
            pv.append((o, to_rgb(img)))
            put(T, t0, 1, n, img)
            for t in range(t0, t1 + 1): set_tile(T, K - t, rot_cw(tile_of(T, t)))
    for base, tb in LABEL_BLOCKS:
        for k, n, ko, off in LABEL_LINES:
            ts = [base + c * 9 + k for c in range(n)]
            img = [[0] * (n * 16) for _ in range(16)]
            for c, t in enumerate(ts):
                if rot_cw(tile_of(T0, t)) != tile_of(T0, tb + off - c): raise BuildError('목록 세로판 어긋남 %d' % t)
                g = tile_of(T, t)
                for y in range(16): img[y][c * 16:c * 16 + 16] = g[y]
            o = to_rgb(img)
            xs = [x for x in range(n * 16) if any(img[y][x] for y in range(16))]
            ys = [y for y in range(16) if any(img[y])]
            img = [[0] * (n * 16) for _ in range(16)]
            f = ImageFont.truetype(FONT, 12)
            if xs[0] + f.getlength(ko) > n * 16 - 1: raise BuildError('목록 폭 넘침 «%s»' % ko)
            draw_text(img, FONT, ko, 0xDADB, max(xs[0], 1), ys[0])
            pv.append((o, to_rgb(img)))
            for c, t in enumerate(ts):
                g = [row[c * 16:c * 16 + 16] for row in img]
                set_tile(T, t, g); set_tile(T, tb + off - c, rot_cw(g))
    sheet(pv, os.path.join(od, 'keys.png'), 4)
    if '--build' in sys.argv:
        nd = b''.join(struct.pack('<256H', *t) for t in T) + d[len(T) * 512:]
        assert len(nd) == len(d)
        os.makedirs(os.path.join(ROOT, 'work', 'build'), exist_ok=True)
        open(os.path.join(ROOT, 'work', 'build', 'MENU.CHR'), 'wb').write(nd); print('→ work/build/MENU.CHR')
    print('미리보기 →', od)


if __name__ == '__main__':
    main()
