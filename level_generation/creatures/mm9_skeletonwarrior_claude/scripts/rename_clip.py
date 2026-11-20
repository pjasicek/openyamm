#!/usr/bin/env python3
"""Rename clips in a GLB, nothing else changes (dropped-clip pass, 2026-10-31: finger_keys.py gives the throw hand only to a clip
named AttackRanged, so RAttack1OLD is built under that name and renamed AttackRangedOld). Usage: rename_clip.py <in> <out> OLD=NEW ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
src, dst, *pairs = sys.argv[1:]
g = Glb(Path(src)); ren = dict(p.split('=', 1) for p in pairs)
for a in g.json.get('animations', []):
    a['name'] = ren.get(a['name'], a['name'])
g.write(Path(dst)); print('RENAMED', ren, dst)
