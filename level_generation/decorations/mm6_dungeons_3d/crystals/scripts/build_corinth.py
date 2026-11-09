"""MM6 Corinthian column `corinth` (56 x 253 at DSFT scale 1.8: 455 world units tall): square plinth, a base of three
rows of hanging acanthus leaves over a moulded bell, a plain marble shaft, an astragal ring, a capital of three rows
of upright acanthus leaves curling out under a square abacus. Dimensions are the native sprite's (x2 pixels measured
from its bottom row, half widths; README.md), so the front view keeps its outline. Marble (props marble texture,
tinted to the native mean); the leaves are a separate double-sided material. LOD1 keeps coarser leaves, LOD2
replaces each leaf crown by a flared lathe. Writes work/corinth_export.glb.
Usage: blender --background --python build_corinth.py -- corinth"""
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crystals_lib as cl  # noqa: E402

pl = cl.pl
SCALE = 1.8
NATIVE = (144.2, 132.8, 116.6)       # native mean colour (sRGB)


def W(px):
    """x2 sprite pixels to model metres (logical = px / 2, world = logical x DSFT scale)."""
    return cl.u(px / 2 * SCALE)


# (radius, height) in x2 pixels from the sprite's bottom row.
PLINTH = [(54, 0), (54, 14), (52, 18)]                     # square: corner radius = half width x sqrt 2
BASE = [(44, 17), (40, 40), (36, 60), (33, 84), (30, 88), (31.5, 94), (28, 100), (26, 106), (29, 111), (28.5, 116),
        (25, 122)]
SHAFT = [(25, 122), (25, 378)]
ASTRAGAL = [(25, 378), (27, 380), (29.5, 384), (29.5, 390), (27, 394)]
BELL = [(27, 394), (30, 410), (34, 430), (39, 450), (44, 462)]
ABACUS = [(45, 460), (47, 468), (52, 474), (54, 478), (54, 494), (52, 498)]
# Leaf rows: (bottom, top, radius at the root, radius at the curled tip, width, angular offset); capital leaves grow
# up, base leaves hang down (bottom and top swapped: root at the top).
CAPITAL_ROWS = [(394, 426, 29, 41, 30, 0.0), (410, 444, 32, 45, 31, 0.5), (428, 463, 36, 52, 32, 0.0)]
BASE_ROWS = [(54, 86, 33, 42, 30, 0.0), (36, 68, 37, 47, 31, 0.5), (18, 50, 41, 53, 32, 0.0)]
LEAVES_PER_ROW = 8


def lathe(name, profile, segments, mat, square=False, cap_top=False):
    obj = pl.lathe(name, [(W(r * (math.sqrt(2) if square else 1)), W(h)) for r, h in profile], segments, mat,
                   u_repeat=2.0 if not square else 1.0, v_scale=1.2, cap_top=cap_top, smooth=not square)
    if square:
        obj.rotation_euler.z = math.pi / 4
    return obj


