#!/usr/bin/env python3
"""A5 X4 (2026-11-20): give the scratch root output/studio_cal/x4/root X4's map_stats row and travel row (A2 writes
the real ones after install). The root is a hard-link copy of assets_dev: each table is REPLACED (new file + rename),
never written in place."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else 'output/studio_cal/x4/root'
assert os.path.realpath(root).startswith(_REPO_ROOT + '/output/studio_cal/x4/')
tables = os.path.join(root, 'worlds/xeen/data_tables')


def replace(name, edit):
    path = os.path.join(tables, name)
    text = open(path).read()
    new = edit(text)
    if new == text:
        print(name, 'unchanged')
        return
    tmp = path + '.x4new'
    with open(tmp, 'w') as f:
        f.write(new)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)
    print(name, 'replaced')


def stats(text):
    lines = text.split('\n')
    if any(l.startswith('9102\t') for l in lines):
        return text
    x2 = next(l for l in lines if l.startswith('9136\t')).split('\t')
    row = list(x2)
    row[0], row[1], row[2] = '9102', 'Burlock Savannah', 'xeen_x4.odm'
    row[11] = '2'                                    # Tres 0-6
    row[13], row[14], row[15] = '27', '33', '40'      # M1-M3 %
    row[16:28] = ['Xeen Knight', 'Xeen Knight', '1', ' 2-3', 'Xeen Ogre', 'Xeen Ogre', '0', ' 2-3',
                  'Xeen Gargoyle', 'Xeen Gargoyle', '1', ' 2-4']
    row[28] = '29'                                   # music
    i = next(k for k, l in enumerate(lines) if l.startswith('9136\t'))
    lines.insert(i + 1, '\t'.join(row))
    return '\n'.join(lines)


def travel(text):
    lines = text.split('\n')
    if any(l.startswith('xeen_x4.odm\t') for l in lines):
        return text
    ncols = len(lines[0].split('\t'))
    row = [''] * ncols
    row[0] = 'xeen_x4.odm'
    row[4], row[5], row[6] = 'xeen_x2.odm', 'up', '5'    # south edge: X2's north start
    row[14] = 'Burlock Savannah'
    k = max(i for i, l in enumerate(lines) if l.strip()) + 1
    lines.insert(k, '\t'.join(row))
    return '\n'.join(lines)


replace('map_stats.txt', stats)
replace('outdoor_travels.txt', travel)
