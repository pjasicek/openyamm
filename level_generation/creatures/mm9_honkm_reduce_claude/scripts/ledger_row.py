#!/usr/bin/env python3
"""Replace the Honk male's row (81) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 81 | 1 monster | Honk (male) |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 81 | 1 monster | Honk (male) |'
ROW = (KEY + ' `mm9_honkm.glb` | 8,038 | 6,986 (-13.1 %; candidate n r60: body set 3,087 -> 2,989, head+hands 4,951 -> 3,997; '
       'face skin/beard/ears/neck, eyes/mouth, collar, medallion, linings, robe tube and boots exact) | 3,491 / 1,257 / 417 | '
       'ready for install (2026-11-04; orchestrator pre-screen: l r60 6,864 with the medallion kept exact): pose-aware half-edge '
       'collapse (Highwayman/Lesser Demon mpqem.py: every vertex an installed vertex, texture guard on body base+mask and all three '
       'head tiers, seam slides on the hands with a UV-chart guard); reduction_uv_audit LOD0 0 escaping; hands 0.6, hair shell 0.6, '
       'sleeves 0.85, robe torso 0.6; ladder p99 3.09 / max 14.5 mm, IoU .999, SSIM .994; protected share ~60 %; gates equal or '
       'better (collapse 41,097 -> 38,694 face-frames, robe/detached/forearm poke identical, jitter 0 -> 0, LOD heights and floor '
       'equal to LOD0) except Hit R forearm in body 2.5 -> 2.9 cm and finger stretch p99 | `mm9_honkm_reduce_claude/` | '
       '`mm9_honkm_reduce_claude/before/mm9_honkm.glb` (sha256 4a5c84880d03) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 81 updated')
