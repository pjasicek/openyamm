#!/usr/bin/env python3
"""Write assets_dev/engine/world_items/held.yml: how the solo run's first-person arms hold each weapon, shield and bow
ground model (game/render/HeldWeapons.h, devdocs/solo_action/WEAPONS.md "Held weapons in the game").

For every icon of a weapon, shield or bow row of items.txt with a ground model, the script reads the source model
(assets_source/engine/world_items/models/item_<icon>.glb), finds its shaft (the longer horizontal axis), which end is
the head and which side the edge faces from the width profile, and writes the grip by kind. OVERRIDES holds the hand
corrections found on the in-game contact sheets; they win over the measurement and survive a regeneration, so edit
them here, never in held.yml.

Usage: python3 make_held_table.py [--check]   (--check: report differences, write nothing)
"""
import csv
import json
import statistics
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ITEMS = ROOT / 'assets_dev/engine/data_tables/items.txt'
MODELS = ROOT / 'assets_source/engine/world_items/models'
BINDINGS = ROOT / 'assets_dev/engine/world_items/items.yml'
OUT = ROOT / 'assets_dev/engine/world_items/held.yml'

# kind: (held length in the arms' units, grip as a fraction from the butt; None: just below a blade's guard)
# Lengths follow Oblivion's own weapons (longsword 79, claymore 96, war axe 48, mace 53, steel shield 47 high, bow 107).
KINDS = {
    'dagger': (32, None), 'sword': (79, None), 'shortsword': (79, None), 'greatsword': (96, None),
    'axe': (50, 0.30), 'greataxe': (66, 0.25), 'mace': (53, 0.30), 'hammer': (62, 0.30), 'club': (55, 0.25),
    'staff': (115, 0.25), 'spear': (130, 0.30), 'trident': (130, 0.30), 'polearm': (140, 0.28),
    'poleaxe': (125, 0.28),
    'wand': (30, 0.20), 'blaster': (45, 0.25), 'bow': (107, 0.5), 'crossbow': (70, 0.55), 'shield': (47, 0.5),
}

# Staves and polearms: their shafts are thinned to this diameter where the hands close (arms' units).
LONG_SHAFTS = ('staff', 'spear', 'trident', 'polearm', 'poleaxe')
SHAFT_DIAMETER = 3.2

# Hand corrections from the contact sheets (icon: fields to replace; flip: True turns the head to the other end
# before the grip is measured).
OVERRIDES = {
    '7item003': {'flip': True},   # Gladius-like blade: its guard reads narrower than the pommel ring
    'item242': {'flip': True},    # Spiritslayer: the skull pommel outweighs the point
}
# Contact sheets checked (Blender, the engine's placement): reference/oblivion_poc/preview/held/.


def classify(equip, group, name):
    n = name.lower()
    if equip == 'Shield':
        return 'shield'
    if equip == 'Missile':
        return 'crossbow' if 'crossbow' in n else 'bow'
    if group == 'Dagger':
        return 'dagger'
    if group == 'Sword':
        if equip == 'Weapon2':
            return 'greatsword'
        # Cutlasses, scimitars, sabres and falchions: short curved blades, held as the short sword template.
        return 'shortsword' if any(w in n for w in ('cutlass', 'scimitar', 'saber', 'sabre', 'falchion')) else 'sword'
    if group == 'Axe':
        if 'poleaxe' in n:
            return 'poleaxe'
        return 'greataxe' if equip == 'Weapon2' else 'axe'
    if group == 'Mace':
        return 'hammer' if any(w in n for w in ('hammer', 'maul', 'sledge', 'thor', 'mash')) else 'mace'
    if group == 'Club':
        return 'club'
    if group == 'Staff':
        return 'staff'
    if group == 'Spear':
        if any(w in n for w in ('halberd', 'voulge', 'pole-axe', 'poleaxe', 'gibbet')):
            return 'polearm'
        if any(w in n for w in ('trident', 'fork', 'grapple', 'poseidon')):
            return 'trident'
        return 'spear'
    if group == 'Blaster':
        return 'blaster'
    if equip == 'WeaponW':
        return 'wand'
    return None


def positions(path):
    data = path.read_bytes()
    size = struct.unpack('<I', data[12:16])[0]
    doc = json.loads(data[20:20 + size])
    offset = 20 + size
    blob = data[offset + 8:offset + 8 + struct.unpack('<I', data[offset:offset + 4])[0]]
    points = []
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            accessor = doc['accessors'][primitive['attributes']['POSITION']]
            view = doc['bufferViews'][accessor['bufferView']]
            stride = view.get('byteStride', 12)
            base = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
            for k in range(accessor['count']):
                points.append(struct.unpack('<3f', blob[base + k * stride:base + k * stride + 12]))
    return points


