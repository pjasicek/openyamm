#!/usr/bin/env python3
"""sector_areas.py output with the room each sector is (ids.lock.yml). Usage: named_sectors.py <sectors.txt> [<ids.lock.yml>]"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import re, sys
lock = sys.argv[2] if len(sys.argv) > 2 else _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/ids.lock.yml'
names = {}
sec = False
for l in open(lock):
    if l.startswith('sectors:'): sec = True; continue
    if sec and not l.startswith('  '): break
    if sec:
        k, v = l.strip().split(': '); names[int(v)] = k.replace('room:', '')
for l in open(sys.argv[1]):
    m = re.search(r'sector\s+(\d+)', l)
    print(l.rstrip() + ('  ' + names.get(int(m.group(1)), '?') if m else ''))
