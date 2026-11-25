#!/usr/bin/env python3
"""F62 (the player's pins 2026-11-25, X8 Cloudreach): floors that cut through one another on a built BLV.

A plank bridge whose deck slopes down (a sag, or a lower island on the far side) dipped under the cloud top it was
meant to rest on: the deck ran 8 over the cloud at its end, crossed under the cloud's top before the rim and came out
again over the void, so the cloud was drawn over the planks and the deck's end looked cut into the island. The same
happens wherever two upward faces (floors or slopes) overlap seen from above and their heights cross: one face is
above the other at one end of the overlap and under it at the other.

Every pair of floors (normal z of at least 0.9: decks, ramps, tops; a rock's steep side rising through a cloud top is
meant and not looked at; door and portal faces left out) whose outlines overlap is
sampled on a grid of 16 over the overlap; a pair is a crossing when one face stands more than 1 over the other at
some point and more than 1 under it at another, and the crossing lies within 96 of both (a face far under another is
a floor below, not a crossing). Pairs in one plane are the studio audit's.

`floor.lid` (X8 p8, "you get stuck here"): a face looking down that lies on a floor (within 2 of it, overlapping it
over at least 64 square), the bottom of a block set on an island whose room floor is far below (an open-air map's
blocks all hang from the room's floor, so the studio draws their bottoms). The party walking to the block's foot meets
a ceiling at its feet and is wedged. Sink such a block into the floor it stands on (its base 8 under the top).

Usage: tools/xeen/check_floor_cross.py <map.blv>... [--assets ROOT] [--all]   (--all: every xeen_*.blv in assets_dev)
Exit 1 when a crossing is found. Each line: the map, the two faces (texture, room), the overlap's middle, how far each
stands over the other."""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OY = f'{R}/openyamm-studio/build-xeen/oymap'
GRID = 16.0
NEAR = 96.0
EPS = 1.0
WALK = 0.9   # crossings are looked for between floors (decks, ramps, tops); a rock's steep side through a cloud is meant


