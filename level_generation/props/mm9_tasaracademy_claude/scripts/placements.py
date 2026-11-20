#!/usr/bin/env python3
"""Writes level_generation/projects/mm9r_tasaracademy/props.json: every Prop, Brazier, CandleProp, TreasureChest,
Barrel, DestructableProp and PropDamager placement in the native frame (the old bmodel_world map's frame, which the BLV
keeps: no offset), each under its DAT object name (the map project attaches click events by it), and checks each end
to end as the Verhoffin Ruins's placements.py does (the Anskram Keep's rot, glb_lod0 and world_positions are reused):
the finished GLB's LOD0, placed the way the engine places a decoration model (glTF (x, y, z) -> OpenYAMM (-x, z, y),
scaled by binding height / bounds height, turned by the facing, at the entity position), against the old map's baked
BModel of the same DAT object (MM9_*_<object index>_*); median vertex distance printed. Reused decorations are checked
with their owning project's GLB and meta. Tipped books are compared with their pitch and roll applied.

Positions are the asset origin (base centre) of the old bake, which includes the transcoder's floor drop for
MoveToFloor objects. A model without flame cards is centred on its bake's box where that lowers the median (the
Klusos House rule). Exceptions, none of which the old bake can check:
  - the posed pickaxes (dwarfaxeonside: the bake is the ABC's bind pose) stand with their base on the floor under
    their DAT position (MoveToFloor 1), as Verhoffin's posed beds;
  - MM9 ships no Skillbook.abc: the six SkillBook.scr books (no bake) are the flat book lying on the highest surface
    (floor, desk or table bake) under their DAT position (MoveToFloor 1);
  - BookRules (book-rules.abc, no bake: the old transcoder skipped it) is placed from its DAT position and rotation
    as the transcoder places a model (binding origin, pitch and roll baked in the model, MoveToFloor 0).
Braziers and candles name the light MM9 placed beside each (the map project's work/lights.json when it exists, its kept
lights; else the nearest DAT Light object); their rows carry no light.
Usage: placements.py [--verbose]"""
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
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/tasaracademy.odm'
CLASS_KIND = {'Prop': 'prop', 'Brazier': 'torch', 'CandleProp': 'torch', 'TreasureChest': 'chest', 'Barrel': 'prop',
              'DestructableProp': 'prop', 'PropDamager': 'damager'}
QUEST = {'BookRules'}
LIT = {'Brazier', 'CandleProp'}
NO_MODEL = 'skillbook.abc'


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


def surface_below(bmodels, point, props=False, skip=None):
    """Highest upward face under point, at or below it + 8: the world geometry, plus the prop bakes when props
    (a desk or table under a book), never the bake named skip."""
    best = None
    for b in bmodels:
        if b['name'] == skip or (b['name'].startswith('MM9_') and not props):
            continue
        verts = np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float)
        lo, hi = verts.min(0), verts.max(0)
        if not (lo[0] - 1 <= point[0] <= hi[0] + 1 and lo[1] - 1 <= point[1] <= hi[1] + 1 and lo[2] <= point[2] + 8):
            continue
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


def light_list(raw):
    """The map project's kept lights (work/lights.json), else the DAT Light objects."""
    path = PROJECT / 'work/lights.json'
    if path.exists():
        return [l for l in json.loads(path.read_text()) if l['kept']], 'lights.json'
    out = []
    for o in raw.values():
        p = o['props']
        if o['class'] == 'Light':
            out.append({'name': p['Name'], 'position': [p['Pos'][0] * 2.56, p['Pos'][2] * 2.56, p['Pos'][1] * 2.56],
                        'radius': int(round(float(p.get('LightRadius', 0)) * 2.56)),
                        'colour': [int(v) for v in p.get('LightColor', [255, 255, 255])]})
    return out, 'DAT Light objects'


