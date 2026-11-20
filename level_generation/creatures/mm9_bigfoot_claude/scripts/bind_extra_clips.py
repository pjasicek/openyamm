#!/usr/bin/env python3
"""Run 2: MM9's remaining Bigfoot clips as script_clips on the three Bigfoot descriptors (temp + rename; run from the repo root
under the flock claude_shared/locks/mm9_actors_yml.lock). Idempotent."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
ADD = "    walk_fidget: WalkFidget\n    backpedal: Backpedal\n    backpedal_run: BackpedalRun\n    jumping_down: JumpingDown\n    lying_down: LyingDown\n"
n = 0
for skin in ('bf_a', 'bf_b', 'bf_c'):
    old = f"    death2: Death2\n  skin: {skin}\n"
    assert s.count(old) == 1, skin
    if f"    lying_down: LyingDown\n  skin: {skin}\n" in s:
        continue
    s = s.replace(old, f"    death2: Death2\n{ADD}  skin: {skin}\n"); n += 1
tmp = p + '.tmp.bigfoot'
open(tmp, 'w').write(s); os.chmod(tmp, os.stat(p).st_mode); os.replace(tmp, p); print('script clips added to', n, 'descriptors')
