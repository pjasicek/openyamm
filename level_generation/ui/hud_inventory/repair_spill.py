"""Stage geometry-preserving color repairs for the accepted spill-review queue.

No resampling, silhouette editing, ledger acceptance or runtime installation.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import scan_spill as scan

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'spill_repairs_20260927/review'
ITEMS = {'inventory_items', 'fitted_equipment_variants', 'paperdoll_parts'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def inspect_background(image):
    """Inspect the actual image; never infer its matte from a native BMP key."""
    p = np.asarray(image.convert('RGBA'))
    a = p[:, :, 3]
    border = np.concatenate([p[0], p[-1], p[1:-1, 0], p[1:-1, -1]])
    transparent = float(np.mean(border[:, 3] < 8))
    visible = border[border[:, 3] >= 240]
    keys = {}
    if len(visible):
        c = visible[:, :3].astype(int)
        gaps = {'magenta': np.minimum(c[:, 0], c[:, 2]) - c[:, 1],
                'green': c[:, 1] - np.maximum(c[:, 0], c[:, 2]),
                'cyan': np.minimum(c[:, 1], c[:, 2]) - c[:, 0]}
        for name, gap in gaps.items():
            hit = gap > 180
            if hit.sum() >= max(8, len(border) * .15):
                keys[name] = {'border_fraction': round(float(hit.sum() / len(border)), 4),
                              'median_rgb': np.median(c[hit], axis=0).astype(int).tolist()}
    mode = 'true_alpha' if transparent > .2 else 'keyed_' + max(keys, key=lambda k: keys[k]['border_fraction']) if keys else 'opaque_or_unconfirmed'
    return dict(mode=mode, keys=keys, alpha_range=[int(a.min()), int(a.max())],
                transparent_border_fraction=round(transparent, 4))


@lru_cache(maxsize=1000)
def background(path):
    with Image.open(path) as image:
        result = inspect_background(image)
    return dict(path=scan.relative(path), sha256=digest(path), **result)


def native_chroma(native, size):
    p = np.asarray(native.convert('RGBA'))
    opaque = p[:, :, 3] >= 64
    result = {}
    for color, values in scan.scores(p).items():
        # Native colors are an advisory material guide, not a new geometry mask.
        values = ndimage.maximum_filter(np.where(opaque, np.maximum(values, 0), 0), size=5)
        result[color] = np.asarray(Image.fromarray(values.astype('uint8')).resize(size, Image.Resampling.NEAREST))
    return result


def repair(image, native, treatment, master_keys=(), protected_effect=False, regions=()):
    before = np.asarray(image.convert('RGBA'))
    output = before.copy()
    a = before[:, :, 3]
    visible = a >= 8
    y, x = np.indices(a.shape)
    border_distance = np.minimum.reduce([x, y, a.shape[1] - 1 - x, a.shape[0] - 1 - y])
    inside = scan.distance_inside(visible)
    chroma = scan.scores(before)
    native_max = native_chroma(native, image.size)
    native_rgba = np.asarray(native.convert('RGBA'))
    opaque_panel = (a >= 240).mean() > .96 and treatment not in {'inventory_items', 'fitted_equipment_variants'}
    geometry = 'opaque_canvas_border' if opaque_panel else 'alpha_contour'
    allowed = (border_distance <= 4) if opaque_panel else ((inside <= 5) | (a < 240))
    masks = {}
    original_has_color = {}
    for color in scan.COLORS:
        values = chroma[color]
        native_values = native_max[color].astype(int)
        native_scores = scan.scores(native_rgba)[color]
        original_has_color[color] = bool(np.any((native_scores >= 24) & (native_rgba[:, :, 3] >= 64)))
        minimum = 18 if color != 'cyan' else 26
        foreign = (values > np.maximum(minimum, native_values + 18))
        # A generated magenta rim can sit beside native purple paint. Require a
        # substantial excess before touching that material's edge.
        foreign |= (values > 100) & (values > native_values + 45)
        # The raw restoration key may differ from the game's palette key. A
        # confirmed master key also permits local repairs inside a cutout when
        # that color has no support in the native neighborhood. Do not use
        # the original cyan palette key as proof of cyan spill in a new master.
        interior = np.zeros(a.shape, bool)
        if not opaque_panel and treatment in ITEMS and color in master_keys:
            interior = foreign & (values > 40) & (native_values < 18)
        mask = visible & (allowed | interior) & foreign
        if opaque_panel and color != 'magenta':
            mask &= (values >= 100) & (border_distance <= 1)
        if treatment == 'spell_icon_pair' and color != 'magenta':
            # Green/cyan spell energy is not a cutout-key error by color alone.
            mask[:] = False
        if protected_effect or treatment == 'spell_icon_pair':
            # Ink, spell glyphs and glows need their page/animation context.
            # Their restored hue is not a background-key defect by itself.
            mask[:] = False
        masks[color] = mask
    bad = np.logical_or.reduce(list(masks.values()))
    changed = np.zeros(a.shape, bool)
    distances = np.zeros(a.shape)
    unresolved = bad.copy()
    if bad.any():
        # Exclude contaminated donors; preserve real green/cyan/purple materials
        # when their native neighborhood supports that color.
        clean = (a >= 192) & ~bad
        if clean.any():
            distances, indices = ndimage.distance_transform_edt(~clean, return_indices=True)
            usable = bad & (distances <= 8)
            output[:, :, :3][usable] = before[indices[0], indices[1], :3][usable]
            changed = np.any(before != output, axis=2)
            unresolved = bad & ~usable
    donor_max_distance = round(float(distances[changed].max()), 3) if changed.any() else 0
    for region in regions:
        # Explicitly inspected thin features can lack any nearby clean donor.
        # Keep their alpha and luminance; replace only the contaminated tint.
        assert region['method'] == 'native_brown_string_tint'
        left,top,right,bottom = region['box']
        rgb = output[top:bottom,left:right,:3].astype(float)
        luma = rgb @ np.array([.2126,.7152,.0722])
        tint = np.array([1.15,.95,.60])
        tint /= tint @ np.array([.2126,.7152,.0722])
        opaque = visible[top:bottom,left:right]
        output[top:bottom,left:right,:3][opaque] = np.clip(np.rint(luma[:,:,None]*tint),0,255).astype('uint8')[opaque]
        unresolved[top:bottom,left:right][opaque] = False
    changed = np.any(before != output, axis=2)
    # Existing alpha is authoritative: recolor the fringe, never refit the item.
    assert np.array_equal(output[:, :, 3], before[:, :, 3])
    assert np.array_equal(output[~changed], before[~changed])
    return Image.fromarray(output), dict(method='local_foreground_rgb_extension', geometry=geometry,
        selected_pixels={k:int(v.sum()) for k,v in masks.items()}, changed_pixels=int(changed.sum()),
        unresolved_pixels=int(unresolved.sum()), max_donor_distance=donor_max_distance,
        alpha_identical=True, dimensions_identical=True, clean_pixels_identical=True,
        original_has_color=original_has_color, confirmed_master_keys=sorted(master_keys),
        protected_effect=protected_effect or treatment=='spell_icon_pair',inspected_regions=list(regions)), changed


def comparison(before, after, changed, output):
    # Exact-size images remain separately linked; the proof is display-only.
    panels = []
    h, w = changed.shape
    density = ndimage.uniform_filter(changed.astype(float), size=20)
    yy, xx = np.unravel_index(density.argmax(), density.shape)
    box = (max(0, int(xx)-24), max(0, int(yy)-24), min(w, int(xx)+24), min(h, int(yy)+24))
    for image, label, bg, detail in [(before, 'Current / dark', '#171717', False),
            (after, 'Repair / dark', '#171717', False), (after, 'Repair / light', '#e3e3e3', False),
            (before.crop(box), 'Current detail', '#484848', True),
            (after.crop(box), 'Repair detail', '#484848', True)]:
        frame = Image.new('RGBA', (220, 260), bg)
        piece = image.copy()
        factor = min(214/piece.width, 228/piece.height)
        piece = piece.resize((max(1,round(piece.width*factor)),max(1,round(piece.height*factor))),
                             Image.Resampling.NEAREST if detail else Image.Resampling.LANCZOS)
        frame.alpha_composite(piece, ((220-piece.width)//2, 28+(228-piece.height)//2))
        ImageDraw.Draw(frame).text((4,5),label,fill='white' if bg != '#e3e3e3' else 'black')
        panels.append(frame)
    sheet = Image.new('RGB', (1100,260))
    for i,panel in enumerate(panels): sheet.paste(panel,(i*220,0))
    output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output,quality=93)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', nargs='*', help='Optional pilot target stems')
    parser.add_argument('--output', type=Path, default=OUT)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    report=scan.read(HERE/'spill_audit_20260926/report.json')
    accepted=scan.read(HERE/'runtime_install_20260926/accepted.json')['records']
    contracts={t['id']:t for t in scan.read(HERE/'expected_targets.json')['targets']}
    overrides_path=HERE/'spill_repairs_20260927/inspected_regions.json'
    overrides=scan.read(overrides_path)['records'] if overrides_path.exists() else {}
    rows=[r for r in report['records'] if r['scope']=='accepted_x2' and r['metrics']['status']=='likely_spill']
    if args.targets: rows=[r for r in rows if contracts[r['target']]['runtime_name'] in args.targets]
    guard_paths=[HERE/'checkpoint/state.json',ROOT/'assets_dev/engine/data_tables/item_visuals.txt',
                 HERE/'finalization_20260926/placements.json']
    guards={scan.relative(p):digest(p) for p in guard_paths}
    results=[];cache={}
    for index,row in enumerate(rows,1):
        target=row['target'];contract=contracts[target];entry=accepted[target]
        path=ROOT/row['path']
        assert digest(path)==digest(ROOT/entry['runtime_output_path'])==entry['sha256']==row['sha256'], target
        with Image.open(path) as image: before=image.convert('RGBA')
        native,info=scan.native_reference(contract)
        masters=[]
        for spec in row.get('linked_masters',[]):
            p=ROOT/spec['path']
            try:
                masters.append({**background(p), 'crop':spec.get('crop'),
                                'link_kind':spec.get('kind'), 'evidence':spec.get('evidence')})
            except (OSError, ValueError) as exc:
                masters.append(dict(path=scan.relative(p),mode='unreadable',error=str(exc)))
        master_keys={m['mode'].removeprefix('keyed_') for m in masters if m['mode'].startswith('keyed_')}
        protected_effect=bool(re.match(r'^(?:spell\d|sp\d{2}|zapp\d|convol\d)',contract['runtime_name']))
        override=overrides.get(target,{})
        if override: assert override['before_sha256']==entry['sha256'],target
        regions=override.get('regions',[])
        identity=(row['sha256'],entry['source_sha256'],row['treatment'],tuple(sorted(master_keys)),protected_effect,json.dumps(regions))
        if identity not in cache:
            after,operation,changed=repair(before,native,row['treatment'],master_keys,protected_effect,regions)
            metrics,_=scan.measure(after,native)
            if len(cache)>=32: cache.pop(next(iter(cache)))
            cache[identity]=(after,operation,changed,metrics)
        after,operation,changed,metrics=cache[identity]
        record=dict(target=target,treatment=row['treatment'],before=scan.relative(path),
            before_sha256=entry['sha256'],source=info,master_backgrounds=masters,
            current_alpha_range=list(before.getchannel('A').getextrema()),
            background_technique=('repair_opaque_perimeter_rgb' if operation['geometry']=='opaque_canvas_border'
                                  else 'preserve_delivered_alpha_correct_rgb_only'),
            master_evidence='linked_reference_not_assumed_to_be_latest_parent' if masters else 'no_recovered_master_link',
            operation=operation,before_metrics=row['metrics'],after_metrics=metrics,
            offsets_preserved=True)
        if changed.any():
            dest=out/'candidates'/Path(entry['runtime_output_path']).relative_to('assets_dev')
            # Runtime retains some historical .bmp/.pcx names, with PNG payloads.
            dest.parent.mkdir(parents=True,exist_ok=True);after.save(dest,format='PNG');dest.chmod(0o644)
            with Image.open(dest) as check:
                assert check.size == before.size and check.format == 'PNG', target
                assert np.array_equal(np.asarray(check.convert('RGBA')),np.asarray(after)), target
            mask=out/'masks'/(target+'.png');mask.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(changed.astype('uint8')*255).save(mask)
            proof=out/'previews'/(target+'.jpg');comparison(before,after,changed,proof)
            record.update(candidate=scan.relative(dest),sha256=digest(dest),mask=scan.relative(mask),
                          preview=scan.relative(proof),status='repair_candidate')
            if operation['unresolved_pixels']: record['status']='needs_local_review'
        else:
            record['status']='needs_local_review' if operation['unresolved_pixels'] else 'native_color_or_context_review'
        if operation['protected_effect']: record['status']='protected_spell_art_context_review'
        reference=out/'references'/(target+'.png');reference.parent.mkdir(parents=True,exist_ok=True)
        native.save(reference)
        record['native_reference']=scan.relative(reference)
        results.append(record)
        if index%100==0:print(f'{index}/{len(rows)} processed',flush=True)
    assert all(digest(ROOT/p)==expected for p,expected in guards.items())
    summary=dict(targets=len(results),status=dict(Counter(r['status'] for r in results)),
        treatment=dict(Counter(r['treatment'] for r in results)),
        alpha_changes=0,canvas_changes=0,offset_changes=0,imagegen_calls=0,
        candidate_rescan=dict(Counter(r['after_metrics']['status'] for r in results if 'candidate' in r)))
    master_files={m['path']:m for r in results for m in r['master_backgrounds']}
    summary.update(linked_master_targets=sum(bool(r['master_backgrounds']) for r in results),
        targets_without_master_link=sum(not r['master_backgrounds'] for r in results),
        unique_linked_masters=len(master_files),
        master_modes=dict(Counter(m['mode'] for m in master_files.values())),
        inventory_equipment_entries=sum(r['treatment'] in ITEMS-{'paperdoll_parts'} for r in results),
        inventory_equipment_candidates=sum(r['treatment'] in ITEMS-{'paperdoll_parts'} and 'candidate' in r for r in results))
    manifest=dict(schema='openyamm-spill-repair-candidates-v1',approval='staged_for_review',
        scope='All 1722 likely-spill x2 records, including aliases; optional --targets is an explicit pilot subset.',
        scan_sha256=digest(HERE/'spill_audit_20260926/report.json'),guards=guards,
        recipe_sha256=digest(Path(__file__)),inspected_regions_sha256=digest(overrides_path) if overrides_path.exists() else None,
        summary=summary,records=results)
    save(out/'manifest.json',manifest)
    viewer_data=dict(summary=summary,recipe_sha256=manifest['recipe_sha256'],records=[{
        k:v for k,v in row.items() if k not in ('before_metrics','after_metrics')
    } | {'before_scan':row['before_metrics']['status'],'after_scan':row['after_metrics']['status']}
        for row in results])
    (out/'data.js').write_text('window.SPILL_REPAIRS = '+json.dumps(viewer_data)+';\n')
    for source,dest in [('spill_repair_review.html','index.html'),('spill_repair_review.js','review.js')]:
        if (HERE/source).exists(): (out/dest).write_bytes((HERE/source).read_bytes())
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
