#!/usr/bin/env python3
"""Set PeasantF1's row (14) of the "MM9 reduction" ledger: re-read inside the shared flock, split the row on '|', replace the
After / LODs / Status / Project / Rollback columns, write a temp file and rename. Run as
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row14.py"""
import os
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
PRE = '| 14 | 2 town/animal | Peasant woman (PeasantF1) |'
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(PRE)]
assert len(hit) == 1, hit
c = lines[hit[0]].split('|')
assert len(c) == 12 and c[4].strip() == '`mm9_peasantf1.glb`', c
c[6] = ' 10,818 (-25.3 %; candidate e50: arms+hands 3,570 -> 1,990, skirt 1,358 -> 746 with its lining re-emitted 1,426 -> 814, dress 2,598 -> 1,898, legs 760 -> 608; head primitive 4,762 (face, neck, eyes, teeth, hood) exact) '
c[7] = ' 5,257 / 1,891 / 846 (installed 7,105 / 2,556 / 885) '
c[8] = (' ready for review 2026-11-04 (peasantf1-reduce-20261104): pose-aware half-edge collapse (PeasantF3 mpqem.py: chart guard at 12, '
        'texture guard over both tiers + region mask, W5 4, seam slides on the MPFB hands; every vertex an installed vertex) with the skirt '
        'lining carried as the skirt\'s exact twin per lining UV island and re-emitted from the cut skirt (rim kept); ladder e r50 p99 2.91 / '
        'max 15.0 mm (limits 5.38 / 26.9), IoU .997, SSIM .996; hands 0.6 (every finger), arm skin 0.45, skirt 0.55, shoes 0.6, hidden calves '
        '0.85, bodice 0.5; sleeves, collar, soles, lacing exact; hood kept whole (b50 at 10,496 cut it to 0.65 and its rolled hem shaded as a '
        'dark band in profile/from behind); UV audit 0 LOD0 faces off the charts; gates equal or better (collapse lower in every clip, robe/'
        'sleeve poke 0, arm/hand 0 f > 1 cm, lining numbers identical, jitter 2 = 2, detached/bone/winding/flat equal), see-through equal or '
        'lower except the ground-level view up the open skirt in Death/Dead (collar 896 -> 977, 100 -> 153 px) and 1-4 px single-view rises; '
        'LODs height 1.788 and floor = LOD0 in every clip (installed LOD3 floated up to 0.9 cm); face and hood pixel-identical both tiers; '
        'candidate export/mm9_peasantf1.glb (sha256 6c13a1e4d869), not installed ')
c[9] = ' `mm9_peasantf1_reduce_claude/` '
c[10] = ' `mm9_peasantf1_reduce_claude/before/mm9_peasantf1.glb` (sha256 e07f87e9b75c) '
lines[hit[0]] = '|'.join(c)
tmp = P.with_suffix('.md.tmp_peasantf1'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 14 written')
