"""Read-only screening of pending candidates; does not accept, reject, or alter artwork."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
OUT = HERE / 'magenta_scan'


def measure(image):
    rgba = np.asarray(image.convert('RGBA')).astype(np.int16)
    r, g, b, a = (rgba[:, :, i] for i in range(4))
    visible = a >= 24
    # Padding includes image borders, even for crops with an opaque outermost row.
    distance = ndimage.distance_transform_edt(np.pad(visible, 1))[1:-1, 1:-1]
    pink = visible & (r >= 110) & (b >= 95) & (np.minimum(r, b) - g >= 45)
    key = pink & (r >= 180) & (b >= 170) & (g <= 95) & (abs(r - b) <= 65)
    edge = pink & (distance <= 3)
    suspect = edge | key
    labels, count = ndimage.label(suspect)
    sizes = np.bincount(labels.ravel())[1:] if count else np.array([0])
    ys, xs = np.where(suspect)
    return dict(edge_pixels=int(edge.sum()), key_pixels=int(key.sum()),
                opaque_key_pixels=int((key & (a >= 192)).sum()),
                visible_pixels=int(visible.sum()), purple_core_pixels=int((pink & (distance > 3)).sum()),
                largest_component=int(sizes.max()),
                alpha_weighted_pixels=round(float(a[suspect].sum() / 255), 2),
                bounds=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if xs.size else None)


def classify(metrics, native):
    significant = metrics['alpha_weighted_pixels'] >= 5 and (
        metrics['largest_component'] >= 4 or metrics['edge_pixels'] >= 14)
    if not significant:
        return 'no_spill_detected'
    # Existing purple materials can naturally reach the silhouette; keep them a separate uncertainty class.
    native_purple = native['edge_pixels'] + native['purple_core_pixels']
    if native_purple >= 5 and native_purple / max(native['visible_pixels'], 1) >= .005:
        return 'purple_material_check'
    return 'suspected_magenta_spill'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['equipment', 'jewelry'], default='equipment')
    arguments = parser.parse_args()
    output = OUT if arguments.group == 'equipment' else HERE / 'jewelry_prepared/magenta_scan'
    data = json.loads((HERE / 'catalog.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    names = {t['name'] for t in data['reviewTargets'] if t['active']}
    names |= {i['icon'] for i in data['items'] if i['stat'] in {'Weapon', 'Weapon1or2', 'Weapon2', 'WeaponW', 'Missile', 'Shield'}}
    if arguments.group == 'jewelry':
        names = {i['icon'] for i in data['items'] if i['stat'] in {'Gauntlets', 'Amulet', 'Ring'}}
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for name in sorted(names):
        asset = data['assets'].get(name)
        if not asset or not asset['candidate'] or asset['candidateStatus'] in {'accepted', 'hud_approved'}:
            continue
        with Image.open(HERE / unquote(asset['native'])) as native:
            native_metrics = measure(native)
        alternatives = {o['sha256']: o['path'] for o in asset['preparedAlternatives']}
        alternatives[asset['candidateHash']] = asset['candidate']
        for expected, url in alternatives.items():
            path = HERE / unquote(url)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
            with Image.open(path) as candidate:
                metrics = measure(candidate)
            records.append(dict(target=asset['id'], name=name, candidate_hash=expected,
                source_hash=asset['sourceHash'], path=url, selected=expected == asset['candidateHash'],
                status=classify(metrics, native_metrics), metrics=metrics, native_metrics=native_metrics))
    selected = [r for r in records if r['selected']]
    report = dict(schema='openyamm-magenta-screen-v1', method='visible-magenta-edge-v1',
                  note='Automated screening, not visual rejection. Purple materials are separated; no artwork modified.',
                  summary=dict(selected=len(selected), alternatives=len(records),
                               selected_status=dict(Counter(r['status'] for r in selected))), records=records)
    variable = 'PAPERDOLL_MAGENTA_SCAN' if arguments.group == 'equipment' else 'PAPERDOLL_JEWELRY_MAGENTA_SCAN'
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'report.js').write_text('window.' + variable + ' = ' + json.dumps(report) + ';\n')
    suspicious = sorted((r for r in selected if r['status'] != 'no_spill_detected'),
                        key=lambda r: -r['metrics']['alpha_weighted_pixels'])
    for offset in range(0, len(suspicious), 40):
        sheet = Image.new('RGB', (1200, 1100), (36, 44, 45))
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(suspicious[offset:offset + 40]):
            x, y = index % 8 * 150, index // 8 * 220
            with Image.open(HERE / unquote(row['path'])) as opened:
                picture = opened.convert('RGBA')
                picture.thumbnail((142, 175))
                sheet.paste(picture, (x + 4, y + 35), picture)
            draw.text((x + 3, y + 3), row['name'], fill='white')
            draw.text((x + 3, y + 17), ('purple?' if row['status'] == 'purple_material_check' else 'spill?') +
                      ' ' + str(row['metrics']['edge_pixels']), fill=(255, 170, 215))
        sheet.save(output / f'contact_{offset // 40 + 1:02}.jpg', quality=94)
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
