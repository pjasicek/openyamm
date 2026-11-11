#!/usr/bin/env python3
"""All three mummy rows get the cast clip: rows carry spells (Disease; Curse and Paralyze), the engine refuses a spellcaster binding without one (found in game: Petrified Mummy drew no model). Temp + rename; run under the flock."""
import os, re
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
a = s.index('# MM9 Mummy body (level_generation'); b = s.index('  skin: mummy_c', a)
blk = s[a:b]
blk = blk.replace("    run: Running\n", "    run: Running\n    cast: AttackRanged\n")
blk = blk.replace("      attack_ranged: {impact: 0.333, release: cast_hand}\n", "      attack_ranged: {impact: 0.333, release: cast_hand}\n      cast: {impact: 0.333, release: cast_hand}\n")
tmp = p + '.tmp_mummy'
open(tmp, 'w').write(s[:a] + blk + s[b:])
os.replace(tmp, p)
print('cast clip bound')
