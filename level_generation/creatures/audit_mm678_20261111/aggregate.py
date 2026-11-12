#!/usr/bin/env python3
"""Merge the MM6-MM8 audit measurements into one table per model (audit 2026-11-11).

    python3 level_generation/creatures/audit_mm678_20261111/aggregate.py

Reads bound_models.json, motion/*.json and texq/*.json (and the MM9 reference set motion_mm9/, texq_mm9/), the bound
role clips from each world's actors.yml, provenance_mm6.csv and provenance_mm78.csv. Writes table.json and table.csv.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
# `aggregate.py after` reads after/motion and after/texq (the re-measurement after the fixes) and writes after/table.json;
# the MM9 reference always comes from this folder.
OUT = HERE / sys.argv[1] if len(sys.argv) > 1 else HERE
REPO = HERE.parents[2]
COMBAT = ('attack_melee', 'attack_ranged', 'cast')
DEFORM_ROLES = ('attack_melee', 'attack_ranged', 'cast', 'hit', 'walking', 'run', 'sprint', 'fidget', 'standing')
LIVE_REGIONS = ('hand', 'arm', 'head', 'spine', 'leg', 'tail', 'wing', 'cloth')
# Folders in assets_dev/worlds/<w>/models/ whose own LOD0 sets are not body paint (effects, held items).
SKIP_MATERIAL = ('lod2', 'lod3', 'fringe', 'wind', 'burst', 'wisp', 'fish', 'ooze', 'flame', 'ash', 'spark', 'glow',
                 'arrow', 'bow', 'sword', 'staff', 'axe', 'club', 'mace', 'halberd', 'shield', 'dagger', 'knife')


def bindings():
    """model path -> {'worlds': [...], 'descriptors': [...], 'roles': {role: clip}} (first binding's roles)."""
    out = {}
    for world in ('mm6', 'mm7', 'mm8', 'mm9'):
        doc = yaml.safe_load((REPO / f'assets_dev/worlds/{world}/models/actors.yml').read_text())
        for actor in doc['actors']:
            model = actor.get('model')
            if not model:
                continue
            entry = out.setdefault(model, {'worlds': [], 'descriptors': [], 'roles': {}})
            if world not in entry['worlds']:
                entry['worlds'].append(world)
            entry['descriptors'].append(actor['descriptor'])
            if not entry['roles']:
                roles = dict(actor.get('clips') or {})
                animation = actor.get('animation') or {}
                for key in ('cast', 'run', 'sprint'):
                    if animation.get(key):
                        roles[key] = animation[key]
                entry['roles'] = roles
    return out


def body_type(motion):
    mesh = motion['mesh']
    clips = motion['clips']
    regions = set()
    for clip in clips.values():
        regions.update(clip.get('region_amp', {}))
    if mesh['hand_joints'] >= 2 and 'arm' in regions and 'leg' in regions:
        return 'biped'
    return 'other'


def texture(stem, folder):
    path = (HERE if folder.endswith('_mm9') else OUT) / folder / f'{stem}.json'
    if not path.exists():
        return None
    sets = json.loads(path.read_text())[0]['materials']
    body = [s for s in sets if not any(k in s['material'].lower() for k in SKIP_MATERIAL) and s['triangles'] >= 300]
    if not body:
        return None
    big = max(body, key=lambda s: s['triangles'])
    worst = min(body, key=lambda s: s['atlas_pct'])
    return {
        'material': big['material'], 'size': big['texture'], 'atlas_pct': big['atlas_pct'],
        'equivalent_px': big['equivalent_px'], 'fragment_pct': big['fragment_surface_pct'],
        'stretch_p90': big['stretch_p90'], 'spread': big['spread'],
        'worst_material': worst['material'], 'worst_atlas_pct': worst['atlas_pct'],
        'max_fragment_pct': max(s['fragment_surface_pct'] for s in body),
        'max_stretch_p90': max(s['stretch_p90'] for s in body),
    }


def clip_summary(motion, roles):
    clips = motion['clips']
    standing = clips.get(roles.get('standing', 'Standing'), {})
    base = {r: v['bad_pct'] for r, v in standing.get('deform', {}).items()}
    deform_worst = None
    for role in DEFORM_ROLES:
        name = roles.get(role)
        clip = clips.get(name) if name else None
        if not clip or 'deform' not in clip:
            continue
        for region, value in clip['deform'].items():
            if region not in LIVE_REGIONS:
                continue
            excess = value['bad_pct'] - base.get(region, 0.0)
            if deform_worst is None or excess > deform_worst['excess_pct']:
                deform_worst = {'role': role, 'clip': name, 'region': region, 'excess_pct': round(excess, 1),
                                'time': value['time'], 'hotspot': clip.get('hotspot')}
    hand_worst = None
    for role in ('attack_melee', 'attack_ranged', 'cast', 'hit', 'standing', 'walking', 'fidget', 'run'):
        name = roles.get(role)
        clip = clips.get(name) if name else None
        if clip and clip.get('hand_inside_pct', 0) > (hand_worst or {}).get('pct', -1):
            hand_worst = {'role': role, 'clip': name, 'pct': clip['hand_inside_pct'], 'time': clip['hand_inside_time'],
                          'depth': clip['hand_depth']}
    combat = {}
    for role in COMBAT:
        name = roles.get(role)
        clip = clips.get(name) if name else None
        if clip and clip.get('length_s', 0) > 0:
            combat[role] = {'clip': name, 'amp_p90': clip['amp_p90'], 'body_share': clip['body_share'],
                            'torso_turn_deg': clip['torso_turn_deg'], 'peak_speed': clip['peak_speed'],
                            'length_s': clip['length_s'], 'region_amp': clip['region_amp']}
    combat_names = [roles.get(r) for r in COMBAT if roles.get(r)]
    distinct = len(set(combat_names))
    pops = {n: c['loop_pop'] for n, c in clips.items() if c.get('loop_pop', 0) and c['loop_pop'] > 0.02}
    idle = clips.get(roles.get('standing', 'Standing'), {})
    fidget = clips.get(roles.get('fidget', 'Fidget'), {})
    walk_clip = roles.get('walking')
    attack_is_walk = any(roles.get(r) == walk_clip for r in ('attack_melee', 'attack_ranged'))
    return {
        'deform_worst': deform_worst, 'hand_worst': hand_worst, 'combat': combat,
        'combat_clip_names': combat_names, 'distinct_combat_clips': distinct, 'attack_is_walk': attack_is_walk,
        'loop_pops': pops, 'idle_amp_p90': idle.get('amp_p90'), 'fidget_amp_p90': fidget.get('amp_p90'),
        'fidget_len': fidget.get('length_s'), 'near_duplicates': motion.get('near_duplicates', []),
    }


def provenance():
    rows = {}
    for name in ('provenance_mm6.csv', 'provenance_mm78.csv'):
        path = HERE / name
        if path.exists():
            with path.open() as f:
                for row in csv.DictReader(f):
                    rows[row['model']] = row
    return rows


def main():
    bound = bindings()
    prov = provenance()
    table = {}
    reference = {'biped': [], 'other': []}
    for model, entry in bound.items():
        stem = Path(model).stem
        mm9 = entry['worlds'] == ['mm9']
        folder = 'motion_mm9' if mm9 else 'motion'
        path = (HERE if mm9 else OUT) / folder / f'{stem}.json'
        if not path.exists():
            continue
        motion = json.loads(path.read_text())
        row = {'model': stem, 'path': model, 'worlds': entry['worlds'], 'descriptors': entry['descriptors'],
               'mm9': mm9, 'body': body_type(motion), 'mesh': motion['mesh'],
               'texture': texture(stem, 'texq_mm9' if mm9 else 'texq'),
               **clip_summary(motion, entry['roles'])}
        if mm9:
            reference[row['body']].append(row)
        else:
            p = prov.get(stem, {})
            row['provenance'] = {k: p.get(k, '') for k in ('main_project', 'mesh_route', 'rig_route', 'clip_sources',
                                                           'texture_route', 'user_verdicts', 'known_open_issues')}
        table[stem] = row
    # MM9 reference percentiles of the attack measures, per body type.
    ref = {}
    for body, rows in reference.items():
        values = {k: [] for k in ('amp_p90', 'body_share', 'torso_turn_deg', 'peak_speed')}
        for row in rows:
            attack = row['combat'].get('attack_melee')
            if attack:
                for k in values:
                    values[k].append(attack[k])
        ref[body] = {k: {'n': len(v), 'p10': round(float(np.percentile(v, 10)), 3),
                         'p25': round(float(np.percentile(v, 25)), 3), 'p50': round(float(np.percentile(v, 50)), 3)}
                     for k, v in values.items() if v}
    (OUT / 'table.json').write_text(json.dumps({'mm9_reference': ref, 'models': table}, indent=1))
    print(json.dumps(ref, indent=1))


if __name__ == '__main__':
    main()
