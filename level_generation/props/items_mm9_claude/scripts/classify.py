"""Sorts the 245 MM9 item designs (one per source PCX, from the MM9 icon project's designs.json) into ground-model
routes and writes routes.tsv beside this folder's PLAN.md and classification.json, the per-design record the other
scripts read (key d<design id>: route, item ids, binding length, the icon project's master painting and icon, and a
description). A plan, not production: nothing is generated or paid.

    python3 -I scripts/classify.py

Routes (the 2026-10-18 item sessions' and Hesper's, see PLAN.md):
  meshy       Meshy Smart Topology, untextured (5 credits), Codex-painted views (paint + material mask) baked to PBR
  hybrid      a weapon: Blender components (blade, haft, grip, shaft) plus a Meshy Smart Topology head or hilt (5)
  blender     built from Blender components, Codex paint or procedural materials, no Meshy
  plate       a shield: the icon outline as a curved plate with thickness, rim and boss in Blender, face painted
  reuse?      a candidate for an existing MM6-MM8 ground model (decide beside the icon); falls back to blender
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ICON_PROJECT = HERE.parents[1] / 'ui/mm9_item_icons_20261104'

# Weapons whose head, hilt or whole form is sculpted rather than built from regular parts (the weapon sessions used
# Meshy for the same kinds: blunt heads, ornate axe heads, a few hilts and spear heads).
WEAPON_MESHY = {
    10066: 'bone', 10068: 'spiked wooden club', 10069: 'dragon head', 10070: 'flanged head', 10198: 'spiked log',
    10234: 'sculpted head', 10084: 'dragon hammer head', 10085: 'ornate head', 10193: 'ornate head',
    10199: 'Mjulnir head', 10229: 'skull head', 10197: 'great hammer head', 10194: 'lobed cluster weight',
    10195: 'weight', 10038: 'ornate axe head', 10039: 'ornate axe head', 10183: 'ornate axe head',
    10182: 'ornate axe head', 10179: 'ornate hilt', 10175: 'wide ornate guard', 10176: 'wide ornate guard',
    10180: 'sculpted hilt', 10189: 'Gungnir head', 10191: 'ornate head', 10192: 'ornate head', 10196: 'staff head',
    10080: 'staff head', 10187: 'crossbow stock',
}
# Misc designs that are sculptural or soft (Meshy) versus regular (Blender).
MISC_MESHY = {10241, 10368, 10369, 10370, 10372, 10373, 10380, 10390, 10395, 10398, 10399, 10379, 10591}
REUSE = {
    10400: 'Victory Certificate (106 items): an existing rolled-scroll model if the icon is a plain scroll',
    10445: "Accountant's Key (8 items): an existing MM key model if the icon matches",
    10358: 'Jar: an existing MM jar or vessel model if the icon matches',
}
WEAPON_FAMILIES = {'sword', 'sword2h', 'dagger', 'axe', 'axe2h', 'mace', 'hammer', 'hammer2h', 'flail', 'spear',
                   'halberd', 'staff', 'bow', 'crossbow', 'firearm', 'throwing'}
# Families whose icon painting (paint_a.png) is not the three-quarter view Meshy wants: a new Codex master first.
NEW_MASTER = {'helm', 'boots', 'gauntlets'}


def route(design):
    family, design_id = design['family'], design['design_id']
    if design_id in REUSE:
        return 'reuse?', 0, REUSE[design_id]
    if family in ('armor', 'helm', 'boots', 'gauntlets'):
        return 'meshy', 5, ''
    if family in WEAPON_FAMILIES:
        if design_id in WEAPON_MESHY:
            return 'hybrid', 5, WEAPON_MESHY[design_id]
        return 'blender', 0, 'regular components'
    if family == 'shield':
        return 'plate', 0, ''
    if family == 'misc':
        return ('meshy', 5, 'sculptural or soft') if design_id in MISC_MESHY else ('blender', 0, 'regular shape')
    return 'blender', 0, {'ring': 'band and setting', 'amulet': 'pendant and bail', 'belt': 'strap and buckle',
                          'book': 'book builder', 'scroll': 'scroll kit', 'bottle': 'lathe',
                          'key': 'key kit'}.get(family, '')


def length(design):
    """Binding length: the icon's longest side in logical pixels x 0.9, as the MM6-MM8 bindings (body armour 1.3x more,
    as MM6-MM8 armour is drawn)."""
    from PIL import Image
    with Image.open(ICON_PROJECT / 'items' / str(design['design_id']) / 'icon_a_x2.png') as icon:
        box = icon.getchannel('A').point(lambda alpha: 255 if alpha > 16 else 0).getbbox()
    side = max(box[2] - box[0], box[3] - box[1]) / 2 * 0.9
    return round(side * (1.3 if design['family'] == 'armor' else 1.0), 1)


def description(design):
    """What the design shows: the paperdoll pieces' facts (read from the new icons) where they exist, else the icon
    brief's design notes, else the MM9 text."""
    import yaml
    pieces = yaml.safe_load((ICON_PROJECT / 'paperdoll/pieces.yml').read_text())['pieces']
    piece = pieces.get(f"mm9_item_{design['design_id']}")
    if piece:
        return ' '.join(piece['facts'].split())
    brief = (ICON_PROJECT / 'briefs' / f"{design['design_id']}.md").read_text()
    notes = [line for line in brief.splitlines() if line.startswith('Design notes')]
    corrections = [line for line in brief.splitlines() if line.startswith('CORRECTION')]
    text = notes[0].split(':', 1)[1].strip() if notes else design.get('notes', '')
    return ' '.join([text] + corrections)


def main():
    designs = json.loads((ICON_PROJECT / 'designs.json').read_text())
    rows = [['design_id', 'family', 'name', 'items', 'item_ids', 'route', 'meshy_credits', 'master', 'notes']]
    for design in designs:
        kind, credits, note = route(design)
        master = 'new three-quarter' if design['family'] in NEW_MASTER else 'paint_a.png'
        rows.append([design['design_id'], design['family'], design['name'], len(design['item_ids']),
                     ' '.join(str(item) for item in design['item_ids']), kind, credits, master, note])
    classification = {}
    for design, row in zip(designs, rows[1:]):
        classification[f"d{design['design_id']}"] = {
            'design_id': design['design_id'], 'name': design['name'], 'family': design['family'],
            'route': row[5], 'items': design['item_ids'], 'length': length(design),
            'master': f"items/{design['design_id']}/paint_a.png", 'icon': f"items/{design['design_id']}/icon_a_x2.png",
            'description': description(design)}
    (HERE / 'classification.json').write_text(json.dumps(classification, indent=1) + '\n')
    with (HERE / 'routes.tsv').open('w', newline='') as stream:
        csv.writer(stream, delimiter='\t', lineterminator='\n').writerows(rows)
    totals = {}
    for row in rows[1:]:
        count, credits = totals.get(row[5], (0, 0))
        totals[row[5]] = (count + 1, credits + row[6])
    for kind, (count, credits) in sorted(totals.items()):
        print(f'{kind:8s} {count:4d} designs {credits:4d} credits')
    print('total', len(rows) - 1, 'designs', sum(c for _, c in totals.values()), 'credits')


if __name__ == '__main__':
    main()
