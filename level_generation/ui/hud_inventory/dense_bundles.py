"""Prepare <=64-cell MM6–8 restoration sheets and an auditable return contract. No generation."""
import argparse
import collections
import fcntl
import hashlib
import json
import math
import shutil
import zipfile
from pathlib import Path

from PIL import Image
from freeze_targets import rendered

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT_PIXELS = 1_572_000
MIN_PLANNED_SAMPLING = 2.15
MAX_CELLS = 64
TREATMENTS = {'player_portrait_frames', 'npc_portrait_family', 'inventory_items',
              'legacy_ui_art', 'ui_state_set', 'ui_frame_or_panel'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def grid_for(count, width, height):
    """Pixel budget includes padding, empty slots and aspect-ratio limitations."""
    assert 0 < count <= MAX_CELLS
    choices = []
    for columns in range(1, count+1):
        rows = math.ceil(count/columns)
        w, h = columns*(width+4), rows*(height+4)
        # Add only exterior empty margin when a long/thin icon needs a supported sheet shape.
        if w/h < .5:
            w = math.ceil(h*.5)
        elif w/h > 2:
            h = math.ceil(w/2)
        aspect = w/h
        scale = math.sqrt(OUTPUT_PIXELS/(w*h))
        if .5 <= aspect <= 2 and scale >= MIN_PLANNED_SAMPLING:
            cost = (columns*rows-count)*.25 + abs(math.log(aspect))
            choices.append((cost, columns, rows, w, h, scale))
    if not choices:
        return None
    _, columns, rows, w, h, scale = min(choices)
    return dict(columns=columns, rows=rows, native_sheet_size=[w, h],
                reference_size=[2*w, 2*h], predicted_sampling=scale,
                minimum_output=[2*w, 2*h], cell_size_native=[width+4, height+4])


def experiment_ids():
    result = set()
    for path in (HERE/'experiments').rglob('manifest.json'):
        data = read(path)
        if data.get('status', '').startswith('generated_') or data.get('raw_source') or (path.parent/'raw.png').exists():
            for cell in data.get('cells', data.get('rows', [])):
                if isinstance(cell, dict):
                    value = cell.get('id') or cell.get('cell') or cell.get('member', {}).get('id')
                    if value:
                        result.add(value)
    retained = HERE/'experiments/dense_portraits_20260916/retained_targets.json'
    if retained.exists():
        result.update(read(retained)['targets'])
    return result


def appearance(target):
    # Same pixels alone are not sufficient when dimensions or compositing differ.
    profiles = tuple(sorted((k, v['rgba_sha256']) for k, v in target['compositing']['fingerprints'].items()))
    return target['treatment'], tuple(target['native_size']), profiles


def collect():
    targets = {t['id']:t for t in read(HERE/'expected_targets.json')['targets']}
    jobs = {j['id']:j for j in read(HERE/'jobs.json')['jobs']}
    members = {m['id']:(j, m) for j in jobs.values() for m in j['members']}
    state_path = HERE/'checkpoint/state.json'
    state_hash = sha(state_path)
    state = read(state_path)
    retained = set(state['cells']) | experiment_ids()
    for attempt in state['attempts']:
        payload = read(Path(attempt['payload']))
        retained.update(payload.get('selected_cells', [m['id'] for m in jobs[attempt['job']]['members']]))
    rejected = {f'engine--icons--maleh{i:02d}.bmp' for i in range(1, 7)}
    donors = {}
    for cell in sorted(retained):
        if cell in targets:
            donors.setdefault(appearance(targets[cell]), cell)
    audit, selected, aliases = [], [], []
    canonical = {}
    for tid, t in sorted(targets.items()):
        row = dict(id=tid, treatment=t['treatment'], native_size=t['native_size'], namespace=t['namespace'])
        reason = None
        if t['namespace'] not in ('engine', 'worlds/mm6', 'worlds/mm7', 'worlds/mm8'):
            reason = 'outside_MM6_MM7_MM8'
        elif t['treatment'] not in TREATMENTS:
            reason = 'separate_large_animation_equipment_spell_or_map_workflow'
        elif tid in retained:
            reason = 'retained_attempt_or_review_state'
        elif tid in rejected:
            reason = 'prior_generation_rejection_retained_for_separate_review'
        elif max(t['native_size']) > 256:
            reason = 'larger_than_small_art_scope_256_native_edge'
        elif tid not in members:
            reason = 'not_one_full_canvas_generation_cell'
        else:
            j, member = members[tid]
            allowed = {'accepted_treatment_pilot'}
            if t['treatment'] == 'player_portrait_frames':
                allowed.add('accepted_seed_job')
            if j['id'] in state.get('claims', {}):
                reason = 'active_claim'
            elif any(d['kind'] not in allowed for d in j['dependencies']):
                reason = 'requires_separate_generated_reference_dependency'
            elif member['source_rect'] != [0, 0, *t['native_size']] or member['method'] != 'imagegen_sheet':
                reason = 'specialized_crop_or_deterministic_job'
            elif not grid_for(1, *t['native_size']):
                reason = 'unsupported_shape_or_pixel_budget'
            else:
                source = ROOT/member['source_path']
                assert sha(source) == member['source_sha256'], f'Source drift: {source}'
                key = appearance(t)
                donor = donors.get(key) or canonical.get(key)
                if donor:
                    row.update(disposition='reuse_candidate', donor=donor,
                               donor_kind='retained_art_needs_review' if key in donors else 'new_sheet_target',
                               proof='exact native dimensions and all rendered-profile fingerprints',
                               source_sha256=member['source_sha256'])
                    aliases.append(dict(**row, member=member, target=t))
                else:
                    canonical[key] = tid
                    row['disposition'] = 'generate'
                    selected.append(dict(id=tid, job=j, member=member, target=t))
        if reason:
            row.update(disposition='excluded', reason=reason)
        audit.append(row)
    return targets, jobs, state, state_hash, selected, aliases, audit


def art_mode(target):
    comp = target['compositing']
    if comp['preserve_indexed_keys']:
        return 'indexed_keys'
    if comp['cleanup'] == 'opaque_canvas':
        return 'opaque'
    return 'cutout'


def grouping(entry):
    t, j = entry['target'], entry['job']
    kind = t['treatment']
    if kind == 'player_portrait_frames':
        family = (t.get('frame') or {}).get('family', j['id'])
        return 'pc', t['namespace'], art_mode(t), family
    if kind == 'npc_portrait_family':
        return 'npc_house', t['namespace'], art_mode(t), ''
    if kind in ('ui_state_set', 'ui_frame_or_panel'):
        return 'small_ui', t['namespace'], art_mode(t), j['id']
    # Keep the original preparation family for legacy states/unknown sequences.
    if kind == 'legacy_ui_art':
        return 'legacy_small', t['namespace'], art_mode(t), json.dumps(j['family'])
    w, h = t['native_size']
    return 'inventory', t['namespace'], art_mode(t), f'{math.ceil(w/32)}x{math.ceil(h/32)}'


def pack(selected):
    groups = collections.defaultdict(list)
    for item in selected:
        groups[grouping(item)].append(item)
    sheets = []
    for key, items in sorted(groups.items()):
        items.sort(key=lambda x: ((x['target'].get('frame') or {}).get('ordinal', 0), x['id']))
        while items:
            count = min(MAX_CELLS, len(items))
            while count:
                batch = items[:count]
                g = grid_for(count, max(x['target']['native_size'][0] for x in batch),
                             max(x['target']['native_size'][1] for x in batch))
                if g:
                    break
                count -= 1
            assert count, key
            sheets.append(dict(group=list(key), grid=g, entries=batch))
            items = items[count:]
    # Combine complete small state/family units, never split them just to fill a sheet.
    result = [s for s in sheets if s['group'][0] == 'pc']
    cohorts = collections.defaultdict(list)
    for sheet in sheets:
        if sheet['group'][0] == 'pc':
            continue
        width = max(e['target']['native_size'][0] for e in sheet['entries'])
        height = max(e['target']['native_size'][1] for e in sheet['entries'])
        cohorts[(*sheet['group'][:3], math.ceil(width/64), math.ceil(height/64))].append(sheet)
    for key, units in sorted(cohorts.items()):
        current = []
        for unit in units:
            combined = current + unit['entries']
            grid = None
            if len(combined) <= MAX_CELLS:
                grid = grid_for(len(combined), max(e['target']['native_size'][0] for e in combined),
                                max(e['target']['native_size'][1] for e in combined))
            if current and not grid:
                g = grid_for(len(current), max(e['target']['native_size'][0] for e in current),
                             max(e['target']['native_size'][1] for e in current))
                result.append(dict(group=[*key[:3], 'compatible_complete_groups'], grid=g, entries=current))
                current = unit['entries']
            else:
                current = combined
        if current:
            g = grid_for(len(current), max(e['target']['native_size'][0] for e in current),
                         max(e['target']['native_size'][1] for e in current))
            result.append(dict(group=[*key[:3], 'compatible_complete_groups'], grid=g, entries=current))
    return result


MASTER = '''# Restore the prepared MM6–8 sheets

Read manifest.json. For each sheet, OPEN its reference.png and each listed identity reference, then submit
the exact prompt.txt with those images in the listed order to the built-in imagegen tool. One sheet is one
imagegen call. Native identity references are supplied originals, not accepted restoration or extra targets.
This package authorizes an independent native-reference first pass; do not wait for treatment-pilot approval.
Page/animation dependencies that cannot use this policy were excluded during preparation.

Save the original downloaded master UNCHANGED as outputs/raw/SNNN.png (or its real extension). Immediately
save the exact submitted prompt as outputs/prompts/SNNN.txt and update outputs/progress.json from the template.
Record returned dimensions, filename, model/tool and hashes when available. Return all completed raw results
if interrupted. Do not retry poor cells or redo completed sheets during this first pass. Report rejection/errors
honestly. Never replace generation with enlargement, filtering or programmatic drawing.

Preserve all grid slots, native full canvases, identities, expressions, opaque backgrounds and key colors.
Actual generated detail must be at least twice the native dimensions, not merely a larger export file.
Check each returned cell; nominal whole-sheet dimensions do not prove adequate per-cell sampling or fidelity.
Do not crop, fit, remove backgrounds, recolor or install returned art here. Flag defects for local review.

Return a ZIP containing unchanged manifest.json, outputs/progress.json, outputs/raw/ and outputs/prompts/.
No cloud connection is required. A partial ZIP is useful. Never claim generation or review without actual evidence.
Local catalogue/registration/alpha/identity review and acceptance happen after return. Keep commentary concise.
'''


def native_image(entry):
    t, m = entry['target'], entry['member']
    with Image.open(ROOT/m['source_path']) as source:
        if art_mode(t) == 'indexed_keys':
            return source.convert('RGBA')
        profile = t['compositing']['profiles'][0]
        return rendered(source, profile)


def identity_context(entries, jobs, destination):
    seed_ids = set()
    for item in entries:
        if item['target']['treatment'] == 'player_portrait_frames':
            j = item['job']
            seed_ids.update([d['job'] for d in j['dependencies'] if d['kind'] == 'accepted_seed_job'] or [j['id']])
    refs = []
    for seed in sorted(seed_ids):
        folder = destination/'identity'/seed
        reference = folder/'reference.png'
        if not reference.exists():
            folder.mkdir(parents=True)
            members = jobs[seed]['members']
            cellw = max(m['source_rect'][2] for m in members)*4+16
            cellh = max(m['source_rect'][3] for m in members)*4+16
            contact = Image.new('RGB', (cellw*3, cellh*math.ceil(len(members)/3)), '#333333')
            contract = []
            for i, member in enumerate(members):
                src = ROOT/member['source_path']
                assert sha(src) == member['source_sha256']
                shutil.copy2(src, folder/member['id'])
                with Image.open(src) as im:
                    native = rendered(im, 'hud').convert('RGB')
                contact.paste(native.resize((native.width*4, native.height*4), Image.Resampling.NEAREST),
                              ((i%3)*cellw+8, (i//3)*cellh+8))
                contract.append(member)
            contact.save(reference)
            save(folder/'sources.json', contract)
        refs.append(dict(path=str(reference.relative_to(destination)), sha256=sha(reference)))
    return refs


def write_bundle(destination, batch, jobs, state_hash, aliases):
    destination.mkdir(parents=True)
    manifest = dict(schema='openyamm.dense-restoration.v1', bundle_id=destination.name,
                    status='prepared_only', maximum_cells=MAX_CELLS, reference_scale=2,
                    minimum_generated_sampling=2, planned_sampling=MIN_PLANNED_SAMPLING,
                    source_state_sha256=state_hash, jobs_sha256=sha(HERE/'jobs.json'),
                    source_manifest_sha256=sha(HERE/'expected_targets.json'), sheets=[])
    progress = dict(bundle=destination.name, sheets={})
    ids = set()
    for index, sheet in enumerate(batch, 1):
        sid = f'S{index:03d}'
        folder = destination/'sheets'/sid
        folder.mkdir(parents=True)
        g = sheet['grid']
        reference = Image.new('RGBA', g['reference_size'], '#ff00ff')
        layout = dict(sheet_id=sid, group=sheet['group'], **g, cells=[])
        for i, item in enumerate(sheet['entries']):
            m, t = item['member'], item['target']
            native = native_image(item)
            assert list(native.size) == t['native_size']
            sources = destination/'sources'
            sources.mkdir(exist_ok=True)
            original = sources/item['id']
            shutil.copy2(ROOT/m['source_path'], original)
            native_path = sources/(item['id']+'.png')
            native.save(native_path)
            cw, ch = g['cell_size_native']
            x = (i%g['columns'])*cw+(cw-native.width)/2
            y = (i//g['columns'])*ch+(ch-native.height)/2
            rect = [int(x*2), int(y*2), native.width*2, native.height*2]
            reference.alpha_composite(native.resize(tuple(rect[2:]), Image.Resampling.NEAREST), tuple(rect[:2]))
            layout['cells'].append(dict(id=item['id'], slot=i+1, reference_rect=rect, native_size=t['native_size'],
                x2_size=t['x2_size'], native_png=str(native_path.relative_to(destination)),
                native_png_sha256=sha(native_path), original_file=str(original.relative_to(destination)),
                source_sha256=m['source_sha256'], original_job=item['job']['id'],
                job_contract=item['job'], member=m, target=t))
            ids.add(item['id'])
        reference.convert('RGB').save(folder/'reference.png')
        identities = identity_context(sheet['entries'], jobs, destination)
        mode = sheet['group'][2]
        background = {
            'opaque':'Each portrait/image is fully opaque. Keep its complete original background edge to edge; magenta belongs ONLY in gutters.',
            'cutout':'Use flat pure magenta RGB 255,0,255 only outside the native artwork and genuine holes; preserve real pink/purple details and thin features. No shadows, spill or checkerboards.',
            'indexed_keys':'These are indexed/key-aware assets. Preserve the exact flat native key-color regions (including magenta, cyan, black, pink or blue where present), their boundaries and all opaque artwork. Do not replace black or colored interiors arbitrarily. Original palette/consumer metadata is retained for later local reconstruction.'
        }[mode]
        identity_line = ('Additional images are original seed portraits of this same player character, supplied only for identity. Preserve each target expression, gaze, wounds/effects and framing; do not copy a seed expression or output the context grid.' if identities else '')
        labels = '\n'.join(f'{c["slot"]}. {c["id"]}: native {c["native_size"]}, exact final x2 {c["x2_size"]}, input rectangle xywh {c["reference_rect"]}.' for c in layout['cells'])
        prompt = f'''Faithful restoration of an existing Might and Magic game artwork sheet; image 1 is the EDIT TARGET.
Exactly {g['columns']} columns by {g['rows']} rows; {len(sheet['entries'])} occupied cells, ordered left to right then top to bottom. Keep empty slots empty. Preserve every complete native canvas, margins, object count, symbol, expression, angle, silhouette and internal geometry. Do not merge, duplicate, reorder or recenter cells or borrow features from neighbors.
Reconstruct continuous fine painted contours and material/facial detail at final x2 size. Retain original style, subdued color balance and lighting. No pixel-block enlargement, blur-only output, redesign, beautification, new ornament, exaggerated eyes/teeth or invented lettering. Registry portraits may contain doors, houses, objects, elementals or symbols: restore their actual content; never invent a face.
{background}
{identity_line}
No labels, borders, grid lines, checkerboards or extra shadows. Native artwork is shown at 2x for input legibility, not as a rendering style. Preserve the exact {g['reference_size'][0]}:{g['reference_size'][1]} sheet aspect ratio. Produce the largest available raster with these proportions; do not substitute a square. Every returned portrait/object rectangle must contain at least 2 generated pixels per native pixel before later resizing. Nominal minimum whole sheet is {g['minimum_output'][0]}x{g['minimum_output'][1]}, and individual cells must also be checked.
Occupied cells (other slots stay empty):
{labels}
'''
        (folder/'prompt.txt').write_text(prompt)
        save(folder/'layout.json', layout)
        record = dict(id=sid, cells=[e['id'] for e in sheet['entries']],
                      reference=f'sheets/{sid}/reference.png', reference_sha256=sha(folder/'reference.png'),
                      prompt=f'sheets/{sid}/prompt.txt', prompt_sha256=sha(folder/'prompt.txt'),
                      layout=f'sheets/{sid}/layout.json', layout_sha256=sha(folder/'layout.json'),
                      identity_references=identities, group=sheet['group'], **g)
        manifest['sheets'].append(record)
        progress['sheets'][sid] = dict(status='unattempted', raw_path=None, submitted_prompt_path=None,
                                     actual_dimensions=None, original_filename=None, tool=None, raw_sha256=None,
                                     submitted_prompt_sha256=None, notes='')
    manifest['target_count'] = len(ids)
    manifest['sheet_count'] = len(batch)
    manifest['reuse_candidates'] = [a for a in aliases if a['donor'] in ids]
    save(destination/'manifest.json', manifest)
    save(destination/'progress.template.json', progress)
    (destination/'MASTER_PROMPT.md').write_text(MASTER)
    (destination/'README.md').write_text(f'# {destination.name}\n\n{len(ids)} generation targets on {len(batch)} sheets, at most 64 per sheet.\n\nAttach this ZIP and paste MASTER_PROMPT.md. Return raw masters and exact prompts using progress.template.json. Sources, native identity context and reuse candidates are not extra generation targets. No helpers or provider credentials are required.\n')
    return manifest


def reserve(root, manifests, aliases, initial_hash):
    state_path = HERE/'checkpoint/state.json'
    with (HERE/'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        assert sha(state_path) == initial_hash, 'Queue changed during preparation; re-audit before assignment.'
        state = read(state_path)
        before = {k:v for k,v in state.items() if k not in ('external_assignments', 'external_assignment_history')}
        assignment_map = {}
        for manifest in manifests:
            path = root/manifest['bundle_id']/'manifest.json'
            manifest_hash = sha(path)
            for sh in manifest['sheets']:
                for cell in sh['cells']:
                    assignment_map[cell] = dict(bundle=manifest['bundle_id'], manifest=str(path),
                        manifest_sha256=manifest_hash, status='assigned', dense_sheet=sh['id'],
                        batch_set=str(root), generation_policy='native_reference_first_pass_review_local')
        # Aliases wait for their donor's local review/reuse approval, not another generation.
        catalogue_hash = sha(root/'catalogue.json')
        for alias in aliases:
            assignment_map[alias['id']] = dict(bundle=root.name, manifest=str(root/'catalogue.json'),
                manifest_sha256=catalogue_hash, status='assigned',
                work_kind='reuse_candidate_no_generation', donor=alias['donor'], batch_set=str(root))
        history = state.setdefault('external_assignment_history', [])
        previous = []
        for cell, assignment in assignment_map.items():
            old = state['external_assignments'].get(cell)
            if old:
                assert old['status'] == 'assigned', f'Already returned: {cell}'
                receipt = dict(cell=cell, previous=old, replacement=assignment, reason='user_requested_dense64_repack')
                history.append(receipt)
                previous.append(receipt)
            assert cell not in state['cells']
            state['external_assignments'][cell] = assignment
        assert before == {k:v for k,v in state.items() if k not in ('external_assignments', 'external_assignment_history')}
        save(root/'assignment_history.json', previous)
        save(root/'state_before_reservation.json', read(state_path))
        tmp = state_path.with_suffix('.dense64.tmp')
        save(tmp, state)
        tmp.replace(state_path)
        save(root/'reservation.json', dict(before_sha256=initial_hash, after_sha256=sha(state_path),
             assigned=len(assignment_map), reassigned=len(previous),
             note='Only external assignment bookkeeping changed; old input ZIPs/receipts remain intact. Late old returns require explicit reconciliation.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reserve', action='store_true')
    args = parser.parse_args()
    _, jobs, _, state_hash, selected, aliases, audit = collect()
    sheets = pack(selected)
    summary = dict(generation_targets=len(selected), sheets=len(sheets), reuse_candidates=len(aliases),
        treatments=dict(collections.Counter(x['target']['treatment'] for x in selected)),
        cells_per_sheet=dict(sorted(collections.Counter(len(s['entries']) for s in sheets).items())),
        exclusions=dict(collections.Counter(x['reason'] for x in audit if x['disposition']=='excluded')))
    print(json.dumps(summary, indent=2))
    if not args.output:
        return
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    bundles = []
    # Independent packs of <=8 sheets; keep work types separate for easier review/dispatch.
    by_kind = collections.defaultdict(list)
    for sheet in sheets:
        by_kind[sheet['group'][0]].append(sheet)
    for kind, work in sorted(by_kind.items()):
        for offset in range(0, len(work), 8):
            name = f'dense64_{kind}_{offset//8+1:03d}'
            bundles.append(write_bundle(root/name, work[offset:offset+8], jobs, state_hash, aliases))
    catalogue = dict(schema='openyamm.dense-batch-set.v1', source_state_sha256=state_hash,
                     summary=summary, bundles=[dict(bundle_id=m['bundle_id'], target_count=m['target_count'],
                     sheet_count=m['sheet_count'], manifest=f'{m["bundle_id"]}/manifest.json',
                     manifest_sha256=sha(root/m['bundle_id']/'manifest.json')) for m in bundles],
                     reuse_candidates=aliases, scope=audit)
    save(root/'catalogue.json', catalogue)
    save(root/'summary.json', summary)
    links = ['# Dense64 restoration work bundles\n',
        'Prepared only; no image generation. Use ONE individual ZIP per worker/chat. See BATCHING_DENSE64.md for the pixel budget.\n',
        'These supersede overlapping unreturned older assignments. Do not run both old and new bundles. Retain late older results for explicit reconciliation.\n',
        '| Bundle | Generation targets | Sheets | ZIP |\n| --- | ---: | ---: | --- |']
    for m in bundles:
        name = m['bundle_id']
        z = root/(name+'.zip')
        with zipfile.ZipFile(z, 'x', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted((root/name).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(root/name))
        with zipfile.ZipFile(z) as archive:
            assert archive.testzip() is None
        links.append(f'| {name} | {m["target_count"]} | {m["sheet_count"]} | [ZIP]({name}.zip) |')
    (root/'README.md').write_text('\n'.join(links)+'\n')
    if args.reserve:
        reserve(root, bundles, aliases, state_hash)
    print(root)


if __name__ == '__main__':
    main()
