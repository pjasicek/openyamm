"""Compare an MM7 sprite family with the MM8 family whose installed 3D model it would reuse (batch M).

Reads scripts/project.json (MM7 and MM8 descriptor ids, one or more MM8 candidate families), the descriptor table,
the sprite frame tables, the original indexed bitmaps and the palettes; writes review/identity_check.json.

Per descriptor role (standing, walk, attack, hit, death, corpse, fidget) the MM7 and MM8 frame sequences are paired
frame by frame and view by view (0-4). Each pair reports alpha IoU (bottom-centre aligned, as the sprites are
anchored), the index-equal fraction where the bitmaps have the same size, and the bitmap size ratio. Because two
families can order or count their frames differently, every MM7 frame also gets its best alpha IoU against any MM8
frame of the same view ("best match"), and again with both crops normalised to the same height, which finds the
same render rasterised at another size (the MM7 Troll). Palettes are compared per tier by file hash and by mean colour difference.
A group missing from the frame tables (MM7 7m499*, the unused Ultra Dragon) is read from the native project manifest.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
CONFIG = json.loads((P / 'scripts/project.json').read_text())
MM7_DIRS = [ROOT / 'assets_dev/worlds/mm7/sprites', ROOT / 'assets_dev/engine/sprites',
            ROOT / 'reference/mmerge_data_forus/Data/mm7.sprites.lod']
MM8_DIRS = [ROOT / 'data/Data/sprites.lod', ROOT / 'assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites']
PALETTE_DIRS = {'mm7': [ROOT / 'assets_dev/worlds/mm7/textures', ROOT / 'assets_dev/worlds/mm8/textures'],
                'mm8': [ROOT / 'assets_dev/worlds/mm8/textures', ROOT / 'data/Data/bitmaps.lod']}
ROLES = ['standing', 'walk', 'attack', 'hit', 'death', 'corpse', 'fidget']
ROLE_COLUMNS = {'standing': 11, 'walk': 12, 'attack': 13, 'hit': 15, 'death': 16, 'corpse': 17, 'fidget': 18}
_listing = {}


def find(directories, name):
    for directory in directories:
        if directory not in _listing:
            _listing[directory] = {entry.lower(): entry for entry in os.listdir(directory)} if directory.exists() else {}
        entry = _listing[directory].get(name.lower())
        if entry:
            return directory / entry
    return None


def descriptors():
    table = {}
    for line in (ROOT / 'assets_dev/engine/data_tables/monster_descriptors.txt').read_text(errors='replace').splitlines()[2:]:
        cells = line.split('\t')
        if cells and cells[0].strip().isdigit():
            table[int(cells[0])] = cells
    return table


def frame_tables():
    sprites = {}
    for path in (ROOT / 'assets_dev/engine/rendering/sprite_frames/monsters').glob('*.yml'):
        current = None
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith('sprite_name:'):
                current = sprites.setdefault(line.split('"')[1].lower(), [])
            elif line.startswith('- texture_name:') and current is not None:
                current.append({'texture': line.split('"')[1].lower(), 'scale': 1.0, 'palette': None})
            elif line.startswith('scale:') and current:
                current[-1]['scale'] = float(line.split(':')[1])
            elif line.startswith('palette_id:') and current:
                current[-1]['palette'] = int(line.split(':')[1])
    return sprites


def load(directories, name):
    path = find(directories, name + '.bmp')
    if path is None:
        return None, None
    image = Image.open(path)
    return np.asarray(image), path


def bottom_aligned(a, b):
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])

    def pad(x):
        out = np.zeros((h, w), bool)
        x0 = (w - x.shape[1]) // 2
        out[h - x.shape[0]:, x0:x0 + x.shape[1]] = x
        return out
    return pad(a), pad(b)


def compare(a, b):
    mask_a, mask_b = bottom_aligned(a != 0, b != 0)
    result = {'alpha_iou': round(float((mask_a & mask_b).sum() / max(1, (mask_a | mask_b).sum())), 4),
              'size_ratio': round(float(np.sqrt((a != 0).sum() / max(1, (b != 0).sum()))), 4)}
    if a.shape == b.shape:
        both = (a != 0) | (b != 0)
        result['index_equal_fraction'] = round(float((a == b)[both].mean()), 4)
    return result


def palette(world, pid):
    for directory in PALETTE_DIRS[world]:
        path = find([directory], f'pal{pid}.act')
        if path:
            raw = path.read_bytes()
            return hashlib.sha256(raw).hexdigest(), np.frombuffer(raw[:768], np.uint8).reshape(256, 3).astype(float)
    return None, None


def role_frames(sprites, group, descriptor=None, role=None):
    if not group or group == 'null':
        return []
    if group.lower() in sprites:
        return sprites[group.lower()]
    manifest = P.parent / CONFIG['native_project'] / 'manifest.json'
    animation = json.loads(manifest.read_text())['descriptor_animations'][str(descriptor)].get(role)
    if animation is None:
        return []
    return [{'texture': frame['frame'].lower(), 'scale': float(frame.get('scale', 1.0)),
             'palette': CONFIG.get('native_palette')} for frame in animation['directions']['0']]


def views(directories, texture):
    """Image1 frames name one bitmap (m206wa0); others have five views (m206aa + 0..4)."""
    if find(directories, texture + '.bmp') is not None:
        return [texture]
    stem = texture[:-1] if texture[-1:].isdigit() else texture
    return [stem + str(view) for view in range(5)]


def view_of(name):
    return int(name[-1]) if name[-1:].isdigit() else 0


def cropped(mask):
    rows, cols = np.nonzero(mask)
    return mask[rows.min():rows.max() + 1, cols.min():cols.max() + 1] if rows.size else mask


def height_normalised_iou(mask7, mask8):
    """IoU after cropping both masks to their bounds and resizing the MM7 crop to the MM8 crop height (MM7 bitmaps
    can be the same render at another raster size, drawn with a larger frame scale). Returns (IoU, factor)."""
    a, b = cropped(mask7), cropped(mask8)
    factor = b.shape[0] / max(1, a.shape[0])
    size = (max(1, round(a.shape[1] * factor)), b.shape[0])
    a = np.asarray(Image.fromarray(a.astype(np.uint8) * 255).resize(size, Image.BILINEAR)) >= 128
    a, b = bottom_aligned(a, b)
    return float((a & b).sum() / max(1, (a | b).sum())), factor


def best_matches(mm7_names, mm8_names, normalise=False):
    masks8 = {}
    for name in sorted(mm8_names):
        image, _ = load(MM8_DIRS, name)
        if image is not None and (image != 0).any():
            masks8[name] = image != 0
    frames = []
    for name in sorted(mm7_names):
        image, _ = load(MM7_DIRS, name)
        if image is None or not (image != 0).any():
            continue
        mask = image != 0
        scored = []
        for other, mask8 in masks8.items():
            if view_of(other) != view_of(name):
                continue
            if normalise:
                scored.append((*height_normalised_iou(mask, mask8), other))
            else:
                a, b = bottom_aligned(mask, mask8)
                scored.append((float((a & b).sum() / max(1, (a | b).sum())), 1.0, other))
        if scored:
            iou, factor, other = max(scored)
            frames.append({'mm7': name, 'mm8': other, 'alpha_iou': round(iou, 4), 'factor': round(factor, 4)})
    values = np.array([f['alpha_iou'] for f in frames]) if frames else np.zeros(1)
    key = 'height_normalised_best_match' if normalise else 'best_match'
    summary = {f'{key}_frames': len(frames), f'{key}_iou_min': round(float(values.min()), 4),
               f'{key}_iou_median': round(float(np.median(values)), 4),
               f'{key}_iou_p10': round(float(np.percentile(values, 10)), 4)}
    if normalise and frames:
        factors = np.array([f['factor'] for f in frames])
        summary[f'{key}_factor_median'] = round(float(np.median(factors)), 4)
        summary[f'{key}_factor_p10_p90'] = [round(float(np.percentile(factors, q)), 4) for q in (10, 90)]
    return {'frames': frames, 'summary': summary}


def main():
    table, sprites = descriptors(), frame_tables()
    report = {'mm7_descriptors': CONFIG['mm7'], 'candidates': {}}
    for candidate, mm8_ids in CONFIG['mm8'].items():
        tiers, pairs, mm7_names, mm8_names = [], [], set(), set()
        for mm7_id, mm8_id in zip(CONFIG['mm7'], mm8_ids):
            row7, row8 = table[mm7_id], table[mm8_id]
            tier = {'mm7': [mm7_id, row7[1], int(row7[2])], 'mm8': [mm8_id, row8[1], int(row8[2])], 'roles': {}}
            for role in ROLES:
                f7 = role_frames(sprites, row7[ROLE_COLUMNS[role]], mm7_id, role)
                f8 = role_frames(sprites, row8[ROLE_COLUMNS[role]], mm8_id, role)
                tier['roles'][role] = {'mm7_frames': len(f7), 'mm8_frames': len(f8),
                                       'mm7_scale': sorted({f['scale'] for f in f7}),
                                       'mm8_scale': sorted({f['scale'] for f in f8}),
                                       'mm7_palette': sorted({f['palette'] for f in f7 if f['palette'] is not None}),
                                       'mm8_palette': sorted({f['palette'] for f in f8 if f['palette'] is not None})}
                if len(tiers) == 0:
                    for frame in f7:
                        mm7_names.update(views(MM7_DIRS, frame['texture']))
                    for frame in f8:
                        mm8_names.update(views(MM8_DIRS, frame['texture']))
                    for index, (a, b) in enumerate(zip(f7, f8)):
                        for name7, name8 in zip(views(MM7_DIRS, a['texture']), views(MM8_DIRS, b['texture'])):
                            view = view_of(name7)
                            image7, path7 = load(MM7_DIRS, name7)
                            image8, path8 = load(MM8_DIRS, name8)
                            if image7 is None or image8 is None:
                                continue
                            entry = {'role': role, 'index': index, 'view': view, 'mm7': path7.name, 'mm8': path8.name,
                                     'same_file_bytes': path7.read_bytes() == path8.read_bytes()}
                            entry.update(compare(image7, image8))
                            pairs.append(entry)
            stand = tier['roles']['standing']
            p7 = (stand['mm7_palette'] or [None])[0]
            p8 = (stand['mm8_palette'] or [None])[0]
            h7, c7 = palette('mm7', p7)
            h8, c8 = palette('mm8', p8)
            tier['palettes'] = {'mm7': p7, 'mm8': p8, 'same_file': h7 is not None and h7 == h8,
                                'mean_abs_rgb_difference': None if c7 is None or c8 is None
                                else round(float(np.abs(c7 - c8).mean()), 2)}
            tiers.append(tier)
        # Best matches search every MM8 bitmap of the family, also frames no MM8 descriptor uses (peasant attacks).
        prefix = candidate.split('_')[0].lower()
        for directory in MM8_DIRS:
            find([directory], 'x')
            mm8_names.update(entry[:-4].lower() for entry in _listing[directory]
                             if entry.startswith(prefix) and entry.endswith('.bmp'))
        best = best_matches(mm7_names, mm8_names)
        normalised = best_matches(mm7_names, mm8_names, True)
        if pairs:
            iou = np.array([p['alpha_iou'] for p in pairs])
            equal = [p['index_equal_fraction'] for p in pairs if 'index_equal_fraction' in p]
            ratio = np.array([p['size_ratio'] for p in pairs])
            summary = {'pairs': len(pairs), 'same_size_pairs': len(equal),
                       'identical_files': sum(p['same_file_bytes'] for p in pairs),
                       'alpha_iou_min': round(float(iou.min()), 4), 'alpha_iou_median': round(float(np.median(iou)), 4),
                       'alpha_iou_mean': round(float(iou.mean()), 4),
                       'index_equal_mean': round(float(np.mean(equal)), 4) if equal else None,
                       'size_ratio_median': round(float(np.median(ratio)), 4)}
            summary.update(best['summary'])
            summary.update(normalised['summary'])
        else:
            summary = {'pairs': 0, **best['summary'], **normalised['summary']}
        report['candidates'][candidate] = {'mm8_descriptors': mm8_ids, 'summary': summary, 'tiers': tiers,
                                           'pairs': pairs, 'best_match': best['frames'],
                                           'height_normalised_best_match': normalised['frames']}
        print(candidate, json.dumps(summary))
        for tier in tiers:
            print('  ', tier['mm7'], tier['mm8'], 'standing scale', tier['roles']['standing']['mm7_scale'],
                  tier['roles']['standing']['mm8_scale'], 'palettes', json.dumps(tier['palettes']))
    (P / 'review/identity_check.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    sys.exit(main())
