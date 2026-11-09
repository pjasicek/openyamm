"""Snapshot feedback, stage exact approvals, and prepare native/reviewed comparisons."""
import csv
import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
PREVIOUS = HERE / 'review_pass_20260926'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    review = read(OUT / 'review.original.json')
    catalog = json.loads((HERE / 'catalog.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    assets = {a['id']: a for a in catalog['assets'].values()}
    previous = read(PREVIOUS / 'repairs.json')['results']
    flags = read(OUT / 'new_flags.json')
    (OUT / 'staged-accepted').mkdir(exist_ok=True)
    records = {}
    for target, decision in review['decisions'].items():
        a = assets[target]
        assert a['sourceHash'] == decision['source_hash'], target
        choices = [{'path': a['candidate'], 'sha256': a['candidateHash']}] + a.get('preparedAlternatives', [])
        if target in previous:
            choices.append(previous[target])
        chosen = next(v for v in choices if v['sha256'] == decision['candidate_hash'])
        source = HERE / unquote(chosen['path'])
        assert digest(source) == decision['candidate_hash'], target
        record = {'target': target, 'name': a['name'], 'decision': decision,
                  'reviewed_path': chosen['path'], 'reviewed_sha256': chosen['sha256'], 'source_hash': a['sourceHash']}
        if decision['decision'] == 'approve':
            dest = OUT / 'staged-accepted' / (target + '.png')
            shutil.copyfile(source, dest)
            record['staged_path'] = str(dest.relative_to(HERE))
        records[target] = record
    write(OUT / 'stage_manifest.json', {'schema': 'paperdoll-review-stage-v2', 'staging_only': True,
          'final_ledger_acceptance_authorized': False, 'ledger_modified': False, 'records': records})
    write(OUT / 'placements.json', {'schema': review['placement_schema'], 'placements': review['placements'],
          'inactive_legacy_keys': review['inactive_legacy_placement_keys']})
    with (OUT / 'placement_proposals.csv').open('w', newline='') as stream:
        fields = ['key', 'item_id', 'doll_type', 'slot', 'table', 'base_x', 'base_y', 'delta_x', 'delta_y',
                  'proposed_x', 'proposed_y', 'inherited_from', 'active']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for key, value in review['placements'].items():
            base, delta = value['base'], value['delta']
            writer.writerow({**{k: value.get(k, '') for k in fields[:5]}, 'key': key,
                'base_x': base[0], 'base_y': base[1], 'delta_x': delta[0], 'delta_y': delta[1],
                'proposed_x': base[0]+delta[0], 'proposed_y': base[1]+delta[1],
                'inherited_from': value.get('inherited_from', ''),
                'active': key not in review['inactive_legacy_placement_keys']})
    (OUT / 'contacts').mkdir(exist_ok=True)
    names = list(flags)
    for start in range(0, len(names), 12):
        sheet = Image.new('RGB', (1600, 1500), (55, 65, 70))
        draw = ImageDraw.Draw(sheet)
        for i, target in enumerate(names[start:start+12]):
            a = assets[target]
            x = i % 4 * 400
            y = i // 4 * 500
            draw.text((x+5, y+3), a['name'], fill='white')
            draw.text((x+5, y+18), flags[target]['note'][:55], fill='#efc47a')
            native = Image.open(HERE / unquote(a['native'])).convert('RGBA')
            native = native.resize((native.width*2, native.height*2), Image.Resampling.NEAREST)
            current = Image.open(HERE / unquote(records[target]['reviewed_path'])).convert('RGBA')
            scale = min(1.5, 188/max(native.width, current.width), 450/max(native.height, current.height))
            for j, im in enumerate([native, current]):
                im = im.resize((round(im.width*scale), round(im.height*scale)), Image.Resampling.NEAREST)
                sheet.paste(im, (x+j*200+(190-im.width)//2, y+43), im)
        sheet.save(OUT / 'contacts' / f'{start//12+1:02}.png')
    print({'staged': sum('staged_path' in r for r in records.values()), 'flags': len(flags),
           'placements': len(review['placements'])})


if __name__ == '__main__':
    main()
