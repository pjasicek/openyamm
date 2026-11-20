#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_isleofashes/props.json: every isle prop and tree placement in the remade
map's frame (work/transform.json: new = old - (offset_x, offset_y, sea_level_lt * 2.56)), and checks each converted
prop end to end: the finished GLB's LOD0, placed the way the engine places a decoration model (glTF (x, y, z) ->
OpenYAMM (-x, z, y), scaled by binding height / bounds height, turned by the facing, at the entity position), must
cover the old isle's baked BModel of the same object (median vertex distance printed; under 2 units expected).

Positions: the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. `snap_to_ground`: true when that base is within SNAP units of MM9's own terrain surface
(ground.terrain_top: the terrain polygons the conversion reads), so the prop stands on the terrain and follows the
remade height map; false for props on structures (castle top, bunker, hut floor), afloat or sunk (the boats, the
wreck) or hung on a wall (the coat rack): keep z. Both distances are written per entry.
Usage: placements.py"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fitlib import HERE, REPO, bmodel_vertices, bmodels, rot  # noqa: E402
from glbio import array, read_glb, world_positions  # noqa: E402
from ground import ground, terrain_top  # noqa: E402
import props_table  # noqa: E402

SNAP = 6.0
PROJECT = REPO / 'level_generation/projects/mm9r_isleofashes'
TRANSFORM = json.loads((PROJECT / 'work/transform.json').read_text())
# Objects left out of props.json: duplicates in the same spot.
SKIP = {561: 'duplicate of 766 (the same log pile at scale 0.7 inside the 0.75 one, each with its own Fire object)'}
# Forced z handling (else by distance to the remade terrain).
KEEP = {481: 'sunk wreck: keep z', 492: 'afloat: keep z', 493: 'afloat: keep z', 763: 'wall mounted: keep z',
        766: 'in the hut beside the table (MM9 terrain level, 10 below the hut floor the furniture drops to): keep z',
        761: 'on the hut floor: keep z', 762: 'on the hut floor: keep z',
        67: 'MM9 sets it about 300 over the terrain (on a rock or structure, check): keep z',
        477: 'MM9 sets it about 240 over the terrain (on a rock or structure, check): keep z'}
# MoveToFloor 0 objects whose MM9 position is their base (bottom on the floor), not their centre as the old bake
# assumed: the hut stools (centred on Pos they would sink half into the floor the cot and table stand on).
BASE_AT_POS = {761, 762}
# Gameplay classes the other session binds events to.
INTERACTIVE = {'StatStone': 'MM9 StatStone (stat bonus stone)', 'WellMMIX': 'MM9 WellMMIX (drinkable well)',
               'Cookpot': 'MM9 Cookpot'}
# Trees: an existing OpenYAMM pine per MM9 tree model; target height = the MM9 tree's whole height (ABC y -66.1 to
# 431.5 / 320.7 LithTech units: 497.6 / 386.8; the trunk foot stands on the tree's Pos, which is at the terrain)
# x 2.56 x the object's Scale.
TREES = {'ref_tree05': {'decoration': 'tree29', 'top_lt': 497.6, 'binding_height': 976.0},
         'ref_tree06': {'decoration': 'tree30', 'top_lt': 386.8, 'binding_height': 1000.0}}


def decoration_rows():
    rows = {}
    for line in (REPO / 'assets_dev/engine/data_tables/decoration_data.txt').read_text().splitlines():
        cells = line.split('\t')
        if cells and cells[0].strip().isdigit():
            rows[cells[1].strip().lower()] = int(cells[0])
    return rows


def plan():
    return json.loads((HERE / 'work/decorations_plan.json').read_text())


def to_new(p):
    return [p[0] - TRANSFORM['offset_x'], p[1] - TRANSFORM['offset_y'],
            p[2] - TRANSFORM['sea_level_lt'] * TRANSFORM['scale']]


def glb_lod0(path):
    document, binary = read_glb(path)
    node = next(n for n in document['nodes'] if 'mesh' in n)
    return np.concatenate([array(document, binary, p['attributes']['POSITION'])
                           for p in document['meshes'][node['mesh']]['primitives']])


