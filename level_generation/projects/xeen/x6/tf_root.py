#!/usr/bin/env python3
"""X6's town_feel root (A5, 2026-11-20): a read-only view of assets_dev (symlinks) whose world house_data.txt holds the
world's rows plus X6's houses typed from A4's planned x6.yml (`kind`), only for town_feel's measure, never installed:
A4 writes the real rows when x6.yml stops being planned. Usage: tf_root.py <out dir> (the dir must not exist)."""
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
B = os.path.join(ROOT, 'output/studio_cal/x6/build_w')
for n in os.listdir(os.path.join(A, 'worlds/xeen')):
    if n not in ('data_tables', 'maps', 'events'):
        os.symlink(os.path.join(A, 'worlds/xeen', n), os.path.join(out, 'worlds/xeen', n))
# the maps and the map scripts: assets_dev's, and X6's build in place of an installed X6
os.makedirs(os.path.join(out, 'worlds/xeen/maps'))
for n in os.listdir(os.path.join(A, 'worlds/xeen/maps')):
    if not n.startswith('xeen_x6.'):
        os.symlink(os.path.join(A, 'worlds/xeen/maps', n), os.path.join(out, 'worlds/xeen/maps', n))
for n in ('xeen_x6.odm', 'xeen_x6.scene.yml'):
    os.link(os.path.join(B, n), os.path.join(out, 'worlds/xeen/maps', n))     # the game reads no symlinked file
os.makedirs(os.path.join(out, 'worlds/xeen/events/maps'))
for n in os.listdir(os.path.join(A, 'worlds/xeen/events')):
    if n != 'maps':
        os.symlink(os.path.join(A, 'worlds/xeen/events', n), os.path.join(out, 'worlds/xeen/events', n))
for n in os.listdir(os.path.join(A, 'worlds/xeen/events/maps')):
    if n != 'xeen_x6.lua':
        os.symlink(os.path.join(A, 'worlds/xeen/events/maps', n), os.path.join(out, 'worlds/xeen/events/maps', n))
os.link(os.path.join(B, 'xeen_x6.lua'), os.path.join(out, 'worlds/xeen/events/maps/xeen_x6.lua'))
for n in os.listdir(os.path.join(A, 'worlds/xeen/data_tables')):
    if n not in ('house_data.txt', 'map_stats.txt'):
        os.symlink(os.path.join(A, 'worlds/xeen/data_tables', n), os.path.join(out, 'worlds/xeen/data_tables', n))
town = yaml.safe_load(open(os.path.join(A, 'worlds/xeen/source/towns/x6.yml')))
text = open(os.path.join(A, 'worlds/xeen/data_tables/house_data.txt'), encoding='latin-1').read()
rows = ['%d\t0\t%s\t9104\t-\t%s' % (h['id'], TYPE[h['kind']], h['name']) for h in town['houses'] if h['kind'] in TYPE]
with open(os.path.join(out, 'worlds/xeen/data_tables/house_data.txt'), 'w', encoding='latin-1') as f:
    f.write(text.rstrip('\n') + '\n' + '\n'.join(rows) + '\n')
# X6's map_stats row as project.yml says it (A2 writes the real one: map_rows.yml D3 has no slots yet)
pr = yaml.safe_load(open(os.path.join(ROOT, 'devdocs/xeen/briefs/x6/L4/project.yml')))
m, sl = pr['map_stats'], pr['map_stats']['slots']
ROW = '\t'.join(str(v) for v in [
    m['id'], pr['name'], 'xeen_x6.odm', 0, 0, m['treasure_level'], m['refill_days'], 0, 0, m['lock_difficulty'],
    m['trap_dice'], m['perception_difficulty'], m['encounter_chance'], sl[0]['weight'], sl[1]['weight'], sl[2]['weight']]
    + sum([[q['monster'], q['monster'], q['tier'], ' %d-%d' % tuple(q['per_marker'])] for q in sl], [])
    + [m['music'], 'DESERT', 'map_studio', 0, 0, '-', ''])
ms = open(os.path.join(A, 'worlds/xeen/data_tables/map_stats.txt'), encoding='latin-1').read()
if '\txeen_x6.odm\t' not in ms:
    ms = ms.rstrip('\n') + '\n' + ROW + '\n'
with open(os.path.join(out, 'worlds/xeen/data_tables/map_stats.txt'), 'w', encoding='latin-1') as f:
    f.write(ms)
print('tf root', out, 'with', len(rows), 'X6 rows')
