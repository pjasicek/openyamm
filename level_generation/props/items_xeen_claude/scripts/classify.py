"""Sorts the 64 Xeen item icons (xeen_item_*, the Xeen icon project's manifest.yml `targets`) into ground-model routes
and writes routes.tsv and classification.json, the per-design record the other scripts read (key x<file suffix>:
route, builder, item ids, binding length, the icon project's HD painting and icon, and a description, the manifest's
`draw`). One design per icon; the seven base icons (katana, scimitar ...) each serve every tier of their weapon.

    python3 -I scripts/classify.py

Routes (decided by lane A2, 2026-11-20):
  blender     built from Blender components (build_xeen.py; the builder column names the kind), Codex paint + mask
  reuse       bound to an installed engine model (`reuse` below), nothing built
  meshy       sculptural: needs Meshy, which is lane S's; not built and not bound here
  dropped     not a quest item: the user's scope change of 2026-11-20 keeps ground models for quest items only (the
              new weapon bases and the artifacts are dropped or reskinned onto MM6-MM8 items with engine models)
"""
import csv
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
ICON_PROJECT = HERE.parents[1] / 'ui/xeen_item_icons'
WEAPON_FAMILIES = {'sword', 'sword2h', 'dagger', 'axe', 'axe2h', 'mace', 'hammer', 'flail', 'spear', 'halberd',
                   'staff', 'bow'}
# Weapon family per design where the manifest's (the icon's size class) is not the build family.
FAMILY = {'xkatana': 'sword2h', 'xnaginata': 'spear', 'x12366': 'mace', 'x12310': 'staff', 'x12345': 'staff',
          'x12308': 'staff'}
BUILDER = {
    **{d: 'auto_weapon' for d in ('xkatana', 'xscimitar', 'xflamberge', 'xnaginata', 'xglaive', 'xgreat_axe',
                                  'xflail', 'x12500', 'x12501', 'x12502', 'x12503', 'x12504', 'x12505', 'x12506',
                                  'x12528', 'x12530', 'x12310', 'x12345', 'x12308')},
    **{d: 'rock' for d in ('x12301', 'x12304', 'x12314', 'x12357', 'x12358', 'x12359', 'x12360', 'x12343',
                           'x12362', 'x12312')},
    **{d: 'outline_slab' for d in ('x12302', 'x12305', 'x12309')},
    'x12331': 'sphere', 'x12334': 'disc', 'x12400': 'book_generic', 'x12524': 'book_generic',
    'x12511': 'amulet_generic', 'x12523': 'amulet_generic',
    'x12353': 'vessel_upright', 'x12373': 'vessel_upright',
    **{d: 'custom' for d in ('x12313', 'x12315', 'x12352', 'x12363', 'x12364', 'x12365', 'x12527', 'x12346',
                             'x12347', 'x12192', 'x12366', 'x12510', 'x12522', 'x12525')},
}
# Standing items (bell, jar, chalice; the Meshy statuettes and dolls): the binding's horizontal length is the icon's
# width (length()).
UPRIGHT = {'x12353', 'x12373', 'x12525'}
# Engine models that already show the icon's object (the model stays in the engine; the binding copies its length).
REUSE = {'x12311': 'skull', 'x12350': 'statuet5'}
MESHY = {'x12349', 'x12351', 'x12367', 'x12368', 'x12369', 'x12370', 'x12371'}
DROPPED = {'xkatana', 'xscimitar', 'xflamberge', 'xnaginata', 'xglaive', 'xgreat_axe', 'xflail', 'x12500', 'x12501',
           'x12502', 'x12503', 'x12504', 'x12505', 'x12506', 'x12510', 'x12511', 'x12522', 'x12524', 'x12525',
           'x12526', 'x12527', 'x12528', 'x12530'}


def length(icon, upright=False):
    """Binding length: the icon's longest opaque side in logical pixels x 0.9 (MM9 classify.py). An upright vessel
    (bell, jar, chalice) stands as the icon shows it, so its horizontal side is the icon's width at that scale."""
    from PIL import Image
    with Image.open(icon) as image:
        box = image.getchannel('A').point(lambda alpha: 255 if alpha > 16 else 0).getbbox()
    side = box[2] - box[0] if upright else max(box[2] - box[0], box[3] - box[1])
    return round(side / 2 * 0.9, 1)


def build_family(design, target):
    family = FAMILY.get(design, target['family'])
    if family in WEAPON_FAMILIES or family in ('ring', 'amulet', 'book'):
        return family
    return 'bottle' if BUILDER.get(design) == 'vessel_upright' else 'misc'


def main():
    manifest = yaml.safe_load((ICON_PROJECT / 'manifest.yml').read_text())
    rows = [['design', 'icon', 'family', 'name', 'items', 'route', 'builder']]
    classification = {}
    for target in manifest['targets']:
        design = 'x' + target['file'].removeprefix('xeen_item_')
        items = target.get('ids') or [target['id']]
        route = 'dropped' if design in DROPPED else 'reuse' if design in REUSE else \
            'meshy' if design in MESHY else 'blender'
        builder = REUSE.get(design) if route == 'reuse' else BUILDER.get(design, '') if route == 'blender' else ''
        if route == 'blender' and not builder:
            raise SystemExit(f'{design}: no builder')
        folder = f"items/{target['file']}"
        classification[design] = {
            'icon': target['file'], 'name': target['name'], 'family': build_family(design, target),
            'route': route, 'builder': builder, 'items': items,
            'length': length(ICON_PROJECT / folder / 'icon_a_x2.png', design in UPRIGHT | MESHY),
            'master': f'{folder}/paint_a.png', 'icon_file': f'{folder}/icon_a_x2.png',
            'description': f"{target['name']}: {' '.join(target['draw'].split())}"}
        rows.append([design, target['file'], classification[design]['family'], target['name'],
                     ' '.join(str(item) for item in items), route, builder])
    (HERE / 'classification.json').write_text(json.dumps(classification, indent=1) + '\n')
    with (HERE / 'routes.tsv').open('w', newline='') as stream:
        csv.writer(stream, delimiter='\t', lineterminator='\n').writerows(rows)
    totals = {}
    for row in rows[1:]:
        totals[row[5]] = totals.get(row[5], 0) + 1
    print(totals, 'total', len(rows) - 1)


if __name__ == '__main__':
    main()
