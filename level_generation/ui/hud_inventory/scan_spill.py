"""Read-only magenta/green/cyan screening of accepted icons and retained masters.

This is a classifier, not a cleanup or acceptance tool. All coordinates are xyxy.
"""
import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from freeze_targets import rendered
from native_sources import native_source

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAPER = HERE / 'paperdoll_review'
COLORS = ('magenta', 'green', 'cyan')
RANK = {'likely_spill': 0, 'color_material_review': 1, 'trace': 2, 'no_spill_detected': 3}


def read(path):
    return json.loads(Path(path).read_text())


@lru_cache(maxsize=30000)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def scores(rgb):
    r, g, b = (rgb[:, :, i].astype(np.int16) for i in range(3))
    return dict(magenta=np.minimum(r, b) - g, green=g - np.maximum(r, b), cyan=np.minimum(g, b) - r)


def color_masks(rgb):
    s = scores(rgb)
    r, g, b = (rgb[:, :, i] for i in range(3))
    return dict(magenta=(s['magenta'] >= 24) & (r >= 65) & (b >= 65),
                green=(s['green'] >= 24) & (g >= 65),
                cyan=(s['cyan'] >= 30) & (g >= 70) & (b >= 70))


def distance_inside(mask):
    # Include the canvas perimeter even when every pixel is opaque.
    return ndimage.distance_transform_edt(np.pad(mask, 1))[1:-1, 1:-1]


def bounds(mask):
    ys, xs = np.nonzero(mask)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if xs.size else None


def material_guard(metrics):
    # On a fully opaque illustration a modest green/cyan perimeter can be the
    # scene background, rather than a cutout fringe. Keep it in the review queue.
    full_canvas = metrics['visible_pixels'] == metrics['size'][0] * metrics['size'][1]
    for color in ('green', 'cyan'):
        row = metrics['colors'][color]
        if full_canvas and row['status'] == 'likely_spill' and row['hot_pixels'] == 0:
            row['status'] = 'color_material_review'
            row['context_note'] = 'Opaque illustration; moderate green/cyan may be intentional background.'
    metrics['status'] = min((r['status'] for r in metrics['colors'].values()), key=RANK.get)
    return metrics


def native_reference(contract):
    path = native_source(contract['source_path'])
    if sha(path) != contract['source_sha256']:
        raise ValueError(f'Native source changed: {path}')
    with Image.open(path) as im:
        rgb = np.asarray(im.convert('RGBA')).copy()
        # Preserve pixels visible in any recorded consumer profile. Do not erase
        # intentional art just because another historical consumer keys it out.
        alpha = np.maximum.reduce([np.asarray(rendered(im, p))[:, :, 3]
                                   for p in contract['compositing']['profiles']])
        hidden = (alpha == 0) & (rgb[:, :, 3] > 0)
        key_colors = []
        if hidden.any():
            values, counts = np.unique(rgb[:, :, :3][hidden], axis=0, return_counts=True)
            for i in np.argsort(counts)[-4:][::-1]:
                key_colors.append(dict(rgb=values[i].tolist(), pixels=int(counts[i])))
        rgb[:, :, 3] = alpha
        rgb[alpha == 0, :3] = 0
    return Image.fromarray(rgb), dict(path=relative(path), sha256=contract['source_sha256'],
                                    profiles=contract['compositing']['profiles'], key_colors=key_colors)


