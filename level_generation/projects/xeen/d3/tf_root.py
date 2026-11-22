#!/usr/bin/env python3
"""D3's town_feel root (A5, 2026-11-20): a read-only view of assets_dev (symlinks) whose world house_data.txt holds the
world's rows plus D3's houses typed from A4's planned d3.yml (`kind`), only for town_feel's measure, never installed:
A4 writes the real rows when d3.yml stops being planned. Usage: tf_root.py <out dir> (the dir must not exist)."""
import os
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
A = os.path.join(ROOT, 'assets_dev')
out = sys.argv[1]
assert not os.path.exists(out), out
TYPE = {'weapon_shop': 'Weapon Shop', 'armor_shop': 'Armor Shop', 'magic_shop': 'Magic Shop',
        'alchemist': 'Alchemist', 'temple': 'Temple', 'tavern': 'Tavern', 'training': 'Training',
        'stables': 'Stables', 'boats': 'Boats', 'mind_guild': 'Mind Guild', 'spirit_guild': 'Spirit Guild',
        'light_guild': 'Light Guild', 'dark_guild': 'Dark Guild', 'residence': 'House'}
os.makedirs(os.path.join(out, 'worlds/xeen/data_tables'))
for n in os.listdir(A):
    if n != 'worlds':
        os.symlink(os.path.join(A, n), os.path.join(out, n))
for n in os.listdir(os.path.join(A, 'worlds')):
    if n != 'xeen':
        os.symlink(os.path.join(A, 'worlds', n), os.path.join(out, 'worlds', n))
B = os.path.join(ROOT, 'output/studio_cal/d3/build_w')
for n in os.listdir(os.path.join(A, 'worlds/xeen')):
    if n not in ('data_tables', 'maps', 'events'):
        os.symlink(os.path.join(A, 'worlds/xeen', n), os.path.join(out, 'worlds/xeen', n))
# the maps and the map scripts: assets_dev's, and D3's build in place of an installed D3
os.makedirs(os.path.join(out, 'worlds/xeen/maps'))
for n in os.listdir(os.path.join(A, 'worlds/xeen/maps')):
    if not n.startswith('xeen_d3.'):
        os.symlink(os.path.join(A, 'worlds/xeen/maps', n), os.path.join(out, 'worlds/xeen/maps', n))
for n in ('xeen_d3.odm', 'xeen_d3.scene.yml'):
    os.link(os.path.join(B, n), os.path.join(out, 'worlds/xeen/maps', n))     # the game reads no symlinked file
os.makedirs(os.path.join(out, 'worlds/xeen/events/maps'))
for n in os.listdir(os.path.join(A, 'worlds/xeen/events')):
    if n != 'maps':
        os.symlink(os.path.join(A, 'worlds/xeen/events', n), os.path.join(out, 'worlds/xeen/events', n))
for n in os.listdir(os.path.join(A, 'worlds/xeen/events/maps')):
    if n != 'xeen_d3.lua':
        os.symlink(os.path.join(A, 'worlds/xeen/events/maps', n), os.path.join(out, 'worlds/xeen/events/maps', n))
os.link(os.path.join(B, 'xeen_d3.lua'), os.path.join(out, 'worlds/xeen/events/maps/xeen_d3.lua'))
for n in os.listdir(os.path.join(A, 'worlds/xeen/data_tables')):
    if n not in ('house_data.txt', 'map_stats.txt'):
        os.symlink(os.path.join(A, 'worlds/xeen/data_tables', n), os.path.join(out, 'worlds/xeen/data_tables', n))
town = yaml.safe_load(open(os.path.join(A, 'worlds/xeen/source/towns/d3.yml')))
text = open(os.path.join(A, 'worlds/xeen/data_tables/house_data.txt'), encoding='latin-1').read()
rows = ['%d\t0\t%s\t9110\t-\t%s' % (h['id'], TYPE[h['kind']], h['name']) for h in town['houses'] if h['kind'] in TYPE]
with open(os.path.join(out, 'worlds/xeen/data_tables/house_data.txt'), 'w', encoding='latin-1') as f:
    f.write(text.rstrip('\n') + '\n' + '\n'.join(rows) + '\n')
# D3's map_stats row as project.yml says it (A2 writes the real one: map_rows.yml D3 has no slots yet)
ROW = ('9110\tSandcaster and the Aging Forest\txeen_d3.odm\t0\t0\t3\t672\t0\t0\t8\t4\t4\t10\t50\t26\t24\t'
       'Xeen Mantis\tXeen Mantis\t1\t 2-3\tXeen Cobra\tXeen Cobra\t1\t 2-3\tXeen Sand Worm\tXeen Sand Worm\t1\t 2-3\t'
       '39\tFOREST\tmap_studio\t0\t0\t-\t')
ms = open(os.path.join(A, 'worlds/xeen/data_tables/map_stats.txt'), encoding='latin-1').read()
if '\txeen_d3.odm\t' not in ms:
    ms = ms.rstrip('\n') + '\n' + ROW + '\n'
with open(os.path.join(out, 'worlds/xeen/data_tables/map_stats.txt'), 'w', encoding='latin-1') as f:
    f.write(ms)
print('tf root', out, 'with', len(rows), 'D3 rows')
