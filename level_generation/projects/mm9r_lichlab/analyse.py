#!/usr/bin/env python3
"""
Lich Lab, MM9 rework: analysis of the DAT world before the conversion (phase A).

    python3 level_generation/projects/mm9r_lichlab/analyse.py

Writes work/dat_objects.json (every DAT object with its properties), work/analysis.json (every world model with its
class, bounds and the rule overrides.yml gives it; the doors, UserPortals, lights, exits, triggers, scripted objects,
chests and monsters with their positions in LithTech and native units) and work/plan_<level>.png (top-down plans of
the four floor levels: floors by height, walls, door leaves, UserPortals, triggers, labels), which the archway cuts in
overrides.yml are chosen on. Native = (LT.x, LT.z, LT.y) * 2.56 (the old bmodel_world map's frame).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'tools/mm9_import_discovery'))
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402

DAT = ROOT / 'mm9/extracted/WORLDS/WORLDS/LICHLAB.dat'
WORK = PROJECT / 'work'
SCALE = 2.56
MONSTERS = {'SkeletonMaster', 'FlyingIcky', 'Oculus', 'Dagrell', 'PowerLich', 'LichKing', 'VenomousDagrell', 'Eye',
            'Lich', 'Revenant', 'Ghast', 'SpectreDagrell'}
# Floor levels (LithTech y bands of floor polygons) for the plans.
LEVELS = {'basement': (-500, -150), 'ground': (-150, 350), 'upper': (350, 800), 'top': (800, 1500)}
PX = 0.25                       # pixels per LithTech unit


def value(v):
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    try:
        return [value(x) for x in v]
    except TypeError:
        return str(v)


def native(p):
    return [round(p[0] * SCALE, 1), round(p[2] * SCALE, 1), round(p[1] * SCALE, 1)]


def main():
    WORK.mkdir(exist_ok=True)
    world = read_dat_world(DAT)
    objects = []
    for index, o in enumerate(world.objects):
        objects.append({'i': index, 'class': o.name, 'props': {p.name: value(p.value) for p in o.properties}})
    (WORK / 'dat_objects.json').write_text(json.dumps(objects, indent=1))
    by_name = {o['props'].get('Name', '').lower(): o for o in objects}
    overrides = yaml.safe_load((PROJECT / 'overrides.yml').read_text()) if (PROJECT / 'overrides.yml').exists() else {}
    rules = overrides.get('models', {})

    models = []
    for m in world.world_models:
        points = np.array(m.points, float) if len(m.points) else np.zeros((1, 3))
        cls = by_name.get(m.name.lower(), {}).get('class')
        models.append({'name': m.name, 'class': cls, 'polies': len(m.polies),
                       'min_lt': points.min(0).round(1).tolist(), 'max_lt': points.max(0).round(1).tolist(),
                       'rule': rules.get(m.name)})
    portals = [{'name': u.name, 'centre_lt': list(np.round(u.center, 1)), 'dims_lt': list(np.round(u.dims, 1))}
               for u in next(m for m in world.world_models if m.name == 'VisBSP').user_portals]

    def entry(o, keys):
        p = o['props']
        out = {'name': p.get('Name'), 'class': o['class'], 'index': o['i'], 'pos_lt': [round(x, 1) for x in p['Pos']],
               'pos_native': native(p['Pos'])}
        out.update({k: p.get(k) for k in keys if p.get(k) not in (None, '', 0, 0.0)})
        return out

    door_keys = ['PortalName', 'DoubleDoorName', 'RotationAngles', 'RotationPoint', 'MoveDist', 'MoveDir', 'Speed',
                 'StartOpen', 'Sticky', 'PushOpen', 'TouchToOpen', 'Locked', 'CloseWaitTime'] + \
                [f'{a}Trigger{b}{c}' for a in ('Open', 'Close') for c in range(4) for b in ('Target', '')]
    analysis = {
        'counts': dict(Counter(o['class'] for o in objects).most_common()),
        'models': models,
        'user_portals': portals,
        'doors': [entry(o, door_keys) for o in objects if o['class'] in ('RotatingDoor', 'Door', 'Switch')],
        'lights': [entry(o, ['LightRadius', 'LightColor', 'Radius', 'Color', 'BrightScale']) for o in objects
                   if o['class'] in ('Light', 'GlowingLight')],
        'exits': [entry(o, ['Dims', 'DestinationWorld', 'StartPointName', 'AskPlayer']) for o in objects
                  if o['class'] == 'ExitTrigger'],
        'starts': [entry(o, ['Rotation']) for o in objects if o['class'] == 'StartPoint'],
        'triggers': [entry(o, ['Dims', 'TriggerTouch', 'PlayerTriggerable', 'StartOn'] +
                           [f'{a}{i}' for i in range(1, 11) for a in ('TargetName', 'MessageName')])
                     for o in objects if o['class'] == 'Trigger'],
        'scripted': [entry(o, ['ScriptName', 'ScriptParams', 'Filename']) for o in objects
                     if o['props'].get('ScriptName') and o['class'] not in MONSTERS],
        'shooters': [entry(o, ['Rotation', 'ProjectileName', 'DamageAmt', 'StartOn']) for o in objects
                     if o['class'] == 'Shooter'],
        'destructibles': [entry(o, ['HitPoints', 'DeathTriggerTarget', 'DeathTriggerMessage', 'Glass', 'Wood'])
                          for o in objects if o['class'] == 'DestructableBrush'],
        'chests': [entry(o, ['Filename', 'TreasureLevel', 'TrapLevel', 'TreasureType0_7']) for o in objects
                   if o['class'] == 'TreasureChest'],
        'monsters': [entry(o, ['Scale', 'ScriptName', 'ScriptParams', 'WanderPathName']) for o in objects
                     if o['class'] in MONSTERS],
        'fires': [entry(o, ['LightMaxRadius', 'LightColor1', 'On']) for o in objects if o['class'] == 'Fire'],
        'water': [entry(o, ['Viscosity', 'SurfaceHeight', 'Damage']) for o in objects if o['class'] == 'BlueWater'],
    }
    analysis['monster_classes'] = dict(Counter(m['class'] for m in analysis['monsters']).most_common())
    (WORK / 'analysis.json').write_text(json.dumps(analysis, indent=1))
    plans(world, objects, portals)
    print('models', len(models), 'portals', len(portals), 'doors', len(analysis['doors']), 'lights',
          len(analysis['lights']), 'monsters', len(analysis['monsters']), analysis['monster_classes'])


def plans(world, objects, portals):
    physics = next(m for m in world.world_models if m.name == 'PhysicsBSP')
    points = np.array(physics.points, float)
    lo, hi = points.min(0), points.max(0)
    width, height = int((hi[0] - lo[0]) * PX) + 40, int((hi[2] - lo[2]) * PX) + 40

    def xy(p):          # top-down, north (+z) up
        return (20 + (p[0] - lo[0]) * PX, 20 + (hi[2] - p[2]) * PX)

    polys = []
    for poly in physics.polies:
        ring = ring_of(poly)
        if len(ring) < 3:
            continue
        p = points[ring]
        n = np.cross(p - p.mean(0), np.roll(p, -1, 0) - p.mean(0)).sum(0)
        if np.linalg.norm(n) < 1e-9:
            continue
        polys.append((p, n / np.linalg.norm(n)))
    font = ImageFont.load_default()
    doors = {o['props']['Name']: o for o in objects if o['class'] in ('RotatingDoor', 'Door', 'Switch')}
    leaf_models = {m.name: np.array(m.points, float) for m in world.world_models if m.name in doors}
    for level, (y0, y1) in LEVELS.items():
        image = Image.new('RGB', (width, height), (20, 20, 24))
        draw = ImageDraw.Draw(image)
        for p, n in polys:
            if n[1] > 0.7 and y0 <= p[:, 1].mean() < y1:
                t = (p[:, 1].mean() - y0) / (y1 - y0)
                draw.polygon([xy(q) for q in p], fill=(int(60 + 150 * t), int(90 + 60 * (1 - t)), 120))
        for p, n in polys:
            if abs(n[1]) < 0.3 and p[:, 1].min() < y1 and p[:, 1].max() > y0 + 40:
                draw.line([xy(q) for q in p] + [xy(p[0])], fill=(230, 230, 230), width=1)
        for name, pts in leaf_models.items():
            if y0 - 64 <= pts[:, 1].min() < y1:
                a, b = xy(pts.min(0)), xy(pts.max(0))
                draw.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], outline=(255, 60, 60))
        for u in portals:
            c = np.array(u['centre_lt'])
            if y0 - 64 <= c[1] < y1 + 64:
                d = np.array(u['dims_lt'])
                a, b = xy(c - d), xy(c + d)
                draw.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], outline=(80, 160, 255), width=2)
        for o in objects:
            p = o['props']
            if 'Pos' not in p or not (y0 - 64 <= p['Pos'][1] < y1):
                continue
            colour = {'Trigger': (255, 200, 0), 'ExitTrigger': (0, 255, 0), 'StartPoint': (0, 255, 0),
                      'TreasureChest': (255, 255, 0), 'ScriptObject': (255, 0, 255), 'Shooter': (255, 128, 0),
                      'DestructableBrush': (255, 120, 200)}.get(o['class'])
            if o['class'] in MONSTERS:
                colour = (200, 40, 40)
            if colour is None:
                continue
            x, y = xy(p['Pos'])
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=colour)
            if o['class'] not in MONSTERS:
                draw.text((x + 4, y - 4), p['Name'], fill=colour, font=font)
        step = 512
        for gx in range(int(lo[0] // step) * step, int(hi[0]) + 1, step):
            draw.text(xy((gx, 0, hi[2])), str(gx), fill=(120, 120, 120), font=font)
        for gz in range(int(lo[2] // step) * step, int(hi[2]) + 1, step):
            draw.text(xy((lo[0], 0, gz)), str(gz), fill=(120, 120, 120), font=font)
        image.save(WORK / f'plan_{level}.png')


def ring_of(poly):
    """A v66 poly's base ring (the reader appends the same ring again with its T-junction vertices; a plan needs only
    the outline)."""
    indices = [vertex.vertex_index for vertex in poly.disk_verts]
    for split in range(3, len(indices)):
        if indices[split] == indices[0]:
            return indices[:split]
    return indices


if __name__ == '__main__':
    main()
