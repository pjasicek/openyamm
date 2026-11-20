#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_templeofhonk/props.json: every Prop, Brazier, WallTorch and TreasureChest
placement plus the Golden Honk (PickupItem 453) in the native frame (the old bmodel_world map's frame, which the BLV
keeps: no offset), and checks each end to end as the Anskram Keep's placements.py does (its rot and glb_lod0 are
reused): the finished GLB's LOD0, placed the way the engine places a decoration model (glTF (x, y, z) -> OpenYAMM
(-x, z, y), scaled by binding height / bounds height, turned by the facing, at the entity position), against the old
map's baked BModel of the same object (MM9_static_prop_<object>_<name>, MM9_chest_<object>_<name>,
MM9_pickup_<object>_<name>); median vertex distance printed. Reused decorations are checked with their owning
project's GLB and meta. The tilted book is compared with its pitch applied (the isle's tilt_oy).

Positions are the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. The Golden Honk (MoveToFloor 1) stands with its base on the floor under its DAT position (the
altar top: the highest floor face of the old map's world geometry below it). Braziers and torches name the BLV light
MM9 placed beside each (the map project's work/lights.json: the nearest kept light; their rows carry no light).
Usage: placements.py"""
import json
import math
import sys

import numpy as np
from scipy.spatial import cKDTree

import anskram
import props_table

base = anskram.load('placements')
rot, glb_lod0, world_positions = base.rot, base.glb_lod0, base.world_positions

REPO = props_table.REPO
PROJECT = props_table.PROJECT
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/templeofhonk.odm'
CLASS_KIND = {'Prop': 'prop', 'WallTorch': 'torch', 'Brazier': 'brazier', 'TreasureChest': 'chest',
              'PickupItem': 'quest'}
QUEST = {'key0'}                    # the accountant's key (scripts\HonkKey.scr opens his door)
PREFIX = {'TreasureChest': 'MM9_chest', 'PickupItem': 'MM9_pickup'}


def tilt_oy(local, pitch, roll):
    """The transcoder's object pitch (about x) then roll (about y), in OpenYAMM-local axes (the isle's placements)."""
    cx, sx, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ryy = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return local @ (ryy @ rx).T


def load_map():
    sys.path.insert(0, str(REPO))
    from util.map_export import parse_odm_file
    return parse_odm_file(ODM)['payload']['bmodels']


def floor_below(bmodels, point):
    """Highest upward face of the world geometry (not props, chests, pickups) under point, at or below it + 8."""
    best = None
    for b in bmodels:
        if b['name'].startswith('MM9_'):
            continue
        verts = np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float)
        for f in b['faces']:
            poly = verts[f['vertex_indices'][:f['vertex_count']]]
            for k in range(1, len(poly) - 1):
                a, bb, c = poly[0], poly[k], poly[k + 1]
                n = np.cross(bb - a, c - a)
                if abs(n[2]) < 1e-6 or n[2] / np.linalg.norm(n) < 0.7:
                    continue
                d0 = np.cross(bb - a, point - a)[2] * n[2]
                d1 = np.cross(c - bb, point - bb)[2] * n[2]
                d2 = np.cross(a - c, point - c)[2] * n[2]
                if min(d0, d1, d2) < 0:
                    continue
                z = a[2] - (n[0] * (point[0] - a[0]) + n[1] * (point[1] - a[1])) / n[2]
                if z <= point[2] + 8 and (best is None or z > best):
                    best = z
    return best


def main():
    bmodels = load_map()
    baked = {b['name']: np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float) for b in bmodels}
    plan = json.loads((props_table.HERE / 'work/decorations_plan.json').read_text())
    raw = {o['index']: o for o in props_table.objects()}
    lights = [l for l in json.loads((PROJECT / 'work/lights.json').read_text()) if l['kept']]
    light_points = np.array([l['position'] for l in lights], float)
    entries, report = [], []
    for idx, prop in props_table.placements():
        o = raw[idx]
        p = o['props']
        s = float(p.get('Scale', 1.0))
        ry = float(p['Rotation'][1])
        pos_old = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        home = props_table.home(prop)
        meta = json.loads((home / f'work/{prop}_meta.json').read_text())
        variant = next(d for d in plan if d['prop'] == prop and abs(d['scale'] - s) < 1e-3)
        g = world_positions(home / f'work/raw/{prop}/{prop}.glb') + np.array(props_table.binding_origin(prop)) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        if prop in props_table.BOOK_TILT:
            local = tilt_oy(local, *props_table.BOOK_TILT[prop])
        inst = (local * s) @ rot(-ry).T + pos_old
        stem = f"{PREFIX.get(o['class'], 'MM9_static_prop')}_{idx}_"      # BModel names stop at 32 characters
        bake = next(v for k, v in baked.items() if k.startswith(stem) and p['Name'].startswith(k[len(stem):]))
        extra = (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        note = ''
        if o['class'] == 'PickupItem':
            floor = floor_below(bmodels, pos_old)
            note = f' (base {position[2]:.1f} in the bake, floor under the DAT position {floor:.1f})'
            position[2] = floor
        a = glb_lod0(home / f'work/mm9_deco_{prop}.glb')
        engine_scale = variant['height'] / (a[:, 1].max() - a[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        if meta.get('flame_head_m'):          # the flame cards are not in the bake
            placed = placed[a[:, 1] * engine_scale < (meta['flame_head_m'][2] * 81.7 * engine_scale) - 1]
        d, _ = cKDTree(bake).query(placed)
        fit = float(np.median(d))
        entry = {'source_object': idx, 'source_name': p['Name'], 'class': o['class'],
                 'kind': 'quest' if p['Name'] in QUEST else CLASS_KIND[o['class']],
                 'source_model': p['Filename'], 'source_skin': p.get('Skin'), 'prop': prop,
                 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                 'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                 'yaw_degrees': round(math.degrees(-ry) % 360.0, 2), 'fit_median_units': round(fit, 2)}
        if o['class'] in ('WallTorch', 'Brazier'):
            distance = np.linalg.norm(light_points - pos_old, axis=1)
            nearest = int(distance.argmin())
            entry['light'] = {'name': lights[nearest]['name'], 'distance': round(float(distance[nearest])),
                              'radius': lights[nearest]['radius'], 'colour': lights[nearest]['colour']}
        entries.append(entry)
        report.append(f"{idx} {p['Name']} {prop}: fit median {fit:.2f}, worst vertex {d.max():.1f}{note}")
    (PROJECT / 'props.json').write_text(json.dumps(entries, indent=1) + '\n')
    fits = np.array([e['fit_median_units'] for e in entries])
    if '--verbose' in sys.argv:
        print('\n'.join(report))
    print('WROTE', PROJECT / 'props.json', len(entries), 'entries; fit median of medians',
          round(float(np.median(fits)), 2), 'worst', round(float(fits.max()), 2))
    for e in sorted(entries, key=lambda e: -e['fit_median_units'])[:8]:
        print('  ', e['source_object'], e['source_name'], e['prop'], e['fit_median_units'])
    lit = [e['light']['distance'] for e in entries if 'light' in e]
    names = [e['light']['name'] for e in entries if 'light' in e]
    print('lights: distance', min(lit), '-', max(lit), 'units;', len(set(names)), 'distinct of', len(names))
    print('\n'.join(r for r in report if 'floor' in r))


if __name__ == '__main__':
    main()
