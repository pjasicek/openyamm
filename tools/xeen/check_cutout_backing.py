#!/usr/bin/env python3
"""F71 (the player's pins 2026-11-26, XD-13 p2 "is here something missing?"): see-through textures with nothing
behind them.

XD-13's speaking grille was a wall panel in `xngrille`, a cutout (its bars on transparent texels, made for XD-02's hoist
gate, which has the shaft behind it). On a solid wall the transparent texels showed whatever the renderer clears to,
the sky, through the bars.

Every face with a cutout texture (`kind: cutout` in `assets_dev/worlds/xeen/source/textures.yml`, or a Xeen texture
whose picture is mostly transparent) is looked through: from points on the face, rays run straight back through it
(against its normal), on through other cutout faces (a cage's far bars) and portals. Something must be drawn behind
it: the nearest other face a ray meets must face the ray (a floor, a wall or a ceiling of the space behind it). A ray
that meets nothing, or first meets the back of a face (the outside of another room's wall: the portal renderer draws
nothing past a wall), sees the void: on a map with sky faces (IndoorSky) the void is drawn as the sky, an error
(`cutout.no_backing`); on a map without them it is black, which reads as a dark hole behind bars, a warning to look at
(`cutout.dark_backing`).
Fix: a backing (a recess with a back wall in the panel's frame, a dark face behind the bars) or an opaque picture.

Usage: tools/xeen/check_cutout_backing.py <map.blv>... [--assets ROOT] [--all]   (--all: every xeen_*.blv)
Exit 1 on an error."""
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
FAR = 8192.0
SKY = 0x00400000
AXES = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def cutouts(assets):
    names = set()
    with open(f'{R}/assets_dev/worlds/xeen/source/textures.yml') as f:
        data = yaml.safe_load(f)
    rows = data.get('textures', data) if isinstance(data, dict) else data
    for row in rows or []:
        if isinstance(row, dict) and row.get('kind') == 'cutout':
            names.add(row['name'].lower())
    try:
        from PIL import Image
    except ImportError:
        return names
    for path in glob.glob(f'{assets}/worlds/xeen/textures_x2/*.png'):
        im = Image.open(path)
        if 'A' not in im.getbands():
            continue
        h = im.getchannel('A').histogram()
        if sum(h[:128]) > 0.05 * im.size[0] * im.size[1]:
            names.add(os.path.splitext(os.path.basename(path))[0].lower())
    return names


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def inside(poly, p, n):
    ax = max(range(3), key=lambda i: abs(n[i]))
    i, j = [k for k in range(3) if k != ax]
    x, y = p[i], p[j]
    c = False
    for k in range(len(poly)):
        x1, y1 = poly[k][i], poly[k][j]
        x2, y2 = poly[k - 1][i], poly[k - 1][j]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def first_hit(faces, names, i, o, d, min_t=2.0):
    """The nearest face (not face i, not a cutout: more bars, the ray goes on through them) a ray from o along d
    meets: (distance, whether it faces the ray), or (FAR, False)."""
    best, front = FAR, False
    for j, g, gn, gp in faces:
        if j == i or str(g.get('texture', '')).lower() in names:
            continue
        den = dot(gn, d)
        if abs(den) < 1e-6:
            continue
        tt = dot(gn, sub(gp[0], o)) / den
        if tt <= min_t:
            # the back of a wall in the face's own plane (a room on the other side of a shared wall): the portal
            # renderer draws nothing of that room through a wall
            if den > 0 and tt > -2.0:
                hit = (o[0] + d[0] * tt, o[1] + d[1] * tt, o[2] + d[2] * tt)
                if inside(gp, hit, gn):
                    return 0.0, False
            continue
        if tt >= best:
            continue
        hit = (o[0] + d[0] * tt, o[1] + d[1] * tt, o[2] + d[2] * tt)
        if inside(gp, hit, gn):
            best, front = tt, den < 0
    return best, front


def check(path, assets, names):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        d = json.load(open(t.name))
    m = d['map']
    V = m['vertices']
    faces = []
    for i, f in enumerate(m['faces']):
        if f.get('is_portal'):
            continue
        n = tuple(c / 65536.0 for c in f['plane_normal'])
        poly = [tuple(V[v]) for v in f['vertices']]
        if len(poly) < 3:
            continue
        faces.append((i, f, n, poly))
    sky = any(f['attributes'] & SKY for _, f, _, _ in faces)
    found = []
    for i, f, n, poly in faces:
        if str(f.get('texture', '')).lower() not in names:
            continue
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        cz = sum(p[2] for p in poly) / len(poly)
        pts = [(cx, cy, cz)] + [((cx + p[0]) / 2, (cy + p[1]) / 2, (cz + p[2]) / 2) for p in poly[:4]]
        # only a face the party can see: the space in front of it is open (a cage side against a wall, a bottom on
        # the floor are not looked at)
        tt, front = first_hit(faces, names, i, (cx, cy, cz), n, min_t=-2.0)
        if tt < 48 or (tt < FAR and not front):     # nobody looks at it from a gap under 48
            continue
        eye = (cx + n[0] * 24, cy + n[1] * 24, cz + n[2] * 24)
        if any(not fr and t < FAR for t, fr in (first_hit(faces, names, i, eye, a, min_t=0.0) for a in AXES
                                                 if dot(a, n) > -0.5)):    # not back through the face itself
            continue                                       # its front is inside rock (the back of a wall seen)
        d = (-n[0], -n[1], -n[2])
        blind = 0
        for o in pts:
            tt, front = first_hit(faces, names, i, (o[0] + n[0], o[1] + n[1], o[2] + n[2]), d)
            if not front:
                blind += 1
        if blind * 2 > len(pts):
            what = ('error: ', 'cutout.no_backing', 'the sky shows through') if sky else \
                ('warning: ', 'cutout.dark_backing', 'black shows through')
            found.append(f'{what[0]}{os.path.basename(path)}: {what[1]} face {i} ({f["texture"]}, room '
                         f'{f.get("room")}) at ({cx:.0f}, {cy:.0f}, {cz:.0f}): {blind} of {len(pts)} rays through it '
                         f'see no face behind it ({what[2]})')
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('maps', nargs='*')
    ap.add_argument('--assets', default=f'{R}/assets_dev')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    maps = list(a.maps)
    if a.all:
        maps += sorted(glob.glob(f'{a.assets}/worlds/xeen/maps/xeen_*.blv'))
    names = cutouts(a.assets)
    found = []
    for path in maps:
        found += check(path, a.assets, names)
    for line in found:
        print(line)
    errors = sum(1 for line in found if line.startswith('error'))
    print(f'cutout faces with nothing behind them: {errors} error(s) (sky), {len(found) - errors} warning(s) (black) '
          f'(cutout textures: {", ".join(sorted(names))})')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
