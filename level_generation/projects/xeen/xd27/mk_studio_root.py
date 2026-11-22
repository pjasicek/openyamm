#!/usr/bin/env python3
"""A studio check root for world: xeen indoor projects (after lane A7, 2026-11-20; XD-27 copy).

The indoor `oymap validate/build` of merge point 2 read monster numbers and descriptors only from the root's
engine tables, not from worlds/xeen/data_tables (A1 request). This root (cp -al assets_dev <root> first) gets engine
monster_data.txt, monster_descriptors.txt and items.txt with the world's rows appended, each written as a new file and renamed.
The built maps are the same; only the studio's checks need it. Usage: mk_studio_root.py <root>"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os, sys
R = _REPO_ROOT + '/assets_dev'
root = sys.argv[1]
for t in ['monster_data.txt', 'monster_descriptors.txt', 'items.txt']:
    eng = open(f'{R}/engine/data_tables/{t}', encoding='latin-1').read().rstrip('\n').split('\n')
    xe = [l for l in open(f'{R}/worlds/xeen/data_tables/{t}', encoding='latin-1').read().split('\n')
          if l.split('\t')[0].isdigit()]
    dst = f'{root}/engine/data_tables/{t}'
    open(dst + '.tmp', 'w', encoding='latin-1', newline='\n').write('\n'.join(eng + xe) + '\n')
    os.replace(dst + '.tmp', dst)
    print(t, len(xe), 'world rows')