def pip(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def plane(poly, normal):
    nx, ny, nz = (c / 65536.0 for c in normal)
    x0, y0, z0 = poly[0]
    return lambda x, y: z0 - (nx * (x - x0) + ny * (y - y0)) / nz


def check(path, assets):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        d = json.load(open(t.name))
    m = d['map']
    V = m['vertices']
    doorfaces = {fi for door in d.get('doors', []) for fi in door['faces']}
    ups = []
    downs = []
    for i, f in enumerate(m['faces']):
        if not f.get('is_portal') and i not in doorfaces and f['plane_normal'][2] <= -0.99 * 65536:
            poly = [V[v] for v in f['vertices']]
            downs.append((i, f, poly, (min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly),
                                       max(p[1] for p in poly)), plane(poly, f['plane_normal']),
                          min(p[2] for p in poly), max(p[2] for p in poly)))
        if f.get('is_portal') or i in doorfaces or f['plane_normal'][2] < 0.1 * 65536:
            continue
        poly = [V[v] for v in f['vertices']]
        box = (min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly), max(p[1] for p in poly))
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            continue
        zs = [p[2] for p in poly]
        ups.append((i, f, poly, box, plane(poly, f['plane_normal']), min(zs), max(zs)))
    ups.sort(key=lambda u: u[3][0])
    found = []
    for a in range(len(ups)):
        ia, fa, pa, ba, za, loa, hia = ups[a]
        for b in range(a + 1, len(ups)):
            ib, fb, pb, bb, zb, lob, hib = ups[b]
            if bb[0] >= ba[2]:
                break
            if bb[1] >= ba[3] or bb[3] <= ba[1] or lob > hia + NEAR or loa > hib + NEAR:
                continue
            if min(fa['plane_normal'][2], fb['plane_normal'][2]) < WALK * 65536:
                continue
            x0, y0, x1, y1 = max(ba[0], bb[0]), max(ba[1], bb[1]), min(ba[2], bb[2]), min(ba[3], bb[3])
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            over = under = 0.0
            spot_over = spot_under = None
            nx = max(2, int((x1 - x0) / GRID))
            ny = max(2, int((y1 - y0) / GRID))
            step = max(1, (nx * ny) // 4000)
            k = 0
            for gx in range(nx):
                x = x0 + (gx + 0.5) * (x1 - x0) / nx
                for gy in range(ny):
                    k += 1
                    if k % step:
                        continue
                    y = y0 + (gy + 0.5) * (y1 - y0) / ny
                    if not (pip(x, y, pa) and pip(x, y, pb)):
                        continue
                    dz = za(x, y) - zb(x, y)
                    if abs(dz) > NEAR:
                        continue
                    if dz > over:
                        over, spot_over = dz, (x, y)
                    if -dz > under:
                        under, spot_under = -dz, (x, y)
            if over > EPS and under > EPS:
                mid = ((spot_over[0] + spot_under[0]) / 2, (spot_over[1] + spot_under[1]) / 2)
                found.append((ia, fa, ib, fb, mid, over, under))
    def reachable(ib, pb, bb, zb, ia):
        """The block over a lid can be walked onto: a top within a step (50) over the lid, or a slope that starts
        at the lid (a tall block with upright sides hides its lid, which then only wastes a face)."""
        n = 6
        pts = []
        for gx in range(n):
            for gy in range(n):
                x = bb[0] + (gx + 0.5) * (bb[2] - bb[0]) / n
                y = bb[1] + (gy + 0.5) * (bb[3] - bb[1]) / n
                if pip(x, y, pb):
                    pts.append((x, y, zb(x, y)))
        for ic, fc, pc, bc, zc, loc, hic in ups:
            if ic == ia or bc[0] >= bb[2] or bc[2] <= bb[0] or bc[1] >= bb[3] or bc[3] <= bb[1]:
                continue
            if hic < min(p[2] for p in pts) - 2 if pts else True:
                continue
            for x, y, z in pts:
                if not pip(x, y, pc):
                    continue
                rise = zc(x, y) - z
                if 2 < rise <= 50:
                    return True
                if fc['plane_normal'][2] < 0.99 * 65536 and abs(loc - z) <= 2 and 2 < rise:
                    return True
        return False

    lids = []
    for ib, fb, pb, bb, zb, lob, hib in downs:
        for ia, fa, pa, ba, za, loa, hia in ups:
            if hia < lob - 2 or loa > hib + 2 or ba[0] >= bb[2] or ba[2] <= bb[0] or ba[1] >= bb[3] or ba[3] <= bb[1]:
                continue
            x0, y0, x1, y1 = max(ba[0], bb[0]), max(ba[1], bb[1]), min(ba[2], bb[2]), min(ba[3], bb[3])
            hits = 0
            n = 8
            for gx in range(n):
                for gy in range(n):
                    x = x0 + (gx + 0.5) * (x1 - x0) / n
                    y = y0 + (gy + 0.5) * (y1 - y0) / n
                    if pip(x, y, pa) and pip(x, y, pb) and abs(za(x, y) - zb(x, y)) <= 2:
                        hits += 1
            if hits and hits * (x1 - x0) * (y1 - y0) / (n * n) >= 64 * 64:
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                if reachable(ib, pb, bb, zb, ia):
                    lids.append((ib, fb, ia, fa, (mx, my), zb(mx, my)))
    return found, lids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('blv', nargs='*')
    ap.add_argument('--assets', default=f'{R}/assets_dev')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    paths = list(a.blv)
    if a.all:
        paths += sorted(glob.glob(f'{a.assets}/worlds/xeen/maps/xeen_*.blv'))
    total = 0
    for path in paths:
        stem = os.path.basename(path).split('.')[0]
        found, lids = check(path, a.assets)
        for ib, fb, ia, fa, mid, z in lids:
            print(f'{stem}: floor.lid face {ib} ({fb["texture"]}, looking down, room {fb["room"]}) lies on floor face '
                  f'{ia} ({fa["texture"]}) at ({mid[0]:.0f}, {mid[1]:.0f}, {z:.0f})')
        for ia, fa, ib, fb, mid, over, under in found:
            print(f'{stem}: floor.cross face {ia} ({fa["texture"]}, room {fa["room"]}) and face {ib} '
                  f'({fb["texture"]}, room {fb["room"]}) at ({mid[0]:.0f}, {mid[1]:.0f}): {over:.0f} over, '
                  f'{under:.0f} under')
        print(f'{stem}: {len(found)} crossing(s), {len(lids)} lid(s)', file=sys.stderr)
        total += len(found) + len(lids)
    print(f'total {total} finding(s) on {len(paths)} map(s)', file=sys.stderr)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
