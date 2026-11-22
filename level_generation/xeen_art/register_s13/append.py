#!/usr/bin/env python3
"""A6 session 13: append registry entries (a YAML list file) to source/textures.yml by temp + rename.
append.py <entries.yml>; refuses names already registered."""
import os, sys, yaml
REG = '/home/pjasicek/github/OpenYAMM/assets_dev/worlds/xeen/source/textures.yml'
text = open(REG).read()
have = {t['name'] for t in yaml.safe_load(text)['textures']}
new = open(sys.argv[1]).read()
names = [t['name'] for t in yaml.safe_load(new)]
dup = [n for n in names if n in have]
if dup:
    sys.exit(f'already registered: {dup}')
for n in names:
    assert os.path.exists(f'/home/pjasicek/github/OpenYAMM/assets_source/worlds/xeen/textures_x4/{n}.png'), n
text = text.rstrip('\n') + '\n' + new.rstrip('\n') + '\n'
total = len(yaml.safe_load(text)['textures'])
tmp = REG + '.a6tmp'
open(tmp, 'w').write(text)
os.chmod(tmp, 0o664)
os.replace(tmp, REG)
print('registered', names, 'total', total)
