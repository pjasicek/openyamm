"""Build the requested native evidence, readable guides and self-contained handoff; no service jobs."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
CREATURE = ROOT.parent
REPO = CREATURE.parents[2]
ARCHIVE = REPO / 'assets_source/creatures/mm6/backups/20261004/native_runtime_retired/engine/sprites'
REQUIRED = ['phase', 'driver', 'right_arm', 'right_hand', 'left_arm', 'left_hand',
            'body', 'support', 'head', 'secondary', 'seeds', 'checks', 'points_xy']


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)


def source_sheet(clip):
    """Overlay explicitly approximate joint seeds on unchanged native actor canvases."""
    count = len(clip['anchors'])
    sheet = Image.new('RGB', (3 * 710, ((count + 2) // 3) * 666), '#343839')
    draw = ImageDraw.Draw(sheet)
    chains = [(1, 2, 3, 4), (1, 5, 6, 7), (1, 8, 9, 10), (8, 11, 12), (0, 1)]
    colors = ['#ffb74d', '#69d5ff', '#ffb74d', '#69d5ff', '#f7e97c']
    for i, anchor in enumerate(clip['anchors']):
        x, y = (i % 3) * 710, (i // 3) * 666
        original = Image.open(ROOT / anchor['source_images'][0]).convert('RGBA')
        bg = Image.new('RGBA', original.size, '#343839')
        bg.alpha_composite(original)
        sheet.paste(bg.resize((710, 578), Image.Resampling.NEAREST).convert('RGB'), (x, y + 55))
        draw.text((x + 10, y + 4), f"{anchor['native_names'][0]}   t={anchor['time_ms']} ms", font=font(19), fill='white')
        draw.text((x + 10, y + 29), anchor['phase'], font=font(16), fill='white')
        points = [None if p is None else (x + p[0] * 2, y + 55 + p[1] * 2)
                  for p in anchor['points_xy']]
        for chain, color in zip(chains, colors):
            for a, b in zip(chain, chain[1:]):
                if points[a] is not None and points[b] is not None:
                    draw.line([points[a], points[b]], fill=color, width=3)
        for point in points[:-1]:
            if point is not None:
                px, py = point
                draw.ellipse((px - 4, py - 4, px + 4, py + 4), outline='#fefefe', width=2)
        if points[4] is not None and points[13] is not None:
            draw.line([points[4], points[13]], fill='#ea9ff6', width=2)
        draw.text((x + 10, y + 640), 'Orange=R, blue=L, violet=sword; manual fitting seeds', font=font(16), fill='white')
    sheet.save(ROOT / 'guides' / f"{clip['name'].lower()}_landmarks.png")


def build():
    native = read(CREATURE / 'source_manifest.json')
    notes = read(ROOT / 'motion_notes.json')
    anatomy = read(ROOT / 'anatomy_targets.json')
    (ROOT / 'source/frames').mkdir(parents=True, exist_ok=True)
    inventory = {'schema_version': 1, 'identity': anatomy['identity'], 'native_canvas': [355, 289],
                 'raw_unit_ms': 62.5, 'transparent_index': 0, 'palette_id': 745, 'frame_scale': 0.649994,
                 'anchor': 'Bottom anchored, no Center; preserve shared logical canvas and standing scale.',
                 'descriptor_rows': 'source/monster_descriptors_rows.tsv',
                 'descriptor_aliases': {'AttackMelee': 'Attack', 'AttackRanged': 'Attack', 'GotHit': 'Hit',
                                        'Dying': 'Death', 'Dead': 'Corpse', 'Bored': 'Fidget'},
                 'native_manifest_sha256': digest(CREATURE / 'source_manifest.json'),
                 'images': [], 'clips': native['clips'], 'excluded': ['goblet.bmp']}
    hashes = defaultdict(list)
    for record in native['images']:
        bmp = ARCHIVE / record['name']
        assert digest(bmp) == record['sha256'], f'Changed original: {bmp}'
        with Image.open(bmp) as src:
            assert src.mode == 'P' and src.size == (355, 289)
            rgba = src.convert('RGBA')
            indices = Image.frombytes('L', src.size, src.tobytes())
            rgba.putalpha(indices.point(lambda index: 0 if index == 0 else 255))
        png = CREATURE / 'source_audit/frames' / (bmp.stem + '.png')
        assert Image.open(png).convert('RGBA').tobytes() == rgba.tobytes(), f'Source decode differs: {png}'
        target = ROOT / 'source/frames' / png.name
        shutil.copy2(png, target)
        inventory['images'].append({**record, 'original_path': str(bmp.relative_to(REPO)),
                                    'png': str(target.relative_to(ROOT)), 'png_sha256': digest(target)})
        hashes[record['sha256']].append(record['name'])
    inventory['duplicate_originals'] = [names for names in hashes.values() if len(names) > 1]
    inventory['original_file_count'] = len(inventory['images'])
    inventory['distinct_original_hashes'] = len(hashes)
    shutil.copy2(CREATURE / 'source_manifest.json', ROOT / 'source/native_manifest.json')
    shutil.copy2(CREATURE / 'meshy_restart_20260923/source/monster_descriptors_rows.tsv',
                 ROOT / 'source/monster_descriptors_rows.tsv')
    for name in ['standing', 'walk', 'attack', 'hit', 'death', 'corpse', 'fidget']:
        shutil.copy2(CREATURE / 'source_audit' / (name + '_native.png'), ROOT / 'source' / (name + '_native.png'))
    write('source_inventory.json', inventory)

    source_clips = {clip['name']: clip for clip in native['clips']}
    covered = set()
    for clip in notes['clips']:
        source = source_clips[clip['name']]
        assert len(clip['anchors']) == len(source['frames'])
        clip['group'] = source['group']
        clip['native_duration_ms'] = sum(frame['duration_ms'] for frame in source['frames'])
        clip['runtime_hold_indefinite'] = clip['mode'] == 'hold'
        clip['genuine_views'] = ['front', 'front-right', 'right', 'back-right', 'back'] if clip['name'] in ['Standing', 'Walk'] else ['front-only Image1']
        clip['mirroring'] = 'views 5/6/7 mirror 3/2/1' if clip['name'] in ['Standing', 'Walk'] else 'single image reused for all directions'
        time_ms = 0
        for anchor, frame in zip(clip['anchors'], source['frames']):
            assert all(key in anchor for key in REQUIRED), (clip['name'], anchor['phase'])
            assert len(anchor['points_xy']) == len(notes['coordinate_contract']['points_order'])
            anchor['time_ms'] = time_ms
            anchor['native_hold_ms'] = frame['duration_ms']
            anchor['native_names'] = frame['paths']
            anchor['source_images'] = ['source/frames/' + Path(name).stem + '.png' for name in frame['paths']]
            anchor['point_confidence'] = '2D manual seeds; depth/hidden joint centers inferred; null=unknown'
            anchor['multiview_check'] = 'Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.' if len(frame['paths']) == 5 else 'No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.'
            time_ms += frame['duration_ms']
            covered.update(frame['paths'])
        source_sheet(clip)
    assert covered == {record['name'] for record in native['images']}
    assert len(covered) == 59 and sum(len(clip['anchors']) for clip in notes['clips']) == 31
    write('motion_spec.json', notes)

    lines = ['# MM6 Goblin A: native motion study', '', notes['status'], '',
             'This is a 3D authoring and review contract, not a recovered original skeleton. '
             'Read the unannotated source beside the approximate landmark overlays. '
             'All native timestamps come from descriptors; smooth subkeys, depth and numerical angle ranges are extrapolations.', '',
             '## Coordinate, timing and confidence contracts', '']
    for key, value in notes['coordinate_contract'].items():
        lines += [f'**{key.replace("_", " ")}**: {value}', '']
    lines += ['## Rules shared by every action', ''] + ['- ' + value for value in notes['shared_constraints']] + ['']
    lines += ['## Native action inventory', '', '| Action | Anchors | Native duration | Views | Playback |', '| --- | ---: | ---: | --- | --- |']
    for clip in notes['clips']:
        lines.append(f"| {clip['name']} | {len(clip['anchors'])} | {clip['native_duration_ms']} ms | {len(clip['anchors'][0]['source_images'])} genuine | {clip['mode']} |")
    lines += ['', 'AttackMelee and AttackRanged alias Attack. Standing and Corpse durations are metadata for one held frame; their visible hold is indefinite. '
              'Native running is absent. Death d and Corpse have identical original bytes; Death e is a small settling variation.', '']
    for clip in notes['clips']:
        name = clip['name'].lower()
        lines += [f"## {clip['name']}", '', clip['driver'], '', '**Continuous motion**: ' + clip['curve_plan'], '',
                  '**Confidence**: ' + clip['confidence'], '',
                  f"[Unannotated native sheet](source/{name}_native.png) · [Approximate landmark overlay](guides/{name}_landmarks.png)", '']
        for i, anchor in enumerate(clip['anchors']):
            lines += [f"### {chr(97+i)} — {anchor['time_ms']} ms: {anchor['phase']}", '',
                      '**Native evidence**: ' + ', '.join(anchor['native_names']) + f"; native interval {anchor['native_hold_ms']} ms.", '']
            for key in REQUIRED:
                if key in ['phase', 'seeds', 'checks', 'points_xy']:
                    continue
                lines += [f'**{key.replace("_", " ").title()}**: {anchor[key]}', '']
            lines += ['**Anatomical fitting ranges, not local Euler keys**: ' + '; '.join(f'{k}={v}' for k, v in anchor['seeds'].items()) + '.', '',
                      '**Verify**:', ''] + ['- ' + value for value in anchor['checks']] + ['', anchor['multiview_check'], '']
    lines += ['## Review on the returned rig', '',
              'First inspect walking and the sword-grip/high-cross/face-guard/deep-knee/prone stress poses. '
              'Render each native anchor plus intermediate frames through the fastest attack and collapse intervals. '
              'Use one locked camera, scale and ground, compare head/shoulder/wrist/pelvis/sole heights, '
              'hand plane/visible thumb, blade plane, support contacts and the unannotated silhouette. '
              'Approximate 2D seeds suggest where to look, not an automatic pass/fail threshold. '
              'Check front plus genuine native walk views; review inferred action sides/back for plausible chains and clearance. '
              'Repair geometry, bone axis, orientation, contact or weights according to the demonstrated cause; '
              'record annotated before/after images and rerun affected clips. Do not author the rest over a known pilot defect.', '']
    (ROOT / 'ANIMATION_STUDY.md').write_text('\n'.join(lines))

    lines = ['# MM6 Goblin A: anatomy and model-ingest guide', '', anatomy['measurement_contract'], '',
             '**Submission**: ' + anatomy['body_submission'], '',
             '[Selected views](guides/selected_views_review.png) · [Native detail crops](guides/native_details.png) · '
             '[Native standing views](source/standing_native.png) · [Annotated native anatomy](guides/anatomy_native.png)', '']
    for region in anatomy['regions']:
        lines += ['## ' + region['id'].replace('_', ' ').title(), '',
                  f"**Priority**: {region['priority']}. **Confidence**: {region['confidence']}.", '',
                  '**Observed**: ' + region['observed'], '', '**Inferred or selected**: ' + region['inferred_or_selected'], '',
                  '**Model checks**:', ''] + ['- ' + value for value in region['model_checks']] + ['', '**Deformation**: ' + region['deformation'], '']
        if 'projected_ratio_ranges_h' in region:
            lines += ['| Projected measurement / standing H | Range |', '| --- | --- |']
            lines += [f'| {key.replace("_", " ")} | {value[0]}–{value[1]} |' for key, value in region['projected_ratio_ranges_h'].items()] + ['']
    lines += ['## Material families', ''] + [f'**{key.title()}**: {value}\n' for key, value in anatomy['materials'].items()]
    lines += ['## Review order and evidence limits', ''] + ['- ' + value for value in anatomy['review_rules']] + ['']
    (ROOT / 'ANATOMY_GUIDE.md').write_text('\n'.join(lines))

    anatomy_sheet = Image.new('RGB', (2130, 790), '#343839')
    draw = ImageDraw.Draw(anatomy_sheet)
    boxes = [
        ('gobsta0', [('head / ears', (166,33,221,93)), ('gorget / shoulders', (134,83,249,128)),
                     ('hands: 3 fingers + thumb', (116,151,254,211)), ('belt / short strips', (153,149,222,201)),
                     ('3 toes / exposed heels', (153,261,229,289))]),
        ('gobsta2', [('skull wedge / profile', (170,33,230,108)), ('exposed joint gaps', (171,100,225,171)),
                     ('long curved separate sword', (203,154,328,179)), ('long flat foot', (172,265,249,289))]),
        ('gobsta4', [('two separate rear plates', (162,90,229,124)), ('exposed back', (158,126,235,165)),
                     ('right pouch: image-right', (216,162,242,193))])]
    for i, (name, regions) in enumerate(boxes):
        x = i * 710
        im = Image.open(ROOT / 'source/frames' / (name + '.png')).convert('RGBA')
        bg = Image.new('RGBA', im.size, '#343839'); bg.alpha_composite(im)
        anatomy_sheet.paste(bg.resize((710,578), Image.Resampling.NEAREST).convert('RGB'), (x,40))
        draw.text((x+10,8), name + ': native silhouette targets', font=font(20), fill='white')
        for j, (label, box) in enumerate(regions):
            color = ['#ffd36a','#69d5ff','#eaa0f5','#9ce8a3','#ffa380'][j]
            draw.rectangle((x+box[0]*2,40+box[1]*2,x+box[2]*2,40+box[3]*2),outline=color,width=3)
            draw.text((x+10,633+j*28), label, font=font(17), fill=color)
    anatomy_sheet.save(ROOT / 'guides/anatomy_native.png')

    runs = read(ROOT / 'generation_runs.json')
    output_map = {run['output']: ROOT/'raw'/f"{run['id']}.png" for run in runs}
    for run in runs:
        run['raw_file'] = str(output_map[run['output']].relative_to(ROOT))
        run['raw_sha256'] = digest(output_map[run['output']])
        run['actual_sampling_size'] = list(Image.open(output_map[run['output']]).size)
        run['export_resize_or_padding'] = 'None. Selected files are byte-identical copies of actual imagegen returns.'
        run['input_records'] = []
        for supplied in run['inputs']:
            if supplied in output_map:
                path = output_map[supplied]
            elif supplied == '/tmp/goblin-native-details.png':
                path = ROOT/'guides/native_details.png'
            elif supplied.startswith('submission/'):
                path = ROOT/supplied
            else:
                path = CREATURE/supplied
            original_path = path
            if supplied.startswith('meshy_reference_v2/'):
                path = ROOT / 'source/generation_inputs' / ('legacy_' + Path(supplied).name)
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original_path, path)
            elif supplied == 'source_audit/standing_native.png':
                path = ROOT / 'source/standing_native.png'
            run['input_records'].append({'supplied': run.get('original_supplied_inputs', run['inputs'])[len(run['input_records'])],
                                         'original_input_path': str(original_path.relative_to(REPO)),
                                         'retained_path': str(path.relative_to(ROOT)), 'sha256': digest(path)})
    write('generation_runs.json', runs)
    selected = []
    for path in sorted((ROOT/'submission').glob('*.png')):
        im = Image.open(path)
        assert im.mode == 'RGBA' and im.size == (1024,1536)
        box = im.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
        assert box and box[0] > 4 and box[1] > 4 and box[2] < im.width-4 and box[3] < im.height-4, (path,box)
        assert any(run['selected'] and run['raw_sha256'] == digest(path) for run in runs)
        selected.append({'path': str(path.relative_to(ROOT)), 'sha256': digest(path), 'size': list(im.size),
                         'alpha_bounds_threshold_128': box, 'role': 'smart_topology_primary' if path.name.startswith('00') else 'supporting_anatomy_view'})
    assert len(selected) == 5
    assert sum(run['selected'] for run in runs) == len(selected)
    review = Image.new('RGB', (2560, 820), '#eeeeea')
    draw = ImageDraw.Draw(review)
    for i, item in enumerate(selected):
        im = Image.open(ROOT/item['path']).convert('RGBA')
        bg = Image.new('RGBA', im.size, '#eeeeea'); bg.alpha_composite(im)
        review.paste(bg.resize((512,768)).convert('RGB'), (i*512,40))
        draw.text((i*512+10,10), Path(item['path']).stem, font=font(15), fill='black')
    review.save(ROOT/'guides/selected_views_review.png')
    verification = {'native_originals_verified': 59, 'native_png_decode_verified': 59,
                    'native_actions': 7, 'temporal_anchors': 31, 'source_frames_covered': 59,
                    'selected_submission_images': selected, 'imagegen_returns': len(runs),
                    'reference_fixup_passes': 2, 'native_death_d_equals_corpse': digest(ARCHIVE/'gobdyd0.bmp') == digest(ARCHIVE/'gobdyf0.bmp'),
                    'scope': 'Stage 1 references and study only; no Meshy job, new model, rig, UV or texture generated.'}
    assert verification['native_death_d_equals_corpse']
    write('verification.json', verification)
    for key in ['motion_spec.json','source_inventory.json','ANATOMY_GUIDE.md','ANIMATION_STUDY.md','verification.json']:
        assert (ROOT/key).stat().st_size > 0
    print(json.dumps({key: value for key,value in verification.items() if key != 'selected_submission_images'}, indent=2))


def package():
    target = ROOT/'mm6_goblin_stage1_meshy_and_study.zip'
    files = sorted(path for path in ROOT.rglob('*') if path.is_file() and path != target and '__pycache__' not in path.parts)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path,'mm6_goblin_stage1/'+str(path.relative_to(ROOT)))
    with zipfile.ZipFile(target) as bundle:
        assert bundle.testzip() is None and len(bundle.namelist()) == len(files)
    print(f'Package: {target.name}, {len(files)} files, {target.stat().st_size} bytes')


if __name__ == '__main__':
    build()
    package()