def measure(image, native=None, edge_width=3):
    pixels = np.asarray(image.convert('RGBA'))
    alpha = pixels[:, :, 3]
    visible = alpha >= 8
    distance = distance_inside(visible)
    edge = visible & (distance <= edge_width)
    core = visible & (distance > edge_width + 1) & (alpha >= 192)
    masks = color_masks(pixels[:, :, :3])
    chroma = scores(pixels[:, :, :3])
    native_masks = None
    if native is not None:
        original = np.asarray(native.convert('RGBA'))
        original_visible = original[:, :, 3] >= 8
        native_masks = {color: mask & original_visible for color, mask in color_masks(original).items()}
    indices = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True) if core.any() else None
    report, highlighted = {}, {}
    for color in COLORS:
        colored = masks[color] & visible
        hot = colored & (chroma[color] >= 140)
        suspect = (colored & edge) | hot
        weights = alpha.astype(np.float32) / 255
        support = np.zeros(visible.shape, dtype=bool)
        native_fraction = 0.0
        if native_masks is not None:
            material = native_masks[color]
            native_fraction = float(material.sum() / max(1, original_visible.sum()))
            # Local correspondence is advisory, since restored edges can move.
            material = ndimage.binary_dilation(material, iterations=2)
            support = np.asarray(Image.fromarray(material).resize(image.size, Image.Resampling.NEAREST))
        local_excess = suspect & ~support
        if indices is not None:
            inner = chroma[color][indices[0], indices[1]]
            local_excess &= chroma[color] >= inner + 20
        else:
            local_excess &= hot
        labels, count = ndimage.label(suspect, structure=np.ones((3, 3)))
        sizes = np.bincount(labels.ravel())[1:] if count else np.array([0])
        area = max(1, int(visible.sum()))
        weighted = float(weights[suspect].sum())
        evidence = local_excess | (hot & ~support)
        evidence_weight = float(weights[evidence].sum())
        significant = weighted >= 3 and (sizes.max() >= 3 or suspect.sum() >= 8)
        # A whole green/purple object is not, by color alone, proof of spill.
        broad_material = colored.sum() / area > .18 and (colored & ~edge).sum() > 2 * (colored & edge).sum()
        if not suspect.any():
            status = 'no_spill_detected'
        elif not significant:
            status = 'trace'
        elif evidence_weight >= 3 and not broad_material and native_fraction < .05 and native is not None:
            status = 'likely_spill'
        else:
            status = 'color_material_review'
        report[color] = dict(status=status, edge_pixels=int((colored & edge).sum()),
            hot_pixels=int(hot.sum()), suspect_pixels=int(suspect.sum()),
            alpha_weighted_pixels=round(weighted, 2), largest_component=int(sizes.max()),
            unsupported_edge_excess_pixels=int(local_excess.sum()), evidence_weight=round(evidence_weight, 2),
            native_supported_pixels=int((suspect & support).sum()),
            native_material_fraction=round(native_fraction, 5), broad_material=bool(broad_material),
            bounds=bounds(suspect))
        highlighted[color] = suspect
    overall = min((r['status'] for r in report.values()), key=RANK.get)
    return material_guard(dict(status=overall, size=list(image.size), visible_pixels=int(visible.sum()),
                               edge_width=edge_width, colors=report)), highlighted


def suppress_sheet_matte(image):
    """Diagnostic mask only: omit a proven near-key border-connected sheet backing.

    Never use on accepted x2 images: residual keys there are actual findings.
    Soft mixed-color pixels beside the omitted backing remain measurable.
    """
    p = np.asarray(image.convert('RGBA')).copy()
    masks = color_masks(p)
    s = scores(p)
    removed = {}
    border = np.zeros(p.shape[:2], dtype=bool)
    border[[0, -1], :] = True
    border[:, [0, -1]] = True
    for color in COLORS:
        flat = masks[color] & (s[color] >= 200) & (p[:, :, 3] >= 240)
        seeds = flat & border
        if seeds.sum() < max(8, border.sum() * .12):
            continue
        backing = ndimage.binary_propagation(seeds, mask=flat)
        p[backing, 3] = 0
        removed[color] = int(backing.sum())
    return Image.fromarray(p), removed


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def resolve_record_path(value, base=PAPER):
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    if path.parts[0] in ('level_generation', 'assets_dev'):
        return (ROOT / path).resolve()
    if path.parts[0] in ('chat_bundles', 'checkpoint', 'chat_returns'):
        return (HERE / path).resolve()
    return (base / path).resolve()


def provenance_index():
    """Index recorded preparation/repair hashes; never choose a master by mtime."""
    index = defaultdict(list)
    paths = sorted(set(PAPER.glob('*/manifest.json')) | set(PAPER.glob('*/repairs.json')))
    for path in paths:
        for row in walk_dicts(read(path)):
            digest = row.get('sha256')
            if isinstance(digest, str) and len(digest) == 64 and ('path' in row or 'operations' in row):
                index[digest].append((path, row))
    return index


