#!/usr/bin/env python3
"""Refresh output/studio_cal/dd25/root from assets_dev: every file of assets_dev/worlds/xeen that changed since the
root was linked (other lanes install by rename) is linked again; worlds/xeen/data_tables is copied afresh (real copies,
never links) and house_rows.py writes DD-25's test house rows into the copy. The map's own files (xeen_dd25.*) and
the textures linked by hand stay. Nothing under assets_dev is written."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(_REPO_ROOT)
SRC = REPO / 'assets_dev/worlds/xeen'
ROOT = REPO / 'output/studio_cal/dd25/root'
DST = ROOT / 'worlds/xeen'


def main():
    relinked = 0
    for dirpath, dirnames, files in os.walk(SRC):
        rel = Path(dirpath).relative_to(SRC)
        if rel.parts[:1] == ('data_tables',):
            dirnames[:] = []
            continue
        (DST / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            if f.startswith('xeen_dd25.'):
                continue
            s, d = Path(dirpath) / f, DST / rel / f
            if d.exists() and os.stat(d).st_ino == os.stat(s).st_ino:
                continue
            if d.exists():
                d.unlink()
            os.link(s, d)
            relinked += 1
    tables = DST / 'data_tables'
    shutil.rmtree(tables)
    shutil.copytree(SRC / 'data_tables', tables)
    print('relinked', relinked, 'files; data_tables copied')
    subprocess.run([sys.executable, str(REPO / 'level_generation/projects/xeen/dd25/house_rows.py'), str(ROOT)], check=True)


if __name__ == '__main__':
    main()
