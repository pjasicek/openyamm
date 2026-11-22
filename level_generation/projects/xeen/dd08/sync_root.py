#!/usr/bin/env python3
"""Refresh output/studio_cal/dd08/root from assets_dev: hard links for every file except the map's own (xeen_dd08.*)
and worlds/xeen/data_tables/ (real copies). Prints what it changed."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import filecmp
import os
import shutil
from pathlib import Path

A = Path(_REPO_ROOT + '/assets_dev')
R = Path(_REPO_ROOT + '/output/studio_cal/dd08/root')
DT = Path('worlds/xeen/data_tables')
n = 0
for dirpath, dirs, files in os.walk(A):
    rel = Path(dirpath).relative_to(A)
    (R / rel).mkdir(parents=True, exist_ok=True)
    for f in files:
        src, dst = A / rel / f, R / rel / f
        if f.startswith('xeen_dd08.'):
            continue
        if rel == DT or DT in rel.parents:
            if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
                shutil.copy2(src, dst)
                print('copy', rel / f)
                n += 1
            continue
        if dst.exists():
            if os.stat(src).st_ino == os.stat(dst).st_ino:
                continue
            dst.unlink()
        os.link(src, dst)
        print('link', rel / f)
        n += 1
print(n, 'files refreshed')
