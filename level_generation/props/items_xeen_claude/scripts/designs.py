"""Writes designs.json, the per-design record the pipeline scripts read (the MAW and MM9 projects' format), from
classification.json (classify.py; its blender designs only) and design_overrides.yml (hand corrections per design,
applied last). Copied from level_generation/props/items_mm9_claude/scripts/designs.py.

Family defaults: the material classes Codex may paint in the mask (material_masks.py) and the interior material of
surfaces no view sees. Every design is built in Blender (`geometry: procedural`, scripts/build_xeen.py writes
work/procedural/<design>.glb), except route meshy (lane S's statuettes and dolls: `geometry: meshy_st`, the Meshy Smart
Topology shape stood up by scripts/stand_meshy.py into the same file).
Usage: python3 -I scripts/designs.py"""
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
ICON_PROJECT = HERE.parents[1] / 'ui/xeen_item_icons'
# family: (mask classes, unseen material, triangle budget, rest)
FAMILIES = {
    'armor': (['metal', 'leather', 'cloth', 'gem'], 'leather', 3000, 'pca_front'),
    'helm': (['metal', 'leather', 'cloth', 'gem', 'horn'], 'leather', 2400, None),
    'boots': (['metal', 'leather', 'cloth', 'horn'], 'leather', 3000, None),
    'gauntlets': (['metal', 'leather', 'cloth', 'gem'], 'leather', 2200, 'pca_front'),
    'shield': (['metal', 'leather', 'horn', 'gem'], 'horn', 1200, None),
    'ring': (['metal', 'gem'], 'metal', 800, None),
    'amulet': (['metal', 'gem', 'cloth'], 'metal', 1200, None),
    'belt': (['metal', 'leather', 'cloth', 'gem'], 'leather', 1400, None),
    'book': (['leather', 'cloth', 'metal', 'horn'], 'horn', 900, None),
    'scroll': (['cloth', 'horn', 'metal'], 'horn', 900, None),
    'bottle': (['gem', 'metal', 'horn', 'cloth'], 'gem', 1200, None),
    'key': (['metal'], 'metal', 600, None),
    'misc': (['metal', 'leather', 'cloth', 'horn', 'gem'], 'horn', 2400, None),
}
WEAPON = (['metal', 'leather', 'cloth', 'horn', 'gem'], 'metal', 2400, None)
# Route meshy (sculptural, lane S): dolls by default; the statuettes are one material (design_overrides.yml).
MESHY = (['cloth', 'leather', 'metal', 'horn'], 'cloth', 3000, None)
MASK_NOTES = {'horn': 'wood, bone, horn, stone, parchment, paper and other matte non-metal solids'}


def main():
    classification = json.loads((HERE / 'classification.json').read_text())
    overrides_path = HERE / 'design_overrides.yml'
    overrides = (yaml.safe_load(overrides_path.read_text()) or {}) if overrides_path.exists() else {}
    designs = {}
    for key, entry in classification.items():
        if entry['route'] not in ('blender', 'meshy'):
            continue   # reuse (an engine model) and dropped designs are not built here
        meshy = entry['route'] == 'meshy'
        classes, unseen, budget, _ = MESHY if meshy else FAMILIES.get(entry['family'], WEAPON)
        record = {
            'title': entry['name'], 'family': entry['family'], 'route': entry['route'], 'items': entry['items'],
            'icon_path': str(ICON_PROJECT / entry['icon_file']), 'painting': str(ICON_PROJECT / entry['master']),
            'icon': entry['icon'], 'builder': 'stand_meshy' if meshy else entry['builder'],
            'identity': entry['description'], 'materials': entry['description'],
            'material_classes': classes, 'unseen_material': unseen, 'normal': 1.0,
            'length': entry['length'],
        }
        if meshy:
            # Smart Topology at about 3,000 triangles; prep reduces only what is well over the budget.
            record.update({'geometry': 'meshy_st', 'tris': budget, 'smooth_angle': 40})
        else:
            # Built to its own budget in build_xeen.py: prep must not reduce it.
            record['geometry'] = 'procedural'
            record['smooth_angle'] = 35
        record.update(overrides.get(key, {}))
        designs[key] = record
    (HERE / 'designs.json').write_text(json.dumps(designs, indent=1) + '\n')
    print(len(designs), 'designs')


if __name__ == '__main__':
    main()