def master_specs(record, index):
    """Return proven current-lineage raw crops, not every historical attempt."""
    specs = []
    visited = set()

    def add(path, crop, kind, evidence, expected=None):
        path = resolve_record_path(str(path))
        if not path.is_file():
            raise FileNotFoundError(path)
        if expected and sha(path) != expected:
            raise ValueError(f'Master hash changed: {path}')
        spec = dict(path=relative(path), crop=crop, kind=kind, evidence=relative(evidence), sha256=sha(path))
        if spec not in specs:
            specs.append(spec)

    def follow(digest):
        if digest in visited:
            return
        visited.add(digest)
        for evidence, row in index.get(digest, []):
            raw, crop = row.get('raw'), row.get('raw_rect')
            if raw and crop:
                add(raw, crop, 'recorded_raw_crop', evidence, row.get('raw_sha256'))
            for op in row.get('operations', []):
                raw = op.get('master') or op.get('raw')
                crop = op.get('raw_crop') or op.get('raw_search_box') or op.get('component', {}).get('box')
                if raw and (crop or 'master' in op):
                    add(raw, crop, 'repair_input', evidence, op.get('master_sha256') or op.get('raw_sha256'))
            # Only follow the old image if a replacement master was not recorded.
            # Repairs with new masters supersede the old candidate completely.
            if not any(op.get('master') or op.get('raw') for op in row.get('operations', [])):
                if row.get('old_sha256'):
                    follow(row['old_sha256'])
    follow(record['sha256'])
    reviewed = Path(record['reviewed_artifact']).resolve()
    clean = reviewed.with_name(reviewed.stem + '-clean-master.png')
    if clean.is_file():
        add(clean, None, 'clean_master_sibling', reviewed)
    if 'portrait_opaque_regen' in str(reviewed) and reviewed.parent.name == 'restored':
        frame = int(reviewed.stem)
        part = 'A' if frame <= 28 else 'B'
        report = reviewed.parent.parent / part / 'report.json'
        detail = read(report)
        panel = detail['panels'][(frame - 1) % 28]
        box = panel['raw_rect_ltrb'].copy()
        if 'portrait_opaque_regen_remaining' in str(reviewed):
            box = [box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2]
        add(detail['raw'], box, 'opaque_portrait_panel', report, detail['raw_sha256'])
    return specs


@lru_cache(maxsize=4)
def load_rgba(path):
    with Image.open(path) as image:
        return image.convert('RGBA')


def preview(image, native, masks, path):
    """Native, accepted on dark/light, then a magnified flagged-pixel detail."""
    w, h = 225, 230
    canvas = Image.new('RGB', (w * 5, h + 26), '#30343a')
    draw = ImageDraw.Draw(canvas)
    union = np.logical_or.reduce(list(masks.values()))
    box = bounds(union)
    if box:
        # Center the detail on the densest local signal, not a giant union box.
        density = ndimage.uniform_filter(union.astype(float), size=24)
        y, x = np.unravel_index(density.argmax(), density.shape)
        box = [max(0, int(x) - 28), max(0, int(y) - 28),
               min(image.width, int(x) + 28), min(image.height, int(y) + 28)]
    marked = np.asarray(image.convert('RGBA')).copy()
    marked[union] = (255, 165, 0, 255)
    panels = [(native or image, '#454b50', 'Original (rendered)' if native else 'Master (no native link)'),
              (image, '#181818', 'Scanned image / dark'), (image, '#dedede', 'Scanned image / light'),
              (image.crop(box) if box else image, '#30343a', 'Unmodified edge detail'),
              (Image.fromarray(marked).crop(box) if box else image, '#30343a', 'Orange = suspect pixels')]
    for i, (pic, bg, title) in enumerate(panels):
        pic = pic.copy()
        scale = min(w / pic.width, h / pic.height)
        pic = pic.resize((max(1, round(pic.width * scale)), max(1, round(pic.height * scale))),
                         Image.Resampling.NEAREST if i in (0, 3, 4) else Image.Resampling.LANCZOS)
        tile = Image.new('RGBA', (w, h), bg)
        tile.alpha_composite(pic, ((w - pic.width) // 2, (h - pic.height) // 2))
        canvas.paste(tile.convert('RGB'), (i * w, 26))
        draw.text((i * w + 4, 6), title, fill='white')
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, quality=90)


def write_report(output, report):
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'report.js').write_text('window.SPILL_REPORT = ' + json.dumps(report) + ';\n')
    with (output / 'findings.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['scope', 'target', 'status', 'color', 'color_status', 'weighted_pixels',
                         'edge_pixels', 'source_keys', 'path', 'sha256', 'crop'])
        for row in report['records']:
            for color, result in row['metrics']['colors'].items():
                if result['status'] != 'no_spill_detected':
                    writer.writerow([row['scope'], row.get('target', ''), row['metrics']['status'], color,
                        result['status'], result['alpha_weighted_pixels'], result['edge_pixels'],
                        json.dumps(row.get('native', {}).get('key_colors', [])), row['path'], row['sha256'],
                        json.dumps(row.get('crop'))])
    write_viewer(output)