def measure(points, kind, flip=False):
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    ext = [hi[i] - lo[i] for i in range(3)]
    long_axis = 0 if ext[0] >= ext[2] else 2
    edge_axis = 2 - long_axis
    length = ext[long_axis]

    def slice_points(t0, t1):
        a, b = lo[long_axis] + t0 * length, lo[long_axis] + t1 * length
        return [p for p in points if a <= p[long_axis] <= b]

    def width(t0, t1):
        s = [p[edge_axis] for p in slice_points(t0, t1)]
        return (max(s) - min(s)) if s else 0.0

    def flatness(t0, t1):
        s = slice_points(t0, t1)
        if not s:
            return 0.0
        across = max(p[edge_axis] for p in s) - min(p[edge_axis] for p in s)
        thick = max(p[1] for p in s) - min(p[1] for p in s)
        return across / max(thick, 1e-6)

    def mean_across(t0, t1):
        s = [p[edge_axis] for p in slice_points(t0, t1)]
        return statistics.fmean(s) if s else (lo[edge_axis] + hi[edge_axis]) / 2

    widest_t, widest_w = 0.5, -1.0
    for k in range(100):
        w = width(k / 100, (k + 1) / 100)
        if w > widest_w:
            widest_t, widest_w = k / 100 + 0.005, w
    low_mean = statistics.fmean(width(k / 100, (k + 1) / 100) for k in range(0, 25))
    high_mean = statistics.fmean(width(k / 100, (k + 1) / 100) for k in range(75, 100))

    entry = {'long': 'x' if long_axis == 0 else 'z', 'head': 1, 'edge': 1}
    if kind in ('dagger', 'sword', 'shortsword', 'greatsword'):
        # The widest slice is the guard; the tip is the end away from it.
        entry['head'] = 1 if widest_t < 0.5 else -1
    elif kind in ('axe', 'greataxe', 'poleaxe', 'mace', 'hammer', 'club', 'shield'):
        entry['head'] = 1 if widest_t >= 0.5 else -1
    elif kind == 'blaster':
        entry['head'] = 1 if high_mean < low_mean else -1
    elif kind in ('bow', 'crossbow'):
        entry['head'] = 1 if widest_t >= 0.5 else -1
    else:
        # Spears, tridents, polearms, staves, wands: a blade or prongs are flat (wide across, thin through) where a butt
        # cap is round, which decides clearly when one end is flat; otherwise the head carries more width over the end
        # quarter than a butt cap.
        low_flat = statistics.fmean(flatness(k / 100, (k + 1) / 100) for k in range(0, 15))
        high_flat = statistics.fmean(flatness(k / 100, (k + 1) / 100) for k in range(85, 100))
        if max(low_flat, high_flat) >= 2.0 and max(low_flat, high_flat) >= 2.0 * max(min(low_flat, high_flat), 1e-6):
            entry['head'] = 1 if high_flat > low_flat else -1
        else:
            entry['head'] = 1 if high_mean >= low_mean else -1

    if flip:
        entry['head'] = -entry['head']
    span_w = max(ext[edge_axis], 1e-6)
    if kind in ('axe', 'greataxe', 'poleaxe', 'polearm'):
        # The blade is on the side the head reaches further from the shaft's line.
        head_lo, head_hi = (0.7, 1.0) if entry['head'] > 0 else (0.0, 0.3)
        shaft_lo, shaft_hi = (0.0, 0.5) if entry['head'] > 0 else (0.5, 1.0)
        shaft = mean_across(shaft_lo, shaft_hi)
        head_pts = [p[edge_axis] for p in slice_points(head_lo, head_hi)]
        if head_pts:
            entry['edge'] = 1 if (max(head_pts) - shaft) >= (shaft - min(head_pts)) else -1
        entry['across'] = round(min(max((shaft - lo[edge_axis]) / span_w, 0.0), 1.0), 3)
    elif kind == 'bow':
        riser = mean_across(0.45, 0.55)
        tips = statistics.fmean([mean_across(0.0, 0.06), mean_across(0.94, 1.0)])
        entry['edge'] = 1 if tips < riser else -1
        entry['across'] = round(min(max((riser - lo[edge_axis]) / span_w, 0.0), 1.0), 3)
    elif kind == 'blaster':
        # The barrel's line at the muzzle; the handle hangs to the side the rear reaches further from it, and the palm
        # sits halfway down the handle.
        rear = (0.0, 0.4) if entry['head'] > 0 else (0.6, 1.0)
        barrel = mean_across(0.7, 1.0) if entry['head'] > 0 else mean_across(0.0, 0.3)
        rear_pts = [p[edge_axis] for p in slice_points(*rear)]
        hang = max(rear_pts) if (max(rear_pts) - barrel) >= (barrel - min(rear_pts)) else min(rear_pts)
        entry['edge'] = 1 if hang > barrel else -1
        entry['across'] = round(min(max(((barrel + hang) / 2 - lo[edge_axis]) / span_w, 0.0), 1.0), 3)
    else:
        shaft = mean_across(0.0, 0.3) if entry['head'] > 0 else mean_across(0.7, 1.0)
        if kind not in ('shield', 'crossbow'):
            entry['across'] = round(min(max((shaft - lo[edge_axis]) / span_w, 0.0), 1.0), 3)

    held_length, grip = KINDS[kind]
    if grip is None:
        guard_from_butt = widest_t if entry['head'] > 0 else 1 - widest_t
        grip = max(0.04, guard_from_butt - 0.06)
    entry['grip'] = round(grip, 3)
    if kind in LONG_SHAFTS:
        # The shaft's thickness where the hands close, at the held scale: thinned to SHAFT_DIAMETER (a hand's grip;
        # Oblivion's claymore grip is about 2.8 units).
        centre = grip if entry['head'] > 0 else 1 - grip
        for window in (0.06, 0.15):
            around = slice_points(max(0.0, centre - window), min(1.0, centre + window))
            if around:
                thick = max(max(p[edge_axis] for p in around) - min(p[edge_axis] for p in around),
                            max(p[1] for p in around) - min(p[1] for p in around))
                held = thick * held_length / length
                if held > SHAFT_DIAMETER:
                    # A bladed head shares the cross axes, so a polearm thins less than a plain staff.
                    floor = 0.45 if kind == 'staff' else 0.7
                    entry['girth'] = round(max(SHAFT_DIAMETER / held, floor), 3)
                break
    return entry, length


