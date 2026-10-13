# -*- coding: utf-8 -*-
r"""트랙 1 빌드: 원본 트랙 1 사본에 work/build/ 파일을 제자리로 쓰고 MODE1 EDC/ECC 재계산.
  ★파일 크기는 원본과 똑같아야 한다(디렉터리·LBA 불변). 다르면 멈춤.
  출력: dist/build/ (트랙 1 패치본 + 원본 트랙 2 + cue 복사)   --install 이면 F: 설치 폴더 트랙 1 도 덮어씀.
  python tools/discbuild.py [--install]
"""
import os, shutil, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import disc
from cdrom_ecc import recalc_sector

SRC_DIR = os.path.dirname(disc.ROM)
NAME = 'Magical Night Dreams - Cotton 2 (Japan)'
OUT_DIR = os.path.join(ROOT, 'dist', 'build')
F_DIR = r'F:\hospi\roms\ss roms\Magical Night Dreams - Cotton 2 (Japan)'
BUILD = os.path.join(ROOT, 'work', 'build')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    fs = {n: (l, s) for n, l, s in disc.Disc().walk()}
    files = sorted(os.listdir(BUILD))
    for n in files:
        data = open(os.path.join(BUILD, n), 'rb').read()
        if n not in fs or fs[n][1] != len(data):
            sys.exit('⛔ %s 크기 다름/없음 (%s vs %d)' % (n, fs.get(n), len(data)))
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in (' (Track 2).bin', '.cue'):
        shutil.copyfile(os.path.join(SRC_DIR, NAME + ext), os.path.join(OUT_DIR, NAME + ext))
    t1 = os.path.join(OUT_DIR, NAME + ' (Track 1).bin')
    shutil.copyfile(disc.ROM, t1)
    with open(t1, 'r+b') as f:
        for n in files:
            data = open(os.path.join(BUILD, n), 'rb').read(); lba = fs[n][0]
            nsec = (len(data) + 2047) // 2048; changed = 0
            for i in range(nsec):
                f.seek((lba + i) * 2352); sec = bytearray(f.read(2352))
                chunk = data[i * 2048:(i + 1) * 2048]
                if sec[16:16 + len(chunk)] == chunk:
                    continue
                sec[16:16 + len(chunk)] = chunk
                f.seek((lba + i) * 2352); f.write(recalc_sector(bytes(sec))); changed += 1
            print('%-14s LBA %6d · 섹터 %d 중 %d 바뀜' % (n, lba, nsec, changed))
    # 되읽기 검산
    d2 = disc.Disc(t1)
    for n in files:
        l, s = fs[n]
        assert d2.read(l, s) == open(os.path.join(BUILD, n), 'rb').read(), n
    m = md5(t1)
    print('트랙 1 md5', m, '(원본', md5(disc.ROM) + ')')
    if '--install' in sys.argv:
        dst = os.path.join(F_DIR, NAME + ' (Track 1).bin')
        shutil.copyfile(t1, dst)
        print('F: 설치', md5(dst) == m and '✅' or '⛔ md5 불일치', dst)


if __name__ == '__main__':
    main()
