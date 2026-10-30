# -*- coding: utf-8 -*-
r"""갤러리 해설 PVR 한글화(2026-10-30) — DC_G_KAISETU{MA,AL,TA,VA,HE,AN,MO,QP,CAP0,CAP1}.PVR (1024×1024 ARGB1555 트위들, 앞 16 B GBIX)
  패널 = 575×96 상자 10개(y = k×96), 테두리 바깥 4px 는 그대로, 안쪽(x 6~568, y 4~92)을 바탕색으로 지우고 다시 그림:
    1줄(y 14~33)·2줄(y 46~65) = 나눔명조 ExtraBold 20px 흰색(넘치면 15px 까지 줄임, 그래도 넘치면 에러) — 1줄은 «번호» x16, 나머지 x88, «CV：…» 오른쪽 맞춤
    조작 줄(y 76~90) = 갈무리11 흰색(원본 픽셀 글꼴 자리) — 원본에 조작 줄이 있던 패널만
  인코딩: PyPVR(-tw -1555, %TEMP% 아래 임시 폴더 — 경로에 «-» 있으면 PyPVR 실패, 끝나면 지움) + 원본 GBIX 16 B → 원본 PNG 재인코딩이 디스크와 바이트 동일함을 먼저 확인
  python tools/gallery_kr.py            → work/shot/gallery/<이름>.png (원본|한글 미리보기)
  python tools/gallery_kr.py --build    → work/build/DC_G_KAISETU*.PVR"""
import os, tempfile, atexit, sys, csv, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TMP = tempfile.mkdtemp(prefix='gb2pvr_')            # %TEMP%(대시 없음) 아래, 끝나면 지움 — ⛔C:\claude 밑에 임시 폴더 만들지 말 것
atexit.register(shutil.rmtree, TMP, True)
assert '-' not in TMP, TMP
PYPVR = r'C:\claude\utils\dreamcast\PyPVR\pypvr.py'
SERIF = r'C:\claude\utils\font\nanum-myeongjo\NanumMyeongjoExtraBold.ttf'
PIX = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11.ttf'
NAMES = ['MA', 'AL', 'TA', 'VA', 'HE', 'AN', 'MO', 'QP', 'CAP0', 'CAP1']


def decode(name):
    os.makedirs(TMP, exist_ok=True)
    src = os.path.join(ROOT, 'work', 'disc', 'DC_G_KAISETU%s.PVR' % name)
    shutil.copyfile(src, os.path.join(TMP, 'k%s.PVR' % name))
    subprocess.run([sys.executable, PYPVR, 'k%s.PVR' % name], cwd=TMP, capture_output=True)
    return Image.open(os.path.join(TMP, 'k%s.png' % name)).convert('RGBA')


def encode(im, name):
    im.save(os.path.join(TMP, 'n%s.png' % name))
    subprocess.run([sys.executable, PYPVR, 'n%s.png' % name, '-tw', '-1555'], cwd=TMP, capture_output=True)
    body = open(os.path.join(TMP, 'n%s.PVR' % name), 'rb').read()
    orig = open(os.path.join(ROOT, 'work', 'disc', 'DC_G_KAISETU%s.PVR' % name), 'rb').read()
    out = orig[:16] + body
    if len(out) != len(orig): raise SystemExit('%s 크기 %d≠%d' % (name, len(out), len(orig)))
    return out


def load_ko():
    ko = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'work', 'text', 'ko_gallery.tsv'), encoding='utf-8'), delimiter='\t'):
        ko[(r['pvr'], r['panel'])] = r['KO']
    return ko


def has_ctrl(px, y0):
    return any(px[x, y0 + 83][0] > 200 for x in range(16, 560))


def fit(d, text, room, extra=None, name=''):
    """20px 부터 줄여 room 안에 들어가는 글꼴(최소 15px) — 안 들어가면 빌드 에러"""
    for sz in range(20, 14, -1):
        f = ImageFont.truetype(SERIF, sz)
        if d.textlength(text, font=f) + (extra(f) if extra else 0) <= room: return f
    raise SystemExit('폭 넘침 %s «%s»' % (name, text))


def paint(im, ko, name):
    im = im.copy(); px = im.load(); d = ImageDraw.Draw(im)
    fs = ImageFont.truetype(SERIF, 20); fp = ImageFont.truetype(PIX, 12)
    for k in range(10):
        y0 = k * 96; t = ko.get((name, str(k + 1)))
        if t is None: continue
        ctrl = has_ctrl(px, y0)
        from collections import Counter                     # 바탕 = 안쪽에서 가장 흔한 색(글자 위 표본 피함)
        bg = Counter(px[xx, yy] for xx in range(8, 566, 7) for yy in range(y0 + 6, y0 + 90, 5)).most_common(1)[0][0]
        d.rectangle((6, y0 + 4, 568, y0 + 92), fill=bg)
        lines = t.split('／')
        segs = lines[0].split('　')
        d.text((16, y0 + 12), segs[0], font=fs, fill=(255, 255, 255, 255))
        rest = [s for s in segs[1:] if s]
        cv = [s for s in rest if s.startswith('CV')]
        main = '　'.join(s for s in rest if not s.startswith('CV')).replace('　', '  ')
        cvw = lambda f: (d.textlength(cv[0], font=f) + 16) if cv else 0
        f1 = fit(d, main, 565 - 88, extra=cvw, name='%s %d 1줄' % (name, k + 1))
        d.text((88, y0 + 12 + (20 - f1.size) // 2), main, font=f1, fill=(255, 255, 255, 255))
        if cv:
            w = d.textlength(cv[0], font=f1)
            d.text((565 - w, y0 + 12 + (20 - f1.size) // 2), cv[0], font=f1, fill=(255, 255, 255, 255))
        if len(lines) > 1:
            f2 = fit(d, lines[1], 565 - 88, name='%s %d 2줄' % (name, k + 1))
            d.text((88, y0 + 44 + (20 - f2.size) // 2), lines[1], font=f2, fill=(255, 255, 255, 255))
        if ctrl:
            d.text((18, y0 + 77), ko[('ALL', 'ctrl')].replace('　', '   '), font=fp, fill=(255, 255, 255, 255))
        for yy in range(y0 + 4, y0 + 93):                   # 1비트 알파(1555): 반투명 없이
            for xx in range(6, 569):
                r, g, b, a = px[xx, yy]; px[xx, yy] = (r, g, b, 255)
    return im


def main():
    ko = load_ko(); build = '--build' in sys.argv
    od = os.path.join(ROOT, 'work', 'shot', 'gallery'); os.makedirs(od, exist_ok=True)
    for name in NAMES:
        o = decode(name)
        if build:
            chk = encode(o, name)
            if chk != open(os.path.join(ROOT, 'work', 'disc', 'DC_G_KAISETU%s.PVR' % name), 'rb').read():
                raise SystemExit('%s 원본 재인코딩이 디스크와 다름 — 중단' % name)
        n = paint(o, ko, name)
        pv = Image.new('RGBA', (575 * 2 + 10, 960), (40, 40, 40, 255))
        pv.paste(o.crop((0, 0, 575, 960)), (0, 0)); pv.paste(n.crop((0, 0, 575, 960)), (585, 0))
        pv.save(os.path.join(od, name + '.png'))
        if build:
            os.makedirs(os.path.join(ROOT, 'work', 'build'), exist_ok=True)
            open(os.path.join(ROOT, 'work', 'build', 'DC_G_KAISETU%s.PVR' % name), 'wb').write(encode(n, name))
        print(name, 'OK')


if __name__ == '__main__':
    main()
