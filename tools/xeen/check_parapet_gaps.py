#!/usr/bin/env python3
"""F60 (the player's pins 2026-11-25, XD-14 p3/p4 "wall is missing"): slots of sky beside a parapet on a built BLV.

A walk open to the sky on one side keeps its outer wall and draws it as sky over a parapet (D-97). XD-14's generator
ran each parapet 32 in from the sky wall and stopped it 32 short of the walls at both ends, so between the parapet's
end and the side wall a slot 32 wide showed the sky from the floor up: a missing wall.

For every upright wall face drawn as sky (the IndoorSky bit) the faces in its room that stand in front of it, parallel,
within 96, from the floor and lower than it (the parapet's front) are laid along the sky face; a stretch of the sky
face not covered by them, wider than 4, between the first and the last parapet face or between one and the sky face's
end, is a `parapet.gap`. A sky face with no parapet in front (an opening meant as such) is not looked at.

F58/F60 (XD-13 p1 "z-fighting", a flat white face beside a pillar): `sky.low`. A sky wall with no parapet in front,
in a room with a floor the party can stand on, shows the sky below the eye wherever it comes down lower than that
floor's eye (EYE over it): an outdoor preset fills everything under the horizon with its flat fog colour (white, grey
or pale blue; INDOOR_OPEN_SKY.md), which reads as an untextured face. Along each such sky face, every SAMPLE units,
the ground in front of it is the highest top of the room's other faces flush with it (a heap or ledge against it, no
more than FLUSH in front); it is a `sky.low` where that ground is lower than EYE under the highest floor of the room
within REACH. Maps whose preset draws sky below the horizon (`below_horizon: sky`, the sky maps and planes) are not
looked at for it. Fix: a solid wall (the ruin's stone) up to the floor's eye and more, sky only above it, or a parapet.

Usage: tools/xeen/check_parapet_gaps.py <map.blv>... [--assets ROOT] [--all]    exit 1 on a gap or a low sky."""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OY = f'{R}/openyamm-studio/build-xeen/oymap'
SKY_BIT = 0x400000
NEAR = 96
GAP = 4
LOW = 64       # sky this near over the floor at its foot: no wall or parapet between the floor and the sky
FLUSH = 16     # a face this near the sky face's plane, in front of it, stands against it
SAMPLE = 32
DEPTH = 64     # a floor at the sky face's foot narrower than this is a parapet's top, not a place to stand
HORIZON = {'open_ground'}   # open_sky.yml kinds whose sky walls are the map's horizon, the ground meeting them


def sky_below_horizon(stem, assets):
    """True when the map's open sky draws sky, not fog, below the horizon (its preset's `below_horizon: sky`)."""
    try:
        scene = yaml.safe_load(open(f'{assets}/worlds/xeen/maps/{stem}.scene.yml'))
    except OSError:
        return False
    sky = (scene or {}).get('sky') or {}
    presets, aliases = {}, {}
    for f in (f'{assets}/engine/rendering/sky/sky.yml', f'{assets}/worlds/xeen/rendering/sky/sky.yml'):
        try:
            d = yaml.safe_load(open(f)) or {}
        except OSError:
            continue
        presets.update(d.get('presets') or {})
        aliases.update(d.get('aliases') or {})
    name = sky.get('preset') or aliases.get(sky.get('sky_texture'))
    seen = set()
    while name and name not in seen:
        seen.add(name)
        p = presets.get(name) or {}
        if 'below_horizon' in p:
            return p['below_horizon'] == 'sky'
        name = p.get('inherits')
    return False


def low_sky(m, i, f, n, P):
    """`sky.low` spots of one sky wall face with no parapet in front: [(x, y, floor z)], where a floor the party can
    stand on runs up to the sky face and the sky comes down to within LOW of it (no wall or parapet between)."""
    V = m['vertices']
    u = (-n[1], n[0])
    ts = [p[0] * u[0] + p[1] * u[1] for p in P]
    t0, t1 = min(ts), max(ts)
    d0 = P[0][0] * n[0] + P[0][1] * n[1]
    zhi = max(p[2] for p in P)
    flush = []    # (edge points flush with the sky face, is a floor)
    for g in m['faces']:
        if g is f or g['room'] != f['room'] or g.get('is_portal') or g['attributes'] & SKY_BIT:
            continue
        Q = [V[v] for v in g['vertices']]
        near = [q for q in Q if -1 <= q[0] * n[0] + q[1] * n[1] - d0 <= FLUSH]
        if len(near) >= 2:
            # A floor counts only if it is a place to stand, at least DEPTH deep and wide: the top of a thin parapet
            # with the sky standing on its end (XD-12's roof corners, 32 thick) is the parapet, not a floor.
            depth = max(q[0] * n[0] + q[1] * n[1] for q in Q) - d0
            across = [q[0] * u[0] + q[1] * u[1] for q in Q]
            wide = min(depth, max(across) - min(across)) >= DEPTH
            flush.append((near, g['plane_normal'][2] / 65536.0 >= 0.5 and wide))   # steep heaps count
    out = []
    t = t0 + SAMPLE / 2
    while t < t1:
        ground, floor = min(p[2] for p in P), None
        for near, is_floor in flush:
            for a in range(len(near)):
                for b in range(a + 1, len(near)):
                    pa, pb = near[a], near[b]
                    ua, ub = pa[0] * u[0] + pa[1] * u[1], pb[0] * u[0] + pb[1] * u[1]
                    if not min(ua, ub) <= t <= max(ua, ub):
                        continue
                    z = max(pa[2], pb[2]) if abs(ub - ua) < 1 else pa[2] + (pb[2] - pa[2]) * (t - ua) / (ub - ua)
                    ground = max(ground, min(z, zhi))
                    if is_floor:
                        floor = z if floor is None else max(floor, z)
        if floor is not None and ground < zhi - 8 and ground - floor < LOW:
            out.append((t * u[0] + d0 * n[0], t * u[1] + d0 * n[1], floor))
        t += SAMPLE
    return out