def main():
    bmodels = load_map()
    baked = {b['name']: np.array([[a['x'], a['y'], a['z']] for a in b['vertices']], float) for b in bmodels}
    plan = json.loads((props_table.HERE / 'work/decorations_plan.json').read_text())
    raw = {o['index']: o for o in props_table.objects()}
    lights, light_source = light_list(raw)
    light_points = np.array([l['position'] for l in lights], float)
    entries, report, unchecked = [], [], []
    for idx, prop in props_table.placements():
        o = raw[idx]
        p = o['props']
        s = float(p.get('Scale', 1.0))
        ry = float(p['Rotation'][1])
        pos_old = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
        home = props_table.home(prop)
        meta = json.loads((home / f'work/{prop}_meta.json').read_text())
        variant = next(d for d in plan if d['prop'] == prop and abs(d['scale'] - s) < 1e-3)
        no_model = props_table.key(p['Filename']).endswith(NO_MODEL)
        g = world_positions(home / f'work/raw/{prop}/{prop}.glb') + np.array(props_table.binding_origin(prop)) * 2.56
        local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
        if prop in props_table.BOOK_TILT:
            local = tilt_oy(local, *props_table.BOOK_TILT[prop])
        inst = (local * s) @ rot(-ry).T + pos_old
        bake_name = next((k for k in baked if k.startswith('MM9_') and f'_{idx}_' in k), None)      # by object index
        bake = baked.get(bake_name)
        extra = np.zeros(3) if bake is None or prop in props_table.POSES else \
            (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
        position = pos_old + extra + rot(-ry) @ (np.array(meta['origin_local_units']) * s)
        note = ''
        if prop in props_table.POSES:         # posed (the pickaxes on their side): the bake is the bind pose; MM9
            floor = surface_below(bmodels, pos_old + np.array([0, 0, 4]))     # drops them to the shelf
            note = f' (posed: base on the floor at {floor:.1f}; DAT z {pos_old[2]:.1f})'
            position[2] = floor
        if no_model:                          # the skill books: MM9 has no model; the flat book on the surface below
            surface = surface_below(bmodels, pos_old + np.array([0, 0, 4]), props=True)
            note = f' (no MM9 model: stand-in on the surface at {surface:.1f}; DAT z {pos_old[2]:.1f})'
            position = np.array([pos_old[0], pos_old[1], surface])     # centred on the DAT position
        a = glb_lod0(home / f'work/mm9_deco_{prop}.glb')
        engine_scale = variant['height'] / (a[:, 1].max() - a[:, 1].min())
        placed = np.stack([-a[:, 0], a[:, 2], a[:, 1]], 1) * engine_scale @ rot(-ry).T + position
        if meta.get('flame_head_m'):          # the flame cards are not in the bake
            placed = placed[a[:, 1] * engine_scale < (meta['flame_head_m'][2] * 81.7 * engine_scale) - 1]
        fit = None
        if bake is not None and not no_model:
            tree = cKDTree(bake)
            # A turned model's raw import is not the placed mesh (the Chasm's placements): centre the placed mesh on
            # the bake's box, models without flame cards only, kept only where it fits better (Klusos House).
            if not meta.get('flame_head_m') and prop not in props_table.POSES:
                shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
                if np.median(tree.query(placed + shift)[0]) < np.median(tree.query(placed)[0]):
                    position, placed = position + shift, placed + shift
            d, _ = tree.query(placed)
            fit = float(np.median(d))
            worst = float(d.max())
        entry = {'source_object': idx, 'source_name': p['Name'], 'class': o['class'],
                 'kind': 'quest' if p['Name'] in QUEST else CLASS_KIND[o['class']],
                 'source_model': p['Filename'], 'source_skin': p.get('Skin'), 'prop': prop,
                 'decoration': variant['decoration'], 'x': round(float(position[0]), 1),
                 'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1),
                 'yaw_degrees': round(math.degrees(-ry) % 360.0, 2),
                 'fit_median_units': round(fit, 2) if fit is not None else None}
        if p.get('ScriptName'):
            entry['script'] = f"{p['ScriptName']} {p.get('ScriptParams') or ''}".strip()
        if o['class'] in LIT:
            distance = np.linalg.norm(light_points - pos_old, axis=1)
            nearest = int(distance.argmin())
            entry['light'] = {'name': lights[nearest]['name'], 'distance': round(float(distance[nearest])),
                              'radius': lights[nearest]['radius'], 'colour': lights[nearest]['colour']}
        entries.append(entry)
        if fit is None or prop in props_table.POSES:
            unchecked.append(f"{idx} {p['Name']} {prop}{note}" + (f' (bake fit {fit:.2f}: bind pose)' if fit else ''))
        else:
            report.append(f"{idx} {p['Name']} {prop}: fit median {fit:.2f}, worst vertex {worst:.1f}{note}")
    (PROJECT / 'props.json').write_text(json.dumps(entries, indent=1) + '\n')
    checked = [e for e in entries if e['fit_median_units'] is not None and e['prop'] not in props_table.POSES]
    fits = np.array([e['fit_median_units'] for e in checked])
    if '--verbose' in sys.argv:
        print('\n'.join(report))
    from collections import Counter
    print('WROTE', PROJECT / 'props.json', len(entries), 'entries', dict(Counter(e['kind'] for e in entries)),
          '; checked', len(checked), 'fit median of medians', round(float(np.median(fits)), 2),
          'worst', round(float(fits.max()), 2))
    for e in sorted(checked, key=lambda e: -e['fit_median_units'])[:10]:
        print('  ', e['source_object'], e['source_name'], e['prop'], e['fit_median_units'])
    print('not checked against a bake:\n  ' + '\n  '.join(unchecked))
    lit = [e['light']['distance'] for e in entries if 'light' in e]
    names = [e['light']['name'] for e in entries if 'light' in e]
    print('lights (' + light_source + '): distance', min(lit), '-', max(lit), 'units;', len(set(names)), 'distinct of',
          len(names))


if __name__ == '__main__':
    main()