def leaf(name, row, index, mat, across, along, hanging):
    """One acanthus leaf on the bell: rounded, with a raised midrib, its tip curling outward (and over)."""
    bottom, top, r_root, r_tip, width, offset = row
    theta0 = 2 * math.pi * (index + offset) / LEAVES_PER_ROW
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    grid = []
    for j in range(along + 1):
        t = j / along
        curl = max(0.0, (t - 0.6) / 0.4)
        height = t * (top - bottom) - 6.0 * curl ** 2
        z = top - height if hanging else bottom + height
        radius = r_root + 2.5 + (r_tip - r_root) * curl ** 1.5 + 4.0 * math.sin(math.pi * t)
        # Rounded scale outline: widest a little above the middle, a blunt rounded tip.
        half = width / 2 * math.sqrt(max(0.04, 1 - ((t - 0.55) / 0.48) ** 2))
        row_verts = []
        for i in range(across + 1):
            s = -1 + 2 * i / across
            r = radius + 2.5 * (1 - s * s) + 1.5 * s * s * curl
            theta = theta0 + s * half / max(radius, 1.0)
            row_verts.append(bm.verts.new((W(r * math.cos(theta)), W(r * math.sin(theta)), W(z))))
        grid.append(row_verts)
    for j in range(along):
        for i in range(across):
            quad = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            f = bm.faces.new(quad if not hanging else tuple(reversed(quad)))
            for loop in f.loops:
                jj = next(k for k in range(along + 1) if loop.vert in grid[k])
                ii = grid[jj].index(loop.vert)
                loop[uv].uv = (ii / across * 0.5 + 0.25, jj / along * 0.6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = pl.to_object(name, bm, mat, smooth=True)
    # Face the leaf outward (its normals point away from the column axis).
    me = obj.data
    me.update()
    centre = sum((p.center for p in me.polygons), start=me.polygons[0].center * 0) / len(me.polygons)
    outward = sum(p.normal.dot((p.center.x, p.center.y, 0)) for p in me.polygons)
    if outward < 0:
        for p in me.polygons:
            p.flip()
    return obj


def crown(name, rows, mat, segments, hanging):
    """LOD2: a leaf crown as a flared lathe through each row's root and tip."""
    profile = []
    for bottom, top, r_root, r_tip, _, _ in rows:
        if hanging:
            profile += [(r_tip + 1, bottom), (r_root + 2, top)]
        else:
            profile += [(r_root + 2, bottom), (r_tip + 1, top)]
    profile.sort(key=lambda p: p[1])
    return lathe(name, profile, segments, mat)


def build(level, mats):
    marble, leaves = mats['Marble'], mats['Leaves']
    segments = (24, 12, 8)[level]
    # LOD2 keeps only each moulding's main stations.
    base = BASE if level < 2 else [BASE[0], BASE[3], BASE[6], BASE[-1]]
    astragal = ASTRAGAL if level < 2 else [ASTRAGAL[0], ASTRAGAL[2], ASTRAGAL[-1]]
    bell = BELL if level < 2 else [BELL[0], BELL[-1]]
    parts = [lathe('plinth', PLINTH, 4, marble, square=True, cap_top=True),
             lathe('base', base, segments, marble),
             lathe('shaft', SHAFT, segments, marble),
             lathe('astragal', astragal, segments, marble),
             lathe('bell', bell, segments, marble),
             lathe('abacus', ABACUS, 4, marble, square=True, cap_top=True)]
    if level < 2:
        across, along = ((4, 5), (2, 3))[level]
        for rows, hanging in ((CAPITAL_ROWS, False), (BASE_ROWS, True)):
            for r, row in enumerate(rows):
                for k in range(LEAVES_PER_ROW):
                    parts.append(leaf(f'leaf{int(hanging)}{r}{k}', row, k, leaves, across, along, hanging))
    else:
        parts.append(crown('capital', CAPITAL_ROWS, leaves, 6, False))
        parts.append(crown('basecrown', BASE_ROWS, leaves, 6, True))
    cl.apply_transforms(parts)
    for p in parts:
        cl.bright(p)
    return parts


def main():
    pl.reset()
    mats = {'Marble': cl.material('Marble', 'marble', extras={'openyamm_specular': 0.5}),
            'Leaves': cl.material('Leaves', 'marble', extras={'openyamm_specular': 0.5})}
    tints = {name: cl.tint_for(mats[name], NATIVE) for name in mats}
    print('TINTS', tints)
    lods = []
    for level in range(3):
        solid = pl.join(f'corinth{level}', build(level, mats))
        name = 'Corinth' if level == 0 else f'Corinth_LOD{level}'
        lods.append(cl.finish_lod(solid, name, (40, 24, 12)[level], W(24), 0.75, tints, floor=True))
    cl.save_and_export('corinth', lods)


main()
