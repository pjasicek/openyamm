#!/usr/bin/env python3
"""F65 (the player's pins 2026-11-25, XD-26 p1 "make the nest more clickable", XD-23 p1 "i had problem to click on
this"): a clicked low block (a nest, a fire pit, a pool's rim, a bed) whose top does not take its click.

A block under 64 high whose sides run a click event (face attribute 0x02000000) and whose flat top inside the same
outline has another event or none: only the rim is clickable, so a click on the top (where the crosshair lies when the
party looks down at it) does nothing or runs a step text. Causes found: the room's step event on the top (XD-26's
Great nest; fixed in the studio 2026-11-25, openyamm-studio core/IndoorLowering.cpp featureFloorPart) and a top built
as a node of its own (a `set_texture ... face: top` effect, or a water floor part on a pool) that the studio leaves
without the block's click (XD-23's fire pit, DD-13's two pits, XD-02's two pools; studio request 2026-11-25).

Usage: tools/xeen/check_clicked_tops.py [<map.blv>...] [--assets ROOT]    no maps: every Xeen BLV in assets_dev.
Exit 1 on a finding."""
import argparse
import collections
import glob
import json
import os
import subprocess
import sys
import tempfile

R = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
OYMAP = os.path.join(R, 'openyamm-studio/build-xeen/oymap')
CLICKABLE = 0x02000000
LOW = 64


def check(path, assets):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OYMAP, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        m = json.load(open(t.name))['map']
    V = m['vertices']
    stem = os.path.basename(path)[:-4]
    sides = collections.defaultdict(list)
    for f in m['faces']:
        if f['cog_triggered'] and f['attributes'] & CLICKABLE and abs(f['plane_normal'][2]) < 0.3 * 65536 \
                and not f['is_portal']:
            sides[f['cog_triggered']].append([V[v] for v in f['vertices']])
    out = []
    for event, fs in sorted(sides.items()):
        P = [p for f in fs for p in f]
        x0, x1 = min(p[0] for p in P), max(p[0] for p in P)
        y0, y1 = min(p[1] for p in P), max(p[1] for p in P)
        z0, z1 = min(p[2] for p in P), max(p[2] for p in P)
        if z1 - z0 > LOW or len(fs) < 3:
            continue
        for i, f in enumerate(m['faces']):
            if f['plane_normal'][2] < 0.7 * 65536:
                continue
            Q = [V[v] for v in f['vertices']]
            inside = min(q[0] for q in Q) >= x0 - 2 and max(q[0] for q in Q) <= x1 + 2 \
                and min(q[1] for q in Q) >= y0 - 2 and max(q[1] for q in Q) <= y1 + 2
            if inside and all(abs(q[2] - z1) <= 1 for q in Q) \
                    and (f['cog_triggered'] != event or not f['attributes'] & CLICKABLE):
                out.append(f'{stem}: a block clicked for event {event} ([{x0}, {y0}]-[{x1}, {y1}], {z1 - z0} high): '
                           f'its top (face {i}, {f["texture"]}) has event {f["cog_triggered"]}'
                           f'{"" if f["attributes"] & CLICKABLE else ", not clicked"}: only its rim takes the click')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('maps', nargs='*')
    ap.add_argument('--assets', default=os.path.join(R, 'assets_dev'))
    a = ap.parse_args()
    maps = a.maps or sorted(glob.glob(os.path.join(R, 'assets_dev/worlds/xeen/maps/xeen_*.blv')))
    found = 0
    for path in maps:
        for line in check(path, a.assets):
            print(line)
            found += 1
    print(f'total {found} clicked block(s) whose top does not take the click on {len(maps)} map(s)')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
