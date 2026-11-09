"""Writes designs.json, the per-design record the pipeline scripts read (the MAW project's format), from
classification.json (classify.py) and design_overrides.yml (hand corrections per design, applied last).

Family defaults: the material classes Codex may paint in the mask (material_masks.py), the interior material of
surfaces no view sees, the triangle budget, the resting pose of a Meshy model (codex_texture.py `rest`) and whether the
geometry is built in Blender (`geometry: procedural`, scripts/build_mm9.py writes work/procedural/<design>.glb).
Usage: python3 -I scripts/designs.py"""
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
ICON_PROJECT = HERE.parents[1] / 'ui/mm9_item_icons_20261104'
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
MASK_NOTES = {'horn': 'wood, bone, horn, stone, parchment, paper and other matte non-metal solids'}


def main():
    classification = json.loads((HERE / 'classification.json').read_text())
    overrides_path = HERE / 'design_overrides.yml'
    overrides = (yaml.safe_load(overrides_path.read_text()) or {}) if overrides_path.exists() else {}
    designs = {}
    for key, entry in classification.items():
        classes, unseen, tris, rest = FAMILIES.get(entry['family'], WEAPON)
        record = {
            'title': entry['name'], 'family': entry['family'], 'route': entry['route'], 'items': entry['items'],
            'icon_path': str(ICON_PROJECT / entry['icon']), 'painting': str(ICON_PROJECT / entry['master']),
            'identity': entry['description'], 'materials': entry['description'],
            'material_classes': classes, 'unseen_material': unseen, 'tris': tris, 'normal': 1.0,
            'length': entry['length'],
        }
        route = overrides.get(key, {}).get('route', entry['route'])
        if route in ('blender', 'plate', 'hybrid', 'reuse?'):
            # Built to its own budget in build_mm9.py: prep must not reduce it.
            record['geometry'] = 'procedural'
            record['smooth_angle'] = 35
            del record['tris']
        else:
            record['geometry'] = None
            if rest:
                record['rest'] = rest
        record.update(overrides.get(key, {}))
        part = record.get('meshy_part')
        if part and 'master_note' not in record:
            record['master_note'] = {
                'head': 'Show ONLY the weapon\'s head (the striking head, blade or ornament, with the socket where the '
                        'shaft enters), WITHOUT the shaft or handle: the shaft is modelled separately. Keep the head '
                        'upright as in the painting.',
                'hilt': 'Show ONLY the sword\'s hilt (crossguard, grip and pommel, with the base of the blade cut off '
                        'just above the guard), WITHOUT the blade: the blade is modelled separately. Keep it upright '
                        'as in the painting, guard at the top.',
                'weight': 'Show ONLY the flail\'s striking weight (the spiked head), WITHOUT the chain and handle: '
                          'they are modelled separately.'}[part]
        if record.get('geometry') is None:
            record.pop('geometry', None)
            record.setdefault('tris', tris)
        if record.get('rest') is None:
            record.pop('rest', None)
        designs[key] = record
    (HERE / 'designs.json').write_text(json.dumps(designs, indent=1) + '\n')
    print(len(designs), 'designs')


if __name__ == '__main__':
    main()
