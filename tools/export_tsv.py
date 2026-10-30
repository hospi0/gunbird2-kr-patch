# -*- coding: utf-8 -*-
"""대사 창 단위 원문 → 번역 TSV (2026-10-30)
  입력: work/text/jp_strips.tsv (띠별 받아쓰기, tools/jpcheck.py 검산 통과분)
  출력: work/text/jp_boxes.tsv — 창마다 파일·띠·창·줄 수·시작 열·폭·원문(줄 = ／, 앞 빈칸 그대로)
        my files/tsv/gb2_NNN.tsv — 번호·위치·줄×칸·JP·KO (같은 원문은 한 줄, 줄 앞뒤 빈칸 뺌) — UTF-8 18KB 단위
  줄×칸 = 그 창에 한글을 넣을 수 있는 크기(글자 칸 16px 고정, 창 폭 = 원문 가장 긴 줄)
  python tools/export_tsv.py"""
import os, sys, csv, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgpat, jpcheck
SPLIT = 18 * 1024


def boxes():
    out = []; pats = {}
    for r in jpcheck.load():
        nm, k = r['file'], int(r['strip'])
        if nm not in pats: pats[nm] = msgpat.pattern(nm)
        R, C, _ = pats[nm][k]
        rows = [t + '　' * (C - len(t)) for t in r['rows'].split('／')]
        cuts = [0] + [int(x) for x in r['cuts'].split(',') if x] + [C]
        for b, (a, e) in enumerate(zip(cuts, cuts[1:])):
            lines = [t[a:e].rstrip('　') for t in rows]
            out.append({'file': nm, 'strip': k, 'box': b, 'R': R, 'col': a, 'C': e - a, 'lines': lines})
    return out


def write_split(folder, stem, head, lines):
    os.makedirs(folder, exist_ok=True)
    chunks = []; cur = []; size = len(head.encode('utf-8'))
    for ln in lines:
        n = len(ln.encode('utf-8'))
        if cur and size + n > SPLIT: chunks.append(cur); cur = []; size = len(head.encode('utf-8'))
        cur.append(ln); size += n
    if cur: chunks.append(cur)
    for i, c in enumerate(chunks, 1):
        with open(os.path.join(folder, '%s_%03d.tsv' % (stem, i)), 'w', encoding='utf-8', newline='\n') as w:
            w.write(head + ''.join(c))
    return len(chunks)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    bx = boxes()
    with open(os.path.join(ROOT, 'work', 'text', 'jp_boxes.tsv'), 'w', encoding='utf-8', newline='\n') as w:
        w.write('file\tstrip\tbox\tR\tcol\tC\tJP\n')
        for b in bx:
            w.write('%s\t%d\t%d\t%d\t%d\t%d\t%s\n' % (b['file'], b['strip'], b['box'], b['R'], b['col'], b['C'], '／'.join(b['lines'])))
    uniq = collections.OrderedDict()
    for b in bx:
        jp = '／'.join(t.strip('　') for t in b['lines'] if t.strip('　'))
        if not jp: continue
        u = uniq.setdefault(jp, {'at': [], 'R': b['R'], 'C': b['C']})
        u['at'].append('%s:%d.%d' % (b['file'].replace('DEMOMSG', ''), b['strip'], b['box']))
        u['C'] = min(u['C'], b['C'])
    ko = {}                                               # 번역(work/text/ko_0*.tsv) 이 있으면 KO 열에
    for f in sorted(glob.glob(os.path.join(ROOT, 'work', 'text', 'ko_0*.tsv'))):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'): ko[r['번호']] = r['KO']
    lines = ['%04d\t%s\t%dx%d\t%s\t%s\n' % (i, ','.join(u['at']), u['R'], u['C'], jp, ko.get('%04d' % i, '')) for i, (jp, u) in enumerate(uniq.items(), 1)]
    for old in glob.glob(os.path.join(ROOT, 'my files', 'tsv', 'gb2_*.tsv')): os.remove(old)
    nf = write_split(os.path.join(ROOT, 'my files', 'tsv'), 'gb2', '번호\t위치\t줄x칸\tJP\tKO\n', lines)
    print('창', len(bx), '고유 원문', len(uniq), '글자', sum(len(j.replace('／', '')) for j in uniq), 'TSV', nf, '개')


if __name__ == '__main__':
    main()
