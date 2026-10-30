# -*- coding: utf-8 -*-
"""CHR(16비트 화소 16×16 칸 묶음) 훑어보기 — 대사 그림과 같은 칸 배치(tools/msgtile.addr) 가정, 색 ARGB1555
   python tools/chrview.py 파일 [시작칸] [개수] [열] [머리B] → work/shot/chr/<파일>_<시작>.png  (STG?.0xx·END*.CHR 는 머리 32)"""
import os, sys, struct
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import msgtile
nm = sys.argv[1]; st = int(sys.argv[2]) if len(sys.argv) > 2 else 0
n = int(sys.argv[3]) if len(sys.argv) > 3 else 1024; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 64
d = open(os.path.join(ROOT, 'work', 'disc', nm), 'rb').read()[int(sys.argv[5]) if len(sys.argv) > 5 else 0:]
P = struct.unpack('<%dH' % (len(d) // 2), d)
nt = len(P) // 256; n = min(n, nt - st)
im = Image.new('RGB', (cols * 16, (n + cols - 1) // cols * 16))
A = [msgtile.addr(x, y) for y in range(16) for x in range(16)]
for g in range(n):
    t = P[(st + g) * 256:(st + g + 1) * 256]
    for i, a in enumerate(A):
        v = t[a]; x, y = i % 16, i // 16
        im.putpixel((g % cols * 16 + x, g // cols * 16 + y), ((v >> 10 & 31) * 8, (v >> 5 & 31) * 8, (v & 31) * 8))
os.makedirs(os.path.join(ROOT, 'work', 'shot', 'chr'), exist_ok=True)
im.save(os.path.join(ROOT, 'work', 'shot', 'chr', '%s_%d.png' % (nm, st)))
print(nm, '칸', nt)
