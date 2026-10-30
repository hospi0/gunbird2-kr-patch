# -*- coding: utf-8 -*-
r"""건버드 2 디스크 빌드(2026-10-30) — work/build/ 의 바뀐 파일을 원본 Track 3(HD, LBA 45000~) 사본에 «제자리»로 쓰고 EDC/ECC 재계산.
  바뀐 파일은 모두 원본과 크기가 같아야 함(다르면 중단 — 옮기기는 아직 안 함).
  출력: dist/build/Gunbird 2 (Japan)/ (Track 3 패치본 + 원본 Track 1·2·cue 복사), 되읽어 바이트 검산.
  python tools/discbuild.py                → 미리보기(쓸 파일·크기 검사만)
  python tools/discbuild.py --write [--install]   (--install = F:\hospi\roms\dc roms\Gunbird 2 (Japan)\ 의 Track 3 덮어쓰기)"""
import os, sys, shutil, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import iso_extract as ie
from discwrite import TrackWriter

NAME = 'Gunbird 2 (Japan)'
SRC = os.path.join(r'C:\claude\roms\dc', NAME)
OUT = os.path.join(ROOT, 'dist', 'build', NAME)
F_DIR = os.path.join(r'F:\hospi\roms\dc roms', NAME)
T3 = NAME + ' (Track 3).bin'


def plan():
    ents = {full.lstrip('/').upper(): (lba, size) for full, lba, size, fl in ie.walk() if not fl & 2}
    ch = []
    for f in sorted(os.listdir(os.path.join(ROOT, 'work', 'build'))):
        p = os.path.join(ROOT, 'work', 'build', f)
        if not os.path.isfile(p): continue
        if f.upper() not in ents: raise SystemExit('디스크에 없는 파일 %s' % f)
        lba, size = ents[f.upper()]; d = open(p, 'rb').read()
        if len(d) != size: raise SystemExit('%s 크기 %d≠%d (옮기기 미지원)' % (f, len(d), size))
        orig = ie.D.read(lba, size)
        if d != orig: ch.append((f, lba, d))
    return ch


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ch = plan()
    print('바뀐 파일', len(ch), '총', sum(len(d) for _, _, d in ch), 'B')
    if '--write' not in sys.argv: return
    os.makedirs(OUT, exist_ok=True)
    for x in os.listdir(SRC):
        if os.path.isfile(os.path.join(SRC, x)) and x != T3: shutil.copyfile(os.path.join(SRC, x), os.path.join(OUT, x))
    t3 = os.path.join(OUT, T3); shutil.copyfile(os.path.join(SRC, T3), t3)
    w = TrackWriter(t3, 45000)
    for f, lba, d in ch: w.write_user(lba, 0, d)
    print('ECC 다시 계산한 섹터', w.close())
    # 되읽기 검산
    r = TrackWriter(t3, 45000)
    for f, lba, d in ch:
        if r.read_user(lba, 0, len(d)) != d: raise SystemExit('되읽기 불일치 ' + f)
    r.f.close()
    md5 = hashlib.md5(open(t3, 'rb').read()).hexdigest()
    print('✅Track 3 md5', md5, '→', t3)
    if '--install' in sys.argv:
        dst = os.path.join(F_DIR, T3)
        shutil.copyfile(t3, dst)
        print('F: 설치', dst, hashlib.md5(open(dst, 'rb').read()).hexdigest())


if __name__ == '__main__':
    main()