def main():
    check = '--check' in sys.argv
    rows = list(csv.reader(ITEMS.open(encoding='latin-1'), delimiter='\t'))
    header = {h: i for i, h in enumerate(rows[1])}
    kinds, names = {}, {}
    for row in rows[2:]:
        if len(row) <= header['Skill Group']:
            continue
        kind = classify(row[header['Equip Stat']], row[header['Skill Group']], row[header['Name']])
        icon = row[header['Pic File']].strip().lower()
        if kind is None or not icon or icon == 'null':
            continue
        kinds.setdefault(icon, kind)
        names.setdefault(icon, row[header['Name']])
    bound = set()
    for line in BINDINGS.read_text().splitlines():
        if '{icon:' in line:
            bound.add(line.split('{icon:')[1].split(',')[0].strip())
    entries, raw_lengths = {}, {}
    for icon, kind in sorted(kinds.items()):
        source = MODELS / f'item_{icon}.glb'
        if icon not in bound or not source.exists():
            print(f'skip {icon}: no ground model')
            continue
        override = dict(OVERRIDES.get(icon, {}))
        entry, ground_length = measure(positions(source), kind, override.pop('flip', False))
        entries[icon] = (kind, entry)
        raw_lengths[icon] = ground_length
    # Within a kind, a model longer on the ground than the kind's median is held a little longer (±15 %).
    by_kind = {}
    for icon, (kind, _) in entries.items():
        by_kind.setdefault(kind, []).append(raw_lengths[icon])
    medians = {kind: statistics.median(values) for kind, values in by_kind.items()}
    lines = [
        '# How the solo run\'s first-person arms hold each ground item model (game/render/HeldWeapons.h,',
        '# devdocs/solo_action/WEAPONS.md). Generated by',
        '# level_generation/solo_action_weapons_20261113/scripts/make_held_table.py: edit its OVERRIDES, not this file.',
        '# long: the shaft axis of the model (x or z); head: +1 the head at that axis\' maximum, -1 at its minimum;',
        '# edge: the side the edge (an axe\'s blade, a bow\'s riser) faces; grip: the palm as a fraction from the butt;',
        '# length: held length in Oblivion units (~1.43 cm); across: the shaft\'s place across the edge axis (0..1).',
        'schema: openyamm.heldWeapons.v1',
        'held:',
    ]
    for icon, (kind, entry) in sorted(entries.items()):
        held_length = KINDS[kind][0]
        variation = min(max(raw_lengths[icon] / medians[kind], 0.85), 1.15) if medians[kind] > 0 else 1.0
        entry['length'] = round(held_length * variation, 1)
        entry.update({k: v for k, v in OVERRIDES.get(icon, {}).items() if k != 'flip'})
        fields = ', '.join(f'{k}: {v}' for k, v in [('icon', icon), ('kind', kind)] + list(entry.items()))
        lines.append(f'  - {{{fields}}}   # {names[icon]}')
    text = '\n'.join(lines) + '\n'
    if check:
        print('unchanged' if OUT.exists() and OUT.read_text() == text else 'held.yml would change')
        return
    OUT.write_text(text)
    print(f'wrote {OUT} ({len(entries)} models)')


if __name__ == '__main__':
    main()
