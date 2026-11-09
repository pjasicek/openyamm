#!/usr/bin/env python3
"""The Ghoul row casts: `cast: AttackRanged` belongs in the animation block, as on the Mummy (in clips: the validator refuses it). Fixes the three ghoul bindings (temp + rename; run under the flock, from the repo root)."""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
n = 0
def fix(m):
    global n
    b = m.group(0).replace('    attack_ranged: AttackRanged\n    cast: AttackRanged\n', '    attack_ranged: AttackRanged\n')
    if '    sockets:\n      throw_hand' in b and '    cast: AttackRanged\n    sockets:' not in b:
        b = b.replace('    sockets:\n      throw_hand', '    cast: AttackRanged\n    sockets:\n      throw_hand'); n += 1
    return b
s2 = re.sub(r'- descriptor: MM9 Ghoul [ABC]\n(?:(?!- descriptor:).*\n)*', fix, s)
if s2 == s: sys.exit('nothing to change')
tmp = p + '.tmp.ghoul'
open(tmp, 'w').write(s2)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('cast moved on', n)
