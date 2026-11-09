"""Refreshes the review viewer (review/viewer/) from the finished pieces: copies each piece's review sheet and icon
into img/, the outfit and weapon renders from review/outfits/, and rewrites the inlined `const DATA` of index.html
(pieces from pieces.yml and work/<piece>/review/picks.json, all grips from runtime/equip_anchors.tsv and
review/weapons/, the jewellery panels from review/jewelry/).

    python3 scripts/viewer_data.py
"""
import csv
import json
import re
import shutil

import mm9_paperdoll as M

P = M.P
VIEWER = P.PROJECT / 'review/viewer'
IMG = VIEWER / 'img'
# Pieces whose outline is not the mapping table's: shown on the piece card.
NOTES = {
    10120: 'Outline from MM8 Full Helm instead of the table\'s MM7 Elven Helm (an open nasal helm with a coif).',
    10221: 'Outline from MM7 Conscript\'s Helm instead of the table\'s MM7 Elven Helm (its coif).',
    10203: 'Outline from MM8 Full Helm instead of the table\'s MM8 Drogg\'s Helm (crest and side horns). Eye sockets, '
           'nose and mouth made transparent so the face shows through (user, 2026-11-05).',
    10231: 'Outline from MM8 Full Helm instead of the table\'s MM8 Drogg\'s Helm (crest and side horns).',
    10236: 'Outline from MM7 Phynaxian Helm (as Jarl\'s Helm) instead of the table\'s MM7 Mogred Helm (side horns).',
    10204: 'Same design and outline as Plain Helm: its generations are reused.',
    10366: 'Each boot outline cut to its foot (no shaft).',
    10110: 'Coverage thigh_length instead of the table\'s full_harness.',
    10112: 'Coverage thigh_length instead of the table\'s full_harness.',
    10202: 'Coverage thigh_length instead of the table\'s full_harness.',
}

GRIP_NOTES = {
    10074: 'Icon repainted with a slim handle (user: grip too wide); grip recomputed.',
    10075: 'Icon repainted with a slim handle (same fault as War Star); grip recomputed.',
    10194: 'Icon repainted with a slim handle (same fault as War Star); grip recomputed.',
    10188: 'Icon refitted smaller (120 px): taller than MM crossbows, its muzzle showed over every head.',
}


def sheet_copy(source, target):
    image = P.Image.open(source).convert('RGB')
    if image.width > 900 and 'panel_' not in target.name:
        image = image.resize((900, round(image.height * 900 / image.width)), P.Image.Resampling.LANCZOS)
    image.save(target, quality=84)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    html = (VIEWER / 'index.html').read_text()
    match = re.search(r'const DATA = (\{.*?\});\n', html, re.S)
    data = json.loads(match.group(1))
    pieces = []
    for name, piece in P.pieces().items():
        review = P.WORK / name / 'review'
        picks = json.loads((review / 'picks.json').read_text())
        fill = {key: round(shares[picks['picks'][key]]) for key, shares in picks['fill_percent'].items()}
        sheet_copy(review / 'sheet.jpg', IMG / f"sheet_{piece['id']}.jpg")
        shutil.copy2(P.ICONS_X2 / f'{name}.png', IMG / f"icon_{piece['id']}.png")
        reference = P.D.ENGINE_ITEMS[piece['reference']]
        pieces.append({'id': piece['id'], 'name': piece['name'], 'slot': piece['slot'], 'reference': piece['reference'],
                       'reference_name': reference.name, 'coverage': piece.get('coverage'),
                       'coverage_limits': piece.get('coverage_limits'), 'smooth_crown': piece.get('smooth_crown'),
                       'fill': fill, 'note': NOTES.get(piece['id'])})
    data['pieces'] = pieces
    outfits = P.PROJECT / 'review/outfits'
    data['index'] = json.loads((outfits / 'index.json').read_text())
    for entry in data['index']['outfits'] + data['index']['weapons']:
        shutil.copy2(outfits / entry['file'], IMG / entry['file'])
    grips = []
    for row in csv.DictReader((P.PROJECT / 'runtime/equip_anchors.tsv').open(), delimiter='\t'):
        item_id = int(row['Item #'])
        sheet_copy(P.PROJECT / f'review/weapons/{item_id}.jpg', IMG / f'grip_{item_id}.jpg')
        grips.append({'id': item_id, 'name': row['Name'], 'stat': row['Equip Stat'], 'skill': row['Skill Group'],
                      'old': [int(row['Old X']), int(row['Old Y'])], 'new': [int(row['New X']), int(row['New Y'])],
                      'note': GRIP_NOTES.get(item_id)})
    data['grips'] = grips
    data['weapons'] = [dict(weapon, new=next(g['new'] for g in grips if g['id'] == weapon['id']))
                       for weapon in data['weapons']]
    jewelry = json.loads((P.PROJECT / 'review/jewelry/index.json').read_text())
    for entry in jewelry:
        sheet_copy(P.PROJECT / 'review/jewelry' / entry['file'], IMG / entry['file'])
    data['jewelry'] = jewelry
    html = html[:match.start(1)] + json.dumps(data) + html[match.end(1):]
    (VIEWER / 'index.html').write_text(html)
    print(len(pieces), 'pieces,', len(data['index']['outfits']), 'outfit renders,', len(data['index']['weapons']),
          'weapon renders')


if __name__ == '__main__':
    main()
