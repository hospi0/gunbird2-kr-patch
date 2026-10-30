# -*- coding: utf-8 -*-
"""GD-ROM (cue/bin, MODE1/2352) 판독 유틸 - 읽기 전용.

(2026-10-30 아스카 tools/gdi.py 를 건버드 2 용으로 옮김)
트랙 배치(GD-ROM 3트랙): track1 MODE1 SD · track2 AUDIO SD · track3 MODE1 HD(LBA 45000~, ISO9660 PVD @ 45016)
"""
import os, struct

ROM_DIR = r"C:\claude\roms\dc\Gunbird 2 (Japan)"
BASE = "Gunbird 2 (Japan)"

SEC = 2352
HDR = 16
USER = 2048

def track_path(n):
    return os.path.join(ROM_DIR, "%s (Track %d).bin" % (BASE, n))

class Track:
    def __init__(self, num, start_lba, file_first_sector=0):
        self.num = num
        self.path = track_path(num)
        self.start_lba = start_lba
        self.skip = file_first_sector
        self.sectors = os.path.getsize(self.path) // SEC - file_first_sector
        self.f = open(self.path, 'rb')
    def raw(self, lba, count=1):
        self.f.seek((lba - self.start_lba + self.skip) * SEC)
        return self.f.read(count * SEC)
    def user(self, lba, count=1):
        d = self.raw(lba, count)
        return b''.join(d[i*SEC+HDR:i*SEC+HDR+USER] for i in range(count))
    def contains(self, lba):
        return self.start_lba <= lba < self.start_lba + self.sectors

class Disc:
    def __init__(self):
        self.tracks = [Track(1, 0), Track(3, 45000)]
    def track_of(self, lba):
        for t in self.tracks:
            if t.contains(lba):
                return t
        raise KeyError("LBA %d 는 어떤 데이터 트랙에도 없다" % lba)
    def read(self, lba, nbytes):
        t = self.track_of(lba)
        n = (nbytes + USER - 1) // USER
        avail = t.start_lba + t.sectors - lba
        if n > avail:
            raise ValueError("LBA %d 에서 %d 섹터 요청, 트랙%d 잔여 %d" % (lba, n, t.num, avail))
        return t.user(lba, n)[:nbytes]

def msf_of(raw):
    bcd = lambda b: (b >> 4) * 10 + (b & 15)
    return bcd(raw[12]) * 60 * 75 + bcd(raw[13]) * 75 + bcd(raw[14]) - 150
