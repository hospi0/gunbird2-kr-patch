# -*- coding: utf-8 -*-
"""번역 검사(2026-10-30) — work/text/ko_*.tsv(번호·KO) ↔ my files/tsv/gb2_*.tsv(번호·위치·줄x칸·JP)
  줄 수 ≤ R, 줄마다 칸 ≤ C(한글·전각 1칸, 반각 영숫자·기호 0.5칸, 공백 0.5칸 — 그림으로 다시 그리므로 반각은 반 칸),
  반각 «/» 금지(줄바꿈은 ／), 가나·한자 남음 금지, 원문 ‼ ⁉ ♥ ♫ 💧 개수 유지(경고).
  python tools/kocheck.py → 어긋난 줄 목록"""
import os, sys, csv, glob, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KANA = re.compile(r'[぀-ヺー-ヿ一-鿿]')   # ・(30FB) 는 허용


FONT = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri14.ttf'
_F = None


def width(t):
    """갈무리14(15px) 로 그린 픽셀 폭 ÷ 16 = 칸 수(창 = 16px 칸 C 개, 창을 그림으로 다시 그림)"""
    global _F
    if _F is None:
        from PIL import ImageFont
        _F = ImageFont.truetype(FONT, 15)
    return _F.getlength(t) / 16


def load_src():
    src = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'my files', 'tsv', 'gb2_*.tsv'))):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
            R, C = (int(v) for v in r['줄x칸'].split('x')); src[r['번호']] = (R, C, r['JP'])
    return src


def load_ko():
    ko = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'work', 'text', 'ko_0*.tsv'))):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
            ko[r['번호']] = r['KO']
    return ko


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    src, ko = load_src(), load_ko(); bad = 0
    for k, t in sorted(ko.items()):
        R, C, jp = src[k]; err = []
        if t == '◆': continue                          # 원본 칸 그대로(글자 아닌 조각)
        if '/' in t: err.append('반각 / 있음')
        if KANA.search(t): err.append('가나·한자 남음')
        lines = t.split('／')
        if len(lines) > R: err.append('줄 %d>%d' % (len(lines), R))
        for i, l in enumerate(lines):
            if width(l) > C: err.append('%d줄 폭 %.1f>%d «%s»' % (i + 1, width(l), C, l))
        for s in '‼⁉♥♫💧':
            if jp.count(s) != t.count(s): err.append('%s 개수 %d→%d' % (s, jp.count(s), t.count(s)))
        if err: bad += 1; print(k, '%dx%d' % (R, C), jp, '\n   ', t, '\n   ', ' / '.join(err))
    print('번역', len(ko), '/', len(src), '어긋남', bad)


if __name__ == '__main__':
    main()
