# -*- coding: utf-8 -*-
r"""대사 그림 한글 빌더(2026-10-30) — 받아쓴 띠(work/text/jp_strips.tsv)·창 나누기(msgsheet.layout)·번역(work/text/ko_0*.tsv)
  → 창마다 한글을 원본 색으로 그려 16×16 칸으로 쪼개 원래 칸 자리에 쓴다 → work/build/<파일>
  글꼴: 갈무리14 BDF(한글 15px 폭) — 칸 1~14행. ‼ ⁉ 💧 는 갈무리에 없어 «원본 게임 글자 칸»을 그대로(16px)
  색: 원본 대사 글자 = 칸 안 세로 위치별 4단계(0~7행 0xEB7F, 8~9행 0xDF3F, 10~15행 0xD2FF — STG1 대사 통계)
  배치: 줄마다 원문 그 줄 들여쓰기(안 맞으면 창 공통 들여쓰기 → 0), 줄은 원문이 쓰던 행에 차례로(빈 행 끼운 5줄 선택지 등 유지)
  문장부호 뒤 공백 1칸은 지운다(전 프로젝트 규칙)
  빌드 에러: 번역 없음 · 줄 수 초과 · 폭 초과 · 글꼴에 없는 글자
  «◆» = 원본 칸 그대로.  같은 내용 사본 파일(보스 STG0.022·STG2.031·STG3.015 = STG1.008)도 같이 씀.
  python tools/msgbuild.py [--preview]   (--preview: work/shot/build/<파일>.png 원본|한글)"""
import os, sys, csv, glob, struct
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile, msgsheet, jpcheck, msgocr
from bdf import Font

BDF = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri14.bdf'
ROWCOL = [0xEB7F] * 8 + [0xDF3F] * 2 + [0xD2FF] * 6
FROM_GAME = '‼⁉💧'
COPIES = {'STG1.008': ['STG0.022', 'STG2.031', 'STG3.015']}


class BuildError(Exception): pass


PUNCT = ',.!?:;)]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥‼⁉♫'
import re
_SQ = re.compile('([' + re.escape(PUNCT) + '])[ 　](?![ 　])')


def squeeze(t):
    """문장부호 뒤 공백 1칸 삭제(전 프로젝트 규칙 feedback_no_space_after_punct)"""
    return _SQ.sub(r'\1', t)


def key_of(lines):
    return '／'.join(t.strip('　') for t in lines if t.strip('　'))


def load_ko():
    src = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'my files', 'tsv', 'gb2_*.tsv'))):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'): src[r['번호']] = r['JP']
    ko = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'work', 'text', 'ko_0*.tsv'))):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'): ko[src[r['번호']]] = r['KO']
    return ko


class Painter:
    def __init__(self):
        self.f = Font(BDF)
        dic, _ = msgocr.build()
        self.game = {}                                   # 원본 글자 칸(기호) — 글자 → 16×16 잉크
        for b, ch in dic.items():
            if ch in FROM_GAME and ch not in self.game:
                t = struct.unpack('<256H', b)
                self.game[ch] = [(x, y) for y in range(16) for x in range(16) if t[msgtile.addr(x, y)]]

    def line(self, text):
        """→ (잉크 [(x,y)], 폭) — y 는 0~15(한 줄 = 한 칸 높이)"""
        pts = []; x = 0
        for ch in text:
            if ch in self.game:
                pts += [(x + a, b) for a, b in self.game[ch]]; x += 16; continue
            g = self.f.g.get(ord(ch))
            if g is None: raise BuildError('글꼴에 없는 글자 %r' % ch)
            p, w = self.f.draw(ch, x, -3)
            pts += p; x = w
        return pts, x


def paint_box(P, T, s, R, C, lines_src, ko, tag):
    """칸 목록 T 의 s 부터 R×C 창을 한글로. lines_src = 원문 줄(창 폭으로 자른 것)"""
    if ko == '◆': return
    used = [i for i, t in enumerate(lines_src) if t.strip('　')]
    lead = min((len(t) - len(t.lstrip('　')) for t in lines_src if t.strip('　')), default=0)
    kl = ko.split('／')
    if len(kl) > R: raise BuildError('%s 줄 수 %d>%d' % (tag, len(kl), R))
    rows = used[:len(kl)] if len(kl) <= len(used) else list(range(used[0] if used else 0, (used[0] if used else 0) + len(kl)))
    if rows and rows[-1] >= R: rows = list(range(R - len(kl), R))
    img = [[0] * (C * 16) for _ in range(R * 16)]
    for r, text in zip(rows, kl):
        text = squeeze(text)
        pts, w = P.line(text)
        ind = len(lines_src[r]) - len(lines_src[r].lstrip('　')) if lines_src[r].strip('　') else lead
        x0 = next((i * 16 for i in (ind, lead, 0) if w <= (C - i) * 16), 0)   # 원문 그 줄 들여쓰기 → 창 공통 → 0
        if x0 + w > C * 16: raise BuildError('%s 폭 %dpx > %dpx «%s»' % (tag, w, C * 16, text))
        for x, y in pts:
            if 0 <= y < 16 and 0 <= x0 + x < C * 16: img[r * 16 + y][x0 + x] = ROWCOL[y]
    for c in range(C):
        for rr in range(R):
            g = s + c * R + (R - 1 - rr)
            t = [0] * 256
            for y in range(16):
                for x in range(16):
                    t[msgtile.addr(x, y)] = img[rr * 16 + y][c * 16 + x]
            T[g] = t


