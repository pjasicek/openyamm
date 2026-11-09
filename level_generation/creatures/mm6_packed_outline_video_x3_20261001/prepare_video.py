"""Prepare a separate MM6 packed-outline AnimeVideo x3 finishing comparison."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import statistics
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CREATURES = REPO / 'level_generation/creatures'
CACHE = Path('/tmp/mm6test/mm6_outline_video_x3')
METRIC = ('Uncapped arithmetic mean of the measured sampling of multi-pose composite sheets, '
          'with one equal vote per sheet. Single-sprite sheets, retained frames outside the packed '
          'run, empty native endpoints, palette multiplication and repeated holds are excluded. '
          'Within a sheet, sampling is the mean of min(x, y) over its registered native bitmaps.')


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(capped=False):
    selection = read(HERE / 'selection.json') if (HERE / 'selection.json').exists() else {}
    requested = selection.get('requested_families', [])
    paths = list(CREATURES.glob('mm6_packed_outline*/**/redo_2x/run.json'))
    paths.append(CREATURES / 'mm6_goblin/outline_walk_detail_v2/redo_2x/run.json')
    rows = []
    for path in sorted(paths):
        if not path.exists() or any(part in path.parts for part in ['checkpoints', 'partial_export']):
            continue
        run = read(path)
        if 'jobs' not in run or not path.with_name('registration.json').exists():
            continue
        records = read(path.with_name('registration.json'))
        config_path = path.with_name('config.json')
        config = read(config_path) if config_path.exists() else {}
        samples = [min(r['effective_sampling_xy']) for r in records.values()
                   if not r.get('empty_native_endpoint')]
        sheets = []
        composite_samples = []
        for job in run['jobs']:
            values = [min(r['effective_sampling_xy']) for r in records.values()
                      if r['batch'] == job['id'] and not r.get('empty_native_endpoint')]
            if not values:
                continue
            composite = len(job['frames']) > 1
            sheets.append(dict(job=job['id'], kind='composite' if composite else 'single_sprite',
                               pose_count=len(job['frames']), native_bitmaps=len(values),
                               mean_sampling=statistics.mean(values), minimum_sampling=min(values),
                               maximum_sampling=max(values)))
            if composite:
                composite_samples.extend(values)
        composite_sheets = [s for s in sheets if s['kind'] == 'composite']
        main_sheets = [s for s in composite_sheets if not s['job'].startswith('unused_')]
        average = statistics.mean(s['mean_sampling'] for s in composite_sheets)
        capped_average = statistics.mean(min(2, s['mean_sampling']) for s in composite_sheets)
        all_bitmap_average = statistics.mean(samples)
        row = dict(family=config.get('family', 'goblin'), title=config.get('title', 'MM6 Goblin'),
                   source=str(path.parent.relative_to(REPO)), source_status=run['status'],
                   frames=len(records), sheets=len(run['jobs']), mean_source_sampling=average,
                   mean_all_bitmap_source_sampling=all_bitmap_average,
                   mean_composite_frame_sampling=statistics.mean(composite_samples),
                   mean_main_animation_composite_sampling=statistics.mean(s['mean_sampling'] for s in main_sheets),
                   composite_sheets=len(composite_sheets), composite_frames=len(composite_samples),
                   single_sprite_sheets=sum(s['kind'] == 'single_sprite' for s in sheets),
                   single_sprite_frames=sum(s['native_bitmaps'] for s in sheets if s['kind'] == 'single_sprite'),
                   retained_frames_outside_packed_run=len(samples) - sum(s['native_bitmaps'] for s in sheets),
                   sampling_by_sheet=sheets,
                   mean_source_sampling_capped_at_2=capped_average, minimum_source_sampling=min(samples),
                   maximum_source_sampling=max(samples), below_2_frames=sum(s < 2 for s in samples),
                   explicitly_requested=config.get('family', 'goblin') in requested,
                   selected=((capped_average if capped else average) < 1.7 or
                             config.get('family', 'goblin') in requested) and run['status'] == 'validated')
        rows.append(row)
    save(HERE / 'inventory.json', dict(
        cutoff=1.7, metric=METRIC,
        cap_at_2=capped, requested_families=requested, families=rows))
    return rows


def prepare(capped=False):
    rows = inventory(capped)
    previous = read(HERE / 'jobs.json')['jobs'] if (HERE / 'jobs.json').exists() else []
    previous = {(j['family'], j['job']): j for j in previous}
    (CACHE / 'input').mkdir(parents=True, exist_ok=True)
    (CACHE / 'video_x3_rgb').mkdir(exist_ok=True)
    pending = CACHE / 'input_pending_composite'
    pending.mkdir(exist_ok=True)
    jobs = []
    pending_count = 0
    for row in rows:
        if not row['selected']:
            continue
        src = REPO / row['source']
        run, records = read(src / 'run.json'), read(src / 'registration.json')
        out = HERE / ('mm6_' + row['family']) / 'redo_2x'
        (out / 'provenance').mkdir(parents=True, exist_ok=True)
        for filename in ['run.json', 'registration.json', 'processing.json', 'acceptance.json']:
            if (src / filename).exists():
                shutil.copy2(src / filename, out / 'provenance' / ('source_' + filename))
        for job in run['jobs']:
            assert job.get('selected_raw'), (row['family'], job['id'], 'missing selected sheet')
            report = read(src / 'review' / (job['id'] + '_extraction.json'))
            assert report['raw'] == job['selected_raw']
            raw = REPO / report['raw']
            assert digest(raw) == report['raw_sha256']
            old = previous.get((row['family'], job['id']))
            if old and (out / 'upscale.json').exists():
                finished = next((j for j in read(out / 'upscale.json')['jobs'] if j['job'] == job['id']), None)
                contributors = [dict(frame=f['frame'], clean=str((REPO / f['clean_path']).relative_to(REPO)),
                                     clean_sha256=digest(REPO / f['clean_path']), raw_rect=f['raw_rect'])
                                for f in report['frames']]
                cached = bool(finished and old['source_sha256'] == report['raw_sha256'] and
                              old['contributors'] == contributors and old['original_frames'] == job['frames'] and
                              Path(old['input']).exists() and digest(Path(old['input'])) == old['input_sha256'] and
                              Path(old['output']).exists() and digest(Path(old['output'])) == finished['output_sha256'])
                if cached:
                    old['output_sha256'] = finished['output_sha256']
                    target = pending / Path(old['input']).name
                    if target.exists():
                        assert digest(target) == old['input_sha256']
                        target.unlink()
                    jobs.append(old)
                    continue
            sheet = Image.new('RGBA', tuple(report['raw_size']))
            contributors = []
            for frame in report['frames']:
                clean = REPO / frame['clean_path']
                image = Image.open(clean).convert('RGBA')
                rect = frame['raw_rect']
                assert image.size == (rect[2] - rect[0], rect[3] - rect[1])
                sheet.alpha_composite(image, tuple(rect[:2]))
                contributors.append(dict(frame=frame['frame'], clean=str(clean.relative_to(REPO)),
                                         clean_sha256=digest(clean), raw_rect=rect))
            pixels = np.array(sheet)
            solid = pixels[..., 3] > 0
            assert solid.any()
            _, nearest = ndimage.distance_transform_edt(~solid, return_indices=True)
            pixels[..., :3][~solid] = pixels[nearest[0], nearest[1], :3][~solid]
            name = row['family'] + '__' + job['id'] + '.png'
            inp = CACHE / 'input' / name
            Image.fromarray(pixels[..., :3]).save(inp)
            job_record = dict(family=row['family'], job=job['id'], source_sheet=str(raw.relative_to(REPO)),
                              source_sha256=digest(raw), raw_size=report['raw_size'], input=str(inp),
                              input_sha256=digest(inp), output=str(CACHE / 'video_x3_rgb' / name),
                              contributors=contributors, original_frames=job['frames'])
            old = previous.get((row['family'], job['id']))
            output = Path(job_record['output'])
            reused = bool(old and old['input_sha256'] == job_record['input_sha256'] and
                          output.exists() and old.get('output_sha256') == digest(output))
            # Finishing metadata owns the output hash after the initial model pass.
            metadata_path = out / 'upscale.json'
            if old and not reused and metadata_path.exists() and output.exists():
                finished = next((j for j in read(metadata_path)['jobs'] if j['job'] == job['id']), None)
                reused = bool(finished and finished['input_sha256'] == job_record['input_sha256'] and
                              finished.get('output_sha256') == digest(output))
            if reused:
                job_record['output_sha256'] = digest(output)
                target = pending / name
                if target.exists():
                    assert digest(target) == job_record['input_sha256']
                    target.unlink()
            else:
                target = pending / name
                if target.is_symlink():
                    assert target.resolve() == inp.resolve()
                    target.unlink()
                if not target.exists():
                    os.link(inp, target)
                else:
                    assert digest(target) == job_record['input_sha256']
                pending_count += 1
            jobs.append(job_record)
        print(row['title'], f"mean {row['mean_source_sampling']:.3f}x, {row['sheets']} complete sheets", flush=True)
    save(HERE / 'jobs.json', dict(model='realesr-animevideov3', scale=3, tile=256, jobs=jobs,
        input_policy='Reassemble all accepted cleaned returned poses at their original raw-sheet coordinates, '
        'including repeated steps. Extend nearest foreground RGB into transparency only for model inference. '
        'Reuse accepted alpha, material masks and native registration for the final 2x exports.'))
    print('Prepared', len(jobs), 'model inputs;', pending_count, 'pending in', pending, flush=True)


def material_module(path):
    spec = importlib.util.spec_from_file_location('video_finish_materials', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def finish():
    sys.path.insert(0, str(CREATURES / 'mm6_peasants'))
    import package_family
    jobs = read(HERE / 'jobs.json')['jobs']
    rows = read(HERE / 'inventory.json')['families']
    completed = []
    for row in rows:
        if not row['selected']:
            continue
        src = REPO / row['source']
        dst = HERE / ('mm6_' + row['family']) / 'redo_2x'
        records, original = read(src / 'registration.json'), read(src / 'manifest.json')
        config = read(src / 'config.json')
        family_jobs = {j['job']: j for j in jobs if j['family'] == row['family']}
        metadata_path = dst / 'upscale.json'
        previous = read(metadata_path) if metadata_path.exists() else None
        if previous:
            assert previous['source_manifest_sha256'] == digest(src / 'manifest.json'), 'Source changed'
            assert previous['manifest_sha256'] == digest(dst / 'manifest.json'), 'Candidate manifest changed'
            previous_jobs = {j['job']: j for j in previous['jobs']}
            assert previous_jobs.keys() == family_jobs.keys(), 'Candidate sheet coverage changed'
            for job, j in family_jobs.items():
                assert previous_jobs[job]['input_sha256'] == j['input_sha256'], 'Model input changed'
                assert previous_jobs[job]['output_sha256'] == digest(Path(j['output'])), 'Model output changed'
            for asset, sha256 in previous['atlas_sha256'].items():
                assert digest(dst / asset) == sha256, 'Candidate atlas changed'
            manifest = read(dst / 'manifest.json')
            manifest['postprocess']['mean_source_sampling'] = row['mean_source_sampling']
            manifest['postprocess']['selection_metric'] = METRIC
            save(dst / 'manifest.json', manifest)
            template = (CREATURES / 'mm6_peasants/viewer.html').read_text()
            (dst / 'review.html').write_text(template.replace('__TITLE__', config['title'] + ' — Video x3 comparison')
                .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':'))))
            previous['manifest_sha256'] = digest(dst / 'manifest.json')
            previous['selection_metric'] = METRIC
            previous['mean_source_sampling'] = row['mean_source_sampling']
            save(metadata_path, previous)
            row.update(output=str(dst.relative_to(HERE)), prepared_sheets=len(family_jobs),
                       prepared_frames=len(records), palettes=len(manifest['variants']), reused_checkpoint=True)
            completed.append(row)
            print('REUSED', row['title'], len(family_jobs), 'sheets', flush=True)
            continue
        rendered = {}
        for job, j in family_jobs.items():
            path = Path(j['output'])
            assert path.exists(), path
            image = Image.open(path).convert('RGB')
            assert image.size == tuple(3 * d for d in j['raw_size']), (job, image.size)
            rendered[job] = image
            j['output_sha256'] = digest(path)
        for folder in ['aligned_2x', 'masks_2x', 'cleaned']:
            (dst / folder).mkdir(exist_ok=True)
        checked = []
        for name, r in records.items():
            clean = Image.open(REPO / r['clean_path']).convert('RGBA')
            expected = Image.open(src / 'aligned_2x' / (name + '.png')).convert('RGBA')
            x0, y0, x1, y1 = r['raw_rect']
            model_crop = rendered[r['batch']].crop((3*x0, 3*y0, 3*x1, 3*y1))
            size = tuple(max(1, round(d*r['scale'])) for d in clean.size)
            rgb = model_crop.resize(size, Image.Resampling.LANCZOS)
            aligned = Image.new('RGB', expected.size)
            aligned.paste(rgb, tuple(r['translate'][i] - r['canvas_origin_px'][i] for i in range(2)))
            result = aligned.convert('RGBA')
            result.putalpha(expected.getchannel('A'))
            pixels = np.array(result)
            pixels[pixels[..., 3] == 0, :3] = 0
            result = Image.fromarray(pixels)
            assert result.getchannel('A').tobytes() == expected.getchannel('A').tobytes()
            result.save(dst / 'aligned_2x' / (name + '.png'))
            shutil.copy2(src / 'masks_2x' / (name + '.png'), dst / 'masks_2x' / (name + '.png'))
            # The common exporter's source-edge audit consumes the unchanged accepted cleaned source.
            target = dst / 'cleaned' / (name + '.png')
            if not target.exists():
                target.symlink_to(os.path.relpath(REPO / r['clean_path'], target.parent))
            checked.append(dict(frame=name, source_alpha_sha256=hashlib.sha256(expected.getchannel('A').tobytes()).hexdigest()))
        for filename in ['sources.json', 'config.json', 'recolor_vectors.json', 'registration.json', 'calibration.json',
                         'recolor_presets.json', config.get('material_module', '')]:
            if filename and (src / filename).exists():
                shutil.copy2(src / filename, dst / filename)
        generation = read(src / 'generation.json')
        for batch in generation['batches'].values():
            for asset in [batch['raw'], batch['prompt'], *batch['references']]:
                asset['path'] = os.path.relpath((src / asset['path']).resolve(), dst)
        save(dst / 'generation.json', generation)
        if config.get('material_module'):
            materials = material_module(dst / config['material_module'])
            package_family.recolor = materials.recolor
        package_family.export(row['family'], dst, src.parent)
        manifest = read(dst / 'manifest.json')
        for key in ['logical_canvas', 'logical_pivot', 'native_frame_scale', 'animations', 'animations_by_palette',
                    'native_group_bindings', 'recolor_model', 'recolor', 'regions', 'variants', 'generated_detail']:
            if key in original:
                manifest[key] = original[key]
        assert manifest['frames'] == original['frames'], 'Changed frame placement, packing or aliases'
        assert manifest['pages'] == original['pages'], 'Changed page layout'
        manifest['quality_status'] = 'prepared_video_x3_comparison_pending_user_review'
        manifest['limitations'] = ['AnimeVideo x3 finishing candidate. Original generated sampling is unchanged. '
                                   'This does not inherit the source restoration acceptance.']
        manifest['postprocess'] = dict(model='realesr-animevideov3', scale=3, final_pixels_per_native_pixel=2,
            metadata='upscale.json', source_manifest=os.path.relpath(src / 'manifest.json', dst),
            source_manifest_sha256=digest(src / 'manifest.json'), mean_source_sampling=row['mean_source_sampling'],
            selection_metric=METRIC,
            preserve='Exact accepted alpha, native transforms, material masks, palette ramps, timing, mirrors and aliases')
        save(dst / 'manifest.json', manifest)
        template = (CREATURES / 'mm6_peasants/viewer.html').read_text()
        (dst / 'review.html').write_text(template.replace('__TITLE__', config['title'] + ' — Video x3 comparison')
            .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':'))))
        make_sheets(src, dst, records, config, family_jobs)
        for name, r in records.items():
            a = Image.open(src / 'aligned_2x' / (name + '.png')).getchannel('A')
            b = Image.open(dst / 'aligned_2x' / (name + '.png')).getchannel('A')
            assert a.tobytes() == b.tobytes(), name
            assert (src / 'masks_2x' / (name + '.png')).read_bytes() == (dst / 'masks_2x' / (name + '.png')).read_bytes(), name
        save(dst / 'upscale.json', dict(source=str(src.relative_to(REPO)), jobs=list(family_jobs.values()),
            selection_metric=METRIC, mean_source_sampling=row['mean_source_sampling'],
            source_manifest_sha256=digest(src / 'manifest.json'),
            source_acceptance_sha256=digest(src / 'acceptance.json'),
            manifest_sha256=digest(dst / 'manifest.json'),
            atlas_sha256={str(p.relative_to(dst)): digest(p)
                          for folder in ['atlas', 'previews'] for p in sorted((dst / folder).glob('*.png'))},
            alpha_checks=checked, technical_status='all_frames_same_alpha_masks_and_geometry',
            visual_status='prepared_for_review; source acceptance is retained only as provenance'))
        row['output'] = str(dst.relative_to(HERE))
        row['prepared_sheets'] = len(family_jobs)
        row['prepared_frames'] = len(records)
        row['palettes'] = len(manifest['variants'])
        completed.append(row)
        print('FINISHED', row['title'], len(family_jobs), 'sheets', len(records), 'frames', flush=True)
    previous_summary = read(HERE / 'result.json') if (HERE / 'result.json').exists() else {}
    requested = read(HERE / 'inventory.json').get('requested_families', [])
    requested_rows = [r for r in completed if r['family'] in requested]
    save(HERE / 'result.json', dict(**{k: v for k, v in previous_summary.items() if k not in {
        'prepared', 'total_sheets', 'total_frames', 'palettes', 'selection_metric', 'additional_candidates',
        'source_status_summary', 'requested_families', 'requested_sheets', 'requested_frames', 'requested_palettes'}},
        prepared=completed, total_sheets=sum(r['prepared_sheets'] for r in completed),
        total_frames=sum(r['prepared_frames'] for r in completed), palettes=sum(r['palettes'] for r in completed),
        requested_families=requested, requested_sheets=sum(r['prepared_sheets'] for r in requested_rows),
        requested_frames=sum(r['prepared_frames'] for r in requested_rows),
        requested_palettes=sum(r['palettes'] for r in requested_rows),
        selection_metric=METRIC,
        additional_candidates=[r for r in sorted(rows, key=lambda r: r['mean_source_sampling'])
                               if not r['selected'] and r['source_status'] == 'validated' and
                               r['mean_source_sampling'] < 2.1],
        source_status_summary=dict(scanned_packages=len(rows),
            validated_complete_packages=sum(r['source_status'] == 'validated' for r in rows),
            partial_packages=[r['title'] for r in rows if r['source_status'] == 'partial'],
            other_packages=[r['title'] for r in rows if r['source_status'] not in ['validated', 'partial']])))
    make_index(rows, completed)


def make_sheets(src, dst, records, config, jobs):
    """Pack source and finished masters in identical native-coordinate cells for every original cycle."""
    run = read(src / 'run.json')
    folder = dst / 'sheet_masters_2x'
    folder.mkdir(exist_ok=True)
    for job in run['jobs']:
        names = job['frames']
        crop = np.array(job['native_crop'], dtype=float) * 2
        for name in names:
            r = records[name]
            im = Image.open(src / 'aligned_2x' / (name + '.png'))
            box = im.getchannel('A').getbbox()
            if box:
                world = np.array(box) + np.tile(r['canvas_origin_px'], 2)
                crop[:2] = np.minimum(crop[:2], world[:2] - 4)
                crop[2:] = np.maximum(crop[2:], world[2:] + 4)
        crop = np.r_[np.floor(crop[:2]), np.ceil(crop[2:])].astype(int)
        cw, ch = crop[2:] - crop[:2]
        outputs = []
        for origin, suffix in [(src, 'baseline'), (dst, 'video')]:
            sheet = Image.new('RGBA', (int(cw)*job['columns'], int(ch)*job['rows']))
            for index, name in enumerate(names):
                im = Image.open(origin / 'aligned_2x' / (name + '.png')).convert('RGBA')
                local = crop - np.tile(records[name]['canvas_origin_px'], 2)
                cell = im.crop(tuple(local))
                sheet.paste(cell, (index % job['columns'] * int(cw), index // job['columns'] * int(ch)))
            path = folder / (job['id'] + '_' + suffix + '.png')
            sheet.save(path)
            outputs.append(path)
        jobs[job['id']]['final_sheet_crop_native_2x'] = crop.tolist()
        jobs[job['id']]['final_sheet_files'] = [str(p.relative_to(dst)) for p in outputs]
        jobs[job['id']]['final_sheet_size'] = [int(cw)*job['columns'], int(ch)*job['rows']]


def make_index(rows, completed):
    import html
    text = ['<!doctype html><meta charset="utf-8"><title>MM6 Video x3 finishing comparison</title>',
            '<style>body{font:16px system-ui;background:#22262d;color:#eee;margin:30px}a{color:#b8d9ff}'
            'table{border-collapse:collapse}td,th{padding:7px 14px;text-align:left;border-bottom:1px solid #555}</style>',
            '<h1>MM6 outline-packed — AnimeVideo x3 finishing candidates</h1>',
            '<p>Selection: explicitly requested creatures, plus average measured sampling below 1.70× '
            'using only multi-pose composite sheets '
            'with one equal vote per sheet. Single-sprite sheets do not contribute to the average. '
            'Every sheet of each selected complete creature is processed. Final masters remain 2× native size. '
            'Source alpha, placement, masks, palette ramps, native timing, mirrors and aliases are preserved.</p>',
            '<p>Prepared comparison assets; source restoration acceptance does not accept this finishing pass. '
            '<a href="compare.html">Open all paired before / after sheets</a> · '
            '<a href="requested.html">Cockatrice, Flying Demon, Dragonfly and Harpy</a>.</p>',
            '<p>Video x3 can strengthen internal dark lines and simplify fine grain. Compare these candidates '
            'at 100% before choosing them. AI-generated source sampling remains the original measured value.</p>',
            '<p>Both composite-only averages are recorded: equal weight per sheet (used for selection) '
            'and weight per native bitmap. For Cactus these are 1.869× and 1.626× respectively: '
            'its main animations average 1.547×, while one unused three-pose composite measures 3.478×.</p>',
            '<table><tr><th>Creature</th><th>Composite mean</th><th>Minimum</th><th>Sheets</th><th>Frames</th><th>Palettes</th><th>Review</th></tr>']
    for r in completed:
        title = html.escape(r['title'])
        text.append(f'<tr><td>{title}</td><td>{r["mean_source_sampling"]:.3f}×</td>'
                    f'<td>{r["minimum_source_sampling"]:.3f}×</td><td>{r["prepared_sheets"]}</td>'
                    f'<td>{r["prepared_frames"]}</td><td>{r["palettes"]}</td><td>'
                    f'<a href="{r["output"]}/review.html">Animation / palette reviewer</a> · '
                    f'<a href="{r["output"]}/sheet_masters_2x/">All paired sheets</a></td></tr>')
    text.append('</table><h2>Next complete candidates above the cutoff</h2><table><tr><th>Creature</th>'
                '<th>Composite mean</th><th>Composite frame-weighted mean</th>'
                '<th>Previous all-bitmap mean</th><th>Composite sheets</th></tr>')
    for r in sorted(rows, key=lambda r: r['mean_source_sampling']):
        if r['selected'] or r['source_status'] != 'validated' or r['mean_source_sampling'] >= 2.1:
            continue
        text.append(f'<tr><td>{html.escape(r["title"])}</td><td>{r["mean_source_sampling"]:.3f}×</td>'
                    f'<td>{r["mean_composite_frame_sampling"]:.3f}×</td>'
                    f'<td>{r["mean_all_bitmap_source_sampling"]:.3f}×</td><td>{r["composite_sheets"]}</td></tr>')
    text.append('</table><h2>Full source inventory</h2><table><tr><th>Creature</th><th>Composite mean</th>'
                '<th>Composite frame-weighted mean</th>'
                '<th>Previous all-bitmap mean</th><th>Composite sheets / frames</th>'
                '<th>Single-sprite sheets / frames excluded</th><th>Source status</th></tr>')
    for r in sorted(rows, key=lambda r: r['mean_source_sampling']):
        text.append(f'<tr><td>{html.escape(r["title"])}</td><td>{r["mean_source_sampling"]:.3f}×</td>'
                    f'<td>{r["mean_composite_frame_sampling"]:.3f}×</td>'
                    f'<td>{r["mean_all_bitmap_source_sampling"]:.3f}×</td>'
                    f'<td>{r["composite_sheets"]} / {r["composite_frames"]}</td>'
                    f'<td>{r["single_sprite_sheets"]} / {r["single_sprite_frames"]}</td>'
                    f'<td>{html.escape(r["source_status"])}</td></tr>')
    text.append('</table><p><a href="inventory.json">Measured inventory</a> · <a href="result.json">Output summary</a></p>')
    (HERE / 'index.html').write_text('\n'.join(text))


def review_assets():
    result = read(HERE / 'result.json')
    pairs = []
    model_paths = [CREATURES.parents[1] / 'tools/upscaling/models' / ('realesr-animevideov3-x3.' + ext)
                   for ext in ['param', 'bin']]
    model_metadata = [dict(path=str(p.relative_to(REPO)), sha256=digest(p)) for p in model_paths]
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    for row in result['prepared']:
        dst = HERE / row['output']
        src = REPO / row['source']
        metadata = read(dst / 'upscale.json')
        metadata['model_files'] = model_metadata
        metadata['backend'] = 'realesrgan-ncnn-vulkan; NVIDIA GeForce RTX 3060 Ti; tile 256; no TTA'
        metadata['source_manifest_sha256'] = digest(src / 'manifest.json')
        metadata['source_acceptance_sha256'] = digest(src / 'acceptance.json')
        assert (src / 'acceptance.json').read_bytes() == (dst / 'provenance/source_acceptance.json').read_bytes()
        metadata['manifest_sha256'] = digest(dst / 'manifest.json')
        metadata['atlas_sha256'] = {str(p.relative_to(dst)): digest(p)
                                    for folder in ['atlas', 'previews'] for p in sorted((dst / folder).glob('*.png'))}
        for job in metadata['jobs']:
            assert digest(Path(job['input'])) == job['input_sha256']
            assert digest(Path(job['output'])) == job['output_sha256']
            before, after = [dst / name for name in job['final_sheet_files']]
            assert Image.open(before).getchannel('A').tobytes() == Image.open(after).getchannel('A').tobytes()
            im = Image.open(after).convert('RGBA')
            im = im.convert('RGBa').resize((round(im.width/2), round(im.height/2)), Image.Resampling.LANCZOS).convert('RGBA')
            contact = Image.new('RGB', im.size, '#454851')
            contact.paste(im, mask=im.getchannel('A'))
            contact.save(dst / 'review' / (job['job'] + '_video_native_size.png'))
            pairs.append(dict(family=row['family'], title=row['title'] + ' / ' + job['job'],
                              baseline=str(before.relative_to(HERE)), video=str(after.relative_to(HERE))))
        run = read(src / 'run.json')
        selected = [next(j for j in run['jobs'] if j['action'] == action)['frames'][0]
                    for action in ['walk', 'attack']]
        board = Image.new('RGB', (680, 738), '#292c33')
        draw = ImageDraw.Draw(board)
        for index, name in enumerate(selected):
            before = Image.open(src / 'aligned_2x' / (name + '.png')).convert('RGBA')
            after = Image.open(dst / 'aligned_2x' / (name + '.png')).convert('RGBA')
            x0, y0, x1, y1 = before.getchannel('A').getbbox()
            x, y = (x0+x1)//2, (y0+y1)//2
            box = (x-160, y-160, x+160, y+160)
            top = index*369
            for col, (label, image) in enumerate([('Source restoration', before), ('Video x3 → 2×', after)]):
                draw.text((col*340+10, top+8), label, font=font, fill='white')
                patch = image.crop(box)
                bg = Image.new('RGB', (320, 320), '#656970')
                bg.paste(patch, mask=patch.getchannel('A'))
                board.paste(bg, (col*340+10, top+37))
        board.save(dst / 'review/detail_comparison_100pct.png')
        metadata['detail_contact'] = 'review/detail_comparison_100pct.png'
        save(dst / 'upscale.json', metadata)
        validation = read(dst / 'validation.json')
        validation.update(accepted_alpha_exact=True, accepted_material_masks_exact=True,
                          source_frame_metadata_exact=True, source_page_layout_exact=True,
                          native_timing_and_mirrors_exact=True, complete_selected_sheet_coverage=True,
                          visual_review='Prepared before/after sheets, native-size pose contacts, 100% detail contacts '
                          'and shared animation/palette reviewer. Finishing-pass acceptance remains pending.')
        manifest = read(dst / 'manifest.json')
        validation['shipping_bytes'] = (dst / 'manifest.json').stat().st_size + sum(
            (dst / page[key]).stat().st_size for page in manifest['pages'] for key in ['base', 'mask'])
        save(dst / 'validation.json', validation)
        print('REVIEW READY', row['title'], flush=True)
    make_index(read(HERE / 'inventory.json')['families'], result['prepared'])
    template = '''<!doctype html><meta charset="utf-8"><title>MM6 before / after Video x3</title>
<style>*{box-sizing:border-box}body{margin:0;background:#22262d;color:#eee;font:15px system-ui}
header{padding:14px}h1{font-size:18px;margin:0 0 8px}button,select{font:inherit;color:white;background:#39414d;border:1px solid #89909a;padding:6px;border-radius:4px}
button.active{background:#527491}a{color:#badbff}#viewport{height:calc(100vh - 120px);overflow:auto;padding:12px;background-color:#666;background-image:conic-gradient(#777 25%,#666 0 50%,#777 0 75%,#666 0);background-size:24px 24px}
#viewport.dark{background:#17191e}#viewport.light{background:#ececec}img{display:block;max-width:none}#viewport.fit img{max-width:100%;max-height:100%;width:auto;height:auto;margin:auto}</style>
<header><h1>Complete MM6 sheets · source restoration / AnimeVideo x3 → physical 2×</h1>
<select id="sheetlist" aria-label="Creature and sheet"></select> <button id="before" class="active">B · Before</button> <button id="after">V · Video x3</button>
<button id="zoom">Show 100%</button> <select id="bg" aria-label="Background"><option value="">Checker</option><option value="dark">Dark</option><option value="light">Light</option></select> <a href="index.html">Overview and palette reviewers</a></header>
<div id="viewport" class="fit"><img id="picture" alt="Complete native animation sheet"></div>
<script>const pairs=__PAIRS__;const list=document.querySelector('#sheetlist'),image=document.querySelector('#picture'),viewport=document.querySelector('#viewport');let mode='baseline';
pairs.forEach((pair,index)=>{const option=document.createElement('option');option.textContent=pair.title;option.value=index;list.append(option)});
function display(){const x=viewport.scrollLeft,y=viewport.scrollTop;image.onload=()=>{viewport.scrollLeft=x;viewport.scrollTop=y};image.src=pairs[Number(list.value)][mode];document.querySelector('#before').classList.toggle('active',mode==='baseline');document.querySelector('#after').classList.toggle('active',mode==='video')}
list.onchange=()=>{viewport.scrollLeft=0;viewport.scrollTop=0;display()};document.querySelector('#before').onclick=()=>{mode='baseline';display()};document.querySelector('#after').onclick=()=>{mode='video';display()};
document.querySelector('#zoom').onclick=function(){viewport.classList.toggle('fit');this.textContent=viewport.classList.contains('fit')?'Show 100%':'Fit sheet'};
document.querySelector('#bg').onchange=function(){viewport.classList.remove('dark','light');if(this.value)viewport.classList.add(this.value)};
document.addEventListener('keydown',event=>{if(event.target.tagName==='SELECT')return;if(event.key.toLowerCase()==='b')document.querySelector('#before').click();if(event.key.toLowerCase()==='v')document.querySelector('#after').click()});display();</script>'''
    (HERE / 'compare.html').write_text(template.replace('__PAIRS__', json.dumps(pairs)))
    requested = result.get('requested_families', [])
    if requested:
        focused = [pair for family in requested for pair in pairs if pair['family'] == family]
        (HERE / 'requested.html').write_text(template.replace('__PAIRS__', json.dumps(focused)))
    link = CACHE / 'review'
    if not link.exists():
        link.symlink_to(HERE, target_is_directory=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['inventory', 'prepare', 'finish', 'review'])
    parser.add_argument('--cap-at-2', action='store_true')
    args = parser.parse_args()
    if args.action == 'inventory':
        rows = inventory(args.cap_at_2)
        print('Families', len(rows), 'complete', sum(r['source_status'] == 'validated' for r in rows),
              'selected', [r['title'] for r in rows if r['selected']])
    elif args.action == 'prepare':
        prepare(args.cap_at_2)
    elif args.action == 'finish':
        finish()
    else:
        review_assets()
