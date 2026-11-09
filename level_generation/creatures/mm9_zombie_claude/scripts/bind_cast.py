#!/usr/bin/env python3
"""Rows 181, 182 cast spells: cast clip and event on all zombie descriptors (temp + rename; under the flock)."""
import os, re
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
a = s.index('- descriptor: MM9 Zombie A'); b = s.index('# Zombie (row 182)')
e = s.find('  skin: zombie_c', b)
blk = s[a:e]
blk = blk.replace('  animation:\n    run: Running', '  animation:\n    cast: AttackRanged\n    run: Running')
blk = blk.replace('      attack_ranged: {impact: 0.377, release: throw_hand}\n', '      attack_ranged: {impact: 0.377, release: throw_hand}\n      cast: {impact: 0.377, release: throw_hand}\n')
t = p + '.tmp.zombie'
open(t, 'w').write(s[:a] + blk + s[e:]); os.chmod(t, os.stat(p).st_mode); os.replace(t, p); print('ok')
