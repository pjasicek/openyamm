#!/usr/bin/env python3
"""P2's fall check (D-54's shape for a same-map fall, whose damage is random per member): in each fall log under the
given run folder, the four HP logged 0.5 s after the landing equal the four logged 20 s later, every member alive and
hurt no more than the HP set before the fall.   Usage: check_falls.py <run folder>"""
import re
import sys
from pathlib import Path

bad = 0
for log in sorted(Path(sys.argv[1]).glob('playtest_fall_*.log')):
    v = [int(x) for x in re.findall(r'member_points\.health expected=\[[^]]*\] actual=(\d+)', log.read_text())]
    if len(v) != 12:
        print(f'{log.name}: {len(v)} HP values (expected 12): FAIL'); bad += 1; continue
    full, land, later = v[0:4], v[4:8], v[8:12]
    ok = land == later and all(1 <= h <= f for h, f in zip(land, full))
    bad += not ok
    print(f"{log.name}: full {full} landing {land} after 20 s {later} lost {[f - h for f, h in zip(full, land)]}: "
          f"{'ok' if ok else 'FAIL'}")
sys.exit(1 if bad else 0)
