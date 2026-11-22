#!/usr/bin/env python3
"""P3's scree check (D-58 P3 Q1: a drop into the scree is a real fall): in each playtest_scree log under the given run
folder, the four HP logged before the drop are 140 and the four logged after it are all alive and at least one lower.
Usage: check_scree.py <run folder>"""
import re
import sys
from pathlib import Path

bad = 0
for log in sorted(Path(sys.argv[1]).glob('playtest_scree_*.log')):
    v = [int(x) for x in re.findall(r'member_points\.health expected=\[[^]]*\] actual=(\d+)', log.read_text())]
    if len(v) != 8:
        print(f'{log.name}: {len(v)} HP values (expected 8): FAIL'); bad += 1; continue
    before, after = v[:4], v[4:]
    ok = before == [140] * 4 and all(h >= 1 for h in after) and min(after) < 140
    bad += not ok
    print(f"{log.name}: before {before} after the drop {after} lost {[b - a for b, a in zip(before, after)]}: "
          f"{'ok' if ok else 'FAIL'}")
sys.exit(1 if bad else 0)