def check(path, assets, low=True, horizon_rooms=()):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        d = json.load(open(t.name))
    m = d['map']
    V = m['vertices']
    walls = []
    for i, f in enumerate(m['faces']):
        n = [c / 65536.0 for c in f['plane_normal']]
        if f.get('is_portal') or abs(n[2]) > 0.05:
            continue
        P = [V[v] for v in f['vertices']]
        walls.append((i, f, n, P))
    found = []
    for i, f, n, P in walls:
        if not f['attributes'] & SKY_BIT:
            continue
        # along-wall axis u (horizontal, perpendicular to n); distance axis n (into the room)
        u = (-n[1], n[0])
        ts = [p[0] * u[0] + p[1] * u[1] for p in P]
        t0, t1 = min(ts), max(ts)
        d0 = P[0][0] * n[0] + P[0][1] * n[1]
        zlo, zhi = min(p[2] for p in P), max(p[2] for p in P)
        cover = []
        for j, g, gn, Q in walls:
            if j == i or g['attributes'] & SKY_BIT or g['room'] != f['room']:
                continue
            if gn[0] * n[0] + gn[1] * n[1] < 0.99:
                continue   # the parapet's front faces the same way as the sky face (into the room)
            dist = Q[0][0] * n[0] + Q[0][1] * n[1] - d0
            if not 0 < dist <= NEAR:
                continue
            qlo, qhi = min(q[2] for q in Q), max(q[2] for q in Q)
            if qlo > zlo + 8 or qhi >= zhi:
                continue
            qs = [q[0] * u[0] + q[1] * u[1] for q in Q]
            a, b = max(min(qs), t0), min(max(qs), t1)
            if b > a:
                cover.append((a, b))
        if not cover:
            if low:
                spots = [] if f['room'] in horizon_rooms else low_sky(m, i, f, n, P)
                if spots:
                    x, y, fz = max(spots, key=lambda s: s[2])
                    found.append((i, f, (x, y, fz), len(spots) * SAMPLE, 'low'))
            continue
        cover.sort()
        gaps = []
        at = t0
        for a, b in cover:
            if a - at > GAP:
                gaps.append((at, a))
            at = max(at, b)
        if t1 - at > GAP:
            gaps.append((at, t1))
        for a, b in gaps:
            mid = (a + b) / 2
            x = mid * u[0] + d0 * n[0]
            y = mid * u[1] + d0 * n[1]
            found.append((i, f, (x, y, zlo), b - a, None))
    return found


def horizon_rooms(stem):
    """Sector ids of the map's open_sky.yml rooms whose kind is a horizon (HORIZON)."""
    key = stem.replace('xeen_', '')
    try:
        listed = (yaml.safe_load(open(f'{R}/tools/xeen/open_sky.yml')) or {}).get(key) or {}
        ids = yaml.safe_load(open(f'{R}/devdocs/xeen/briefs/{key}/L4/ids.lock.yml')) or {}
    except OSError:
        return set()
    flat = {}
    for k, v in ids.items():
        if isinstance(v, dict):
            flat.update(v)
        else:
            flat[k] = v
    return {flat[r] for r, e in listed.items() if (e or {}).get('kind') in HORIZON and r in flat}


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
        found = check(path, a.assets, low=not sky_below_horizon(stem, a.assets),
                      horizon_rooms=horizon_rooms(stem))
        for i, f, (x, y, z), width, kind in found:
            if kind is None:
                print(f'{stem}: parapet.gap sky face {i} ({f["texture"]}, room {f["room"]}): {width:.0f} wide at '
                      f'({x:.0f}, {y:.0f}, {z:.0f})')
            else:
                print(f'{stem}: sky.low sky face {i} ({f["texture"]}, room {f["room"]}): {width:.0f} of it comes down '
                      f'to the floor at its foot, up to z {z:.0f} at ({x:.0f}, {y:.0f})')
        total += len(found)
    print(f'total {total} gap(s) or low sky face(s) on {len(paths)} map(s)', file=sys.stderr)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