def main():
    rows = decoration_rows()
    decorations = plan()
    raw = {o['index']: o for o in props_table.objects()}
    entries, report = [], []
    for idx, prop in props_table.placements():
        o = raw[idx]; p = o['props']
        s = float(p.get('Scale', 1.0))
        ry = float(p['Rotation'][1])
        pos_old = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        if idx in SKIP:
            report.append(f'{idx} {p["Name"]}: skipped, {SKIP[idx]}')
            continue
        if prop in TREES:
            t = TREES[prop]
            x, y, _ = to_new(pos_old)
            height = t['top_lt'] * 2.56 * s
            entries.append({'source_object': idx, 'source_name': p['Name'], 'source_model': p['Filename'],
                            'decoration': t['decoration'], 'decoration_list_id': rows[t['decoration']] - 1,
                            'x': round(x, 1), 'y': round(y, 1), 'z': round(ground(x, y), 1),
                            'yaw_degrees': round(math.degrees(-ry) % 360.0, 2),
                            'scale': round(height / t['binding_height'], 3), 'target_height': round(height, 1),
                            'snap_to_ground': True})
            continue
        meta = json.loads((HERE / f'work/{prop}_meta.json').read_text())
        variant = next(d for d in decorations if d['prop'] == prop and abs(d['scale'] - s) < 1e-3)
        # where the old bake put the model: its raw vertices through the transcoder's formula, matched to the BModel
        g = world_positions(HERE / f'work/raw/{prop}/{prop}.glb') + np.array(props_table.binding_origin(prop)) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        if meta.get('tilt'):
            local = tilt_oy(local, *meta['tilt'])
        inst = (local * s) @ rot(-ry).T + pos_old
        name = f"MM9_static_prop_{idx}_{p['Name']}"
        B = bmodel_vertices(name)
        extra = (B.min(0) + B.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        if idx in BASE_AT_POS:
            position[2] = pos_old[2]
        # end-to-end: the finished asset as the engine places it
        a = glb_lod0(HERE / f'work/mm9_deco_{prop}.glb')
        bounds_h = a[:, 1].max() - a[:, 1].min()
        engine_scale = variant['height'] / bounds_h
        oy = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale
        placed = oy @ rot(-ry).T + position
        if meta.get('fire_from_units') is not None:
            placed = placed  # flame cards are part of LOD0; the BModel has none, so the median ignores them
        if idx in BASE_AT_POS:
            placed[:, 2] -= position[2] - (pos_old[2] + extra[2] + meta['origin_local_units'][2] * s)
        d, _ = cKDTree(B).query(placed)
        d2, _ = cKDTree(placed).query(B)
        new = to_new(position)
        above = new[2] - ground(new[0], new[1])
        top = terrain_top(new[0], new[1])
        above_terrain = None if top is None else new[2] - top
        snap = idx not in KEEP and above_terrain is not None and abs(above_terrain) <= SNAP
        entry = {'source_object': idx, 'source_name': p['Name'], 'source_model': p['Filename'],
                 'decoration': variant['decoration'],
                 'decoration_list_id': (rows[variant['decoration']] - 1) if variant['decoration'] in rows
                 else variant['provisional_id'] - 1,
                 'x': round(new[0], 1), 'y': round(new[1], 1), 'z': round(new[2], 1),
                 'yaw_degrees': round(math.degrees(-ry) % 360.0, 2), 'scale': 1.0,
                 'snap_to_ground': bool(snap),
                 'base_above_mm9_terrain': None if above_terrain is None else round(above_terrain, 1),
                 'base_above_remade_ground': round(above, 1)}
        if variant['decoration'] not in rows:
            entry['decoration_list_id_provisional'] = True
        if not snap:
            entry['keep_z_reason'] = KEEP.get(idx, 'on a structure (castle, bunker or hut floor) in MM9')
        if o['class'] in INTERACTIVE:
            entry['interactive'] = INTERACTIVE[o['class']]
        entries.append(entry)
        report.append(f'{idx} {p["Name"]} {prop}: fit median {np.median(d):.2f} (bake->asset {np.median(d2):.2f}) '
                      f'units, base {above:+.0f} over the remade ground, {above_terrain if above_terrain is None else round(above_terrain)} '
                      f'over the MM9 terrain, snap {snap}')
    out = PROJECT / 'props.json'
    out.write_text(json.dumps(entries, indent=1) + '\n')
    print('\n'.join(report))
    print('WROTE', out, len(entries), 'entries')


def tilt_oy(local, pitch, roll):
    """The transcoder's object pitch (about x) then roll (about y), in OpenYAMM-local axes."""
    cx, sx, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ryy = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return local @ (ryy @ rx).T


if __name__ == '__main__':
    main()