def write_viewer(output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.html').write_bytes((HERE / 'spill_review.html').read_bytes())
    (output / 'review.js').write_bytes((HERE / 'spill_review.js').read_bytes())


def summarize(records, accepted, errors, examined_keys):
    finals = [r for r in records if r['scope'] == 'accepted_x2']
    linked = [r for r in records if r['scope'] == 'linked_master']
    retained = [r for r in records if r['scope'] == 'retained_master']
    linked_targets = {r['target'] for r in linked}
    return dict(accepted_expected=len(accepted), accepted_scanned=len(finals),
        complete_x2_scan={r['target'] for r in finals} == set(accepted),
        complete_master_scan=not errors,
        unique_accepted_image_hashes=len({r['sha256'] for r in finals}),
        targets_with_linked_master=len(linked_targets),
        targets_without_linked_master=sorted(set(examined_keys) - linked_targets),
        linked_master_files=len({r['path'] for r in linked}), additional_named_master_files=len(retained),
        errors=errors,
        by_scope={scope: dict(Counter(r['metrics']['status'] for r in records if r['scope'] == scope))
                  for scope in sorted({r['scope'] for r in records})},
        by_color={scope: {color: dict(Counter(r['metrics']['colors'][color]['status'] for r in records
                    if r['scope'] == scope)) for color in COLORS}
                  for scope in sorted({r['scope'] for r in records})},
        unique_x2_hashes_by_status={status: len({r['sha256'] for r in finals if r['metrics']['status'] == status})
                                    for status in RANK})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=HERE / 'runtime_install_20260926/accepted.json')
    parser.add_argument('--output', type=Path, default=HERE / 'spill_audit_20260926')
    parser.add_argument('--limit', type=int, help='Diagnostic subset, explicitly marked incomplete')
    parser.add_argument('--skip-retained-masters', action='store_true')
    parser.add_argument('--refresh-viewer', action='store_true', help='Update only the review UI; do not rescan images')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.refresh_viewer:
        write_viewer(output)
        print(f'Updated review UI: {output / "index.html"}')
        return
    accepted = read(args.manifest)['records']
    contracts = {t['id']: t for t in read(HERE / 'expected_targets.json')['targets']}
    ledger_path = HERE / 'checkpoint/state.json'
    ledger_before = sha(ledger_path)
    index = provenance_index()
    records, errors = [], []
    master_paths = set()
    keys = sorted(accepted)[:args.limit]
    for number, target in enumerate(keys, 1):
        row = accepted[target]
        path = Path(row['artifact'])
        try:
            if sha(path) != row['sha256'] or sha(ROOT / row['runtime_output_path']) != row['sha256']:
                raise ValueError('Accepted/runtime hash mismatch')
            native, info = native_reference(contracts[target])
            image = load_rgba(path)
            if list(image.size) != row['x2_size']:
                raise ValueError('Accepted canvas mismatch')
            metrics, masks = measure(image, native)
            entry = dict(scope='accepted_x2', target=target, treatment=contracts[target]['treatment'],
                path=relative(path), sha256=row['sha256'], native=info, metrics=metrics,
                reviewed_artifact=relative(row['reviewed_artifact']))
            if metrics['status'] in ('likely_spill', 'color_material_review'):
                file = 'previews/x2/' + target + '.jpg'
                preview(image, native, masks, output / file)
                entry['preview'] = file
            records.append(entry)
            specs = master_specs(row, index)
            entry['linked_masters'] = specs
            for spec in specs:
                master_path = ROOT / spec['path']
                master_paths.add(master_path)
                master = load_rgba(master_path)
                if spec['crop']:
                    x0, y0, x1, y1 = spec['crop']
                    if not (0 <= x0 < x1 <= master.width and 0 <= y0 < y1 <= master.height):
                        raise ValueError(f'Invalid recorded master crop: {spec}')
                    master = master.crop(spec['crop'])
                removed = {}
                if spec['kind'] != 'opaque_portrait_panel':
                    master, removed = suppress_sheet_matte(master)
                # Match normalized edge thickness while measuring original master pixels.
                edge_width = max(3, round(3 * min(master.width / image.width, master.height / image.height)))
                # Cropped/fitted cutouts have different registration: native color
                # support is approximate and master findings remain advisory.
                master_metrics, master_masks = measure(master, native, edge_width)
                master_entry = dict(scope='linked_master', target=target, **spec, metrics=master_metrics,
                                    matte_background_excluded=removed, native=info)
                if master_metrics['status'] in ('likely_spill', 'color_material_review'):
                    file = 'previews/masters/' + target + f'-{len(records)}.jpg'
                    preview(master, native, master_masks, output / file)
                    master_entry['preview'] = file
                records.append(master_entry)
        except (OSError, ValueError, KeyError, IndexError) as error:
            errors.append(dict(target=target, error=str(error)))
        if number % 250 == 0:
            print(f'Scanned {number}/{len(keys)} accepted icons and their linked masters', flush=True)
    retained_count = 0
    if not args.skip_retained_masters:
        for path in sorted(HERE.parent.rglob('*master*.png')):
            if path in master_paths or output in path.parents:
                continue
            try:
                master, removed = suppress_sheet_matte(load_rgba(path))
                metrics, masks = measure(master)
                entry = dict(scope='retained_master', path=relative(path), sha256=sha(path), metrics=metrics,
                             matte_background_excluded=removed,
                             note='Retained named master; current lineage not established. May be superseded.')
                if metrics['status'] in ('likely_spill', 'color_material_review'):
                    file = 'previews/retained/' + sha(path)[:20] + '.jpg'
                    if not (output / file).exists():
                        preview(master, None, masks, output / file)
                    entry['preview'] = file
                records.append(entry)
                retained_count += 1
            except (OSError, ValueError) as error:
                errors.append(dict(path=relative(path), error=str(error)))
            if retained_count % 250 == 0:
                print(f'Scanned {retained_count} additional retained masters', flush=True)
    records.sort(key=lambda r: (RANK[r['metrics']['status']],
        -sum(c['alpha_weighted_pixels'] for c in r['metrics']['colors'].values()), r.get('target', r['path'])))
    summary = summarize(records, accepted, errors, keys)
    ledger_after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    if ledger_after != ledger_before:
        raise RuntimeError('Ledger changed during scan; rerun against a stable snapshot')
    report = dict(schema='openyamm-icon-spill-screen-v1', method='native-aware-visible-edge-chroma-v2',
        manifest=relative(args.manifest), manifest_sha256=sha(args.manifest), ledger_sha256=ledger_before,
        root_url=os.path.relpath(ROOT, output),
        script_sha256=sha(Path(__file__)), summary=summary, records=records,
        limitations=['Classification is not visual rejection or permission to recolor artwork.',
            'Native color support is approximate after fitting; intentional materials/glows need review.',
            'Named retained masters can be superseded. Their findings do not imply current export defects.',
            'Unlinked raw sheets are not scanned as if their intentional backing were spill.',
            'No artwork, placement, acceptance decisions or runtime files were changed.'])
    write_report(output, report)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('targets_without_linked_master', 'by_color')}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