def build(preview=False):
    sys.stdout.reconfigure(encoding='utf-8')
    P = Painter(); ko = load_ko(); lay = msgsheet.layout()
    files = {}                                           # 파일 → (원본 바이트, 머리 길이, 칸 목록)
    errs = []; nbox = 0
    for r in jpcheck.load():
        nm, k = r['file'], int(r['strip']); f, _, a = nm.partition('@'); a = int(a or 0)
        if f not in files:
            d = open(os.path.join(ROOT, 'work', 'disc', f), 'rb').read()
            hl = 0 if len(d) % 512 == 0 else 32
            T = [list(struct.unpack_from('<256H', d, hl + i * 512)) for i in range((len(d) - hl) // 512)]
            files[f] = (d, hl, T)
        T = files[f][2]
        R, C = lay[nm][k]; s = a + sum(rr * cc for rr, cc in lay[nm][:k])
        rows = [t + '　' * (C - len(t)) for t in r['rows'].split('／')]
        cuts = [0] + [int(x) for x in r['cuts'].split(',') if x] + [C]
        for b, (c0, c1) in enumerate(zip(cuts, cuts[1:])):
            src = [t[c0:c1] for t in rows]; key = key_of(src)
            if not key: continue
            if key not in ko: errs.append('번역 없음 %s %d.%d «%s»' % (nm, k, b, key)); continue
            try:
                paint_box(P, T, s + c0 * R, R, c1 - c0, src, ko[key], '%s %d.%d' % (nm, k, b)); nbox += 1
            except BuildError as e: errs.append(str(e))
    if errs:
        print('\n'.join(errs)); raise SystemExit('빌드 에러 %d' % len(errs))
    out = os.path.join(ROOT, 'work', 'build'); os.makedirs(out, exist_ok=True)
    for f, (d, hl, T) in files.items():
        nd = bytearray(d[:hl]) + b''.join(struct.pack('<256H', *t) for t in T) + d[hl + len(T) * 512:]
        assert len(nd) == len(d)
        for name in [f] + COPIES.get(f, []):
            if name != f: assert open(os.path.join(ROOT, 'work', 'disc', name), 'rb').read() == d, name
            open(os.path.join(out, name), 'wb').write(nd)
    print('창', nbox, '파일', len(files), '(+사본', sum(len(v) for k, v in COPIES.items() if k in files), ') → work/build')
    if preview: make_preview(files, lay)


def make_preview(files, lay):
    from PIL import Image
    od = os.path.join(ROOT, 'work', 'shot', 'build'); os.makedirs(od, exist_ok=True)
    names = {}
    for nm in lay:
        f = nm.partition('@')[0]
        if f in files: names.setdefault(f, []).append(nm)
    for f, nms in names.items():
        d, hl, T = files[f]
        To = [list(struct.unpack_from('<256H', d, hl + i * 512)) for i in range(len(T))]
        ims = []
        for nm in nms:
            a = int(nm.partition('@')[2] or 0); s = a
            for R, C in lay[nm]:
                pair = []
                for TT in (To, T):
                    im = Image.new('RGB', (C * 16, R * 16), (16, 16, 48))
                    for g in range(R * C):
                        c, rr = g // R, R - 1 - g % R
                        t = TT[s + g]
                        for y in range(16):
                            for x in range(16):
                                v = t[msgtile.addr(x, y)]
                                if v: im.putpixel((c * 16 + x, rr * 16 + y), ((v >> 8 & 15) * 17, (v >> 4 & 15) * 17, (v & 15) * 17))
                    pair.append(im)
                w = pair[0].width; row = Image.new('RGB', (w * 2 + 8, pair[0].height + 4), (60, 60, 60))
                row.paste(pair[0], (0, 0)); row.paste(pair[1], (w + 8, 0)); ims.append(row); s += R * C
        W = max(i.width for i in ims); sh = Image.new('RGB', (W, sum(i.height for i in ims)), (30, 30, 30)); y = 0
        for i in ims: sh.paste(i, (0, y)); y += i.height
        sh.resize((sh.width * 2, sh.height * 2), Image.NEAREST).save(os.path.join(od, f.replace('.', '_') + '.png'))


if __name__ == '__main__':
    build('--preview' in sys.argv)
