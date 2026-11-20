"""Export portable imagegen handoffs, optionally assigning their cells to external workers."""
import argparse
import ast
import collections
import fcntl
import importlib.util
import json
import math
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw

from finalize_classification import ROOT, digest
from freeze_targets import rendered

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hud_queue', HERE / 'queue.py')
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)

MASTER = """# Restore this Might and Magic artwork bundle

Use the attached ZIP as the complete input package. Read manifest.json and examples/README.md,
then visually OPEN the good/bad comparison images and the current sheet's reference.png before generation.
The requested work is faithful restoration with AI image generation, not UI redesign or pixel enlargement.
There are {count} target images across {sheets} sheets. Examples are not targets.

Use your built-in image-generation/editing tool. A sheet is ONE imagegen request containing multiple items.
Do not use programmatic drawing, upscalers, filters, nearest-neighbor enlargement or blurred originals as
substitutes for imagegen artwork. Python is permitted for ZIP/files, reference grids, cropping, matting,
premultiplied resampling, registration and QA only. If you cannot open the ZIP/references or use imagegen,
report that limitation; never claim generation or visual inspection that did not happen.

For each sheet, in manifest order:
1. Read sheets/SNNN/prompt.txt and layout.json. OPEN reference.png at full resolution. It is the edit target.
   Native sources are provided individually too. The examples show finish/fidelity only; never copy their design
   into another item. Native item names are context, not permission to invent detail hidden by low resolution.
2. Generate one restored sheet using that reference and the exact sheet prompt. Preserve the row-major slots,
   native canvas margins, pose, identity, holes, symbols, component counts and subdued color balance.
   Never complete an occluded item, exaggerate hardware or make everything glossy. Restore continuous painted
   material detail and smooth curves; do not reproduce enlarged squares, mosaics, dot highlights or pixel steps.
   Request an OPAQUE perfectly flat pure magenta #FF00FF background and genuine holes, without checkerboard,
   gradients, ground shadows, magenta bounce or halos. Keep intentional purple/pink foreground colors.
3. Save the actual returned full-resolution master unchanged as outputs/raw/SNNN.png (or retain its real
   extension and record it). Save the exact submitted prompt. Do not overwrite or regenerate a whole sheet
   because one cell is weak. Preserve outputs promptly; a generated display alone is not a returned file.
4. Inspect the COMPLETE raw sheet and EVERY cell. If Python is available, run the included process_sheet.py
   for the saved sheet to obtain exact-x2 RGBA candidates and full-size native/restored/light/dark comparisons.
   This helper proposes cleanup/fitting, NOT acceptance. Check actual grid layout before running it; incorrect
   layout/cell swaps must be flagged, never silently cropped into the wrong IDs. Keep raw masters regardless.
5. Review each final x2 cell, with complete canvas and light/dark edges. Preserve the artwork footprint,
   not merely output dimensions: width=2*native_width AND height=2*native_height, margins/anchors doubled,
   internal geometry unchanged. No trimming, independent component stretching, native-mask stamping or filler.
   At alpha thresholds 16 and 128: bounds/centroid error <=2 x2 pixels, occupied area ratio 0.90–1.10,
   silhouette IoU >=0.85. These are rejection guards, not proof of fidelity. Measure at least three identifiable
   separated landmarks on source and output (source coordinates in native pixels, output coordinates in x2);
   each axis error <=2 x2 pixels. Inspect material/color, tiny symbols, holes and thin supports visually too.
   Key removal alone is insufficient: use the supplied local matte unmixing, preserve real colored interiors,
   then inspect residual edge spill after premultiplied resizing. Never erase real material to make QA pass.
6. Update outputs/progress.json per cell: reviewed_candidate, needs_inspection, or unattempted. Record concrete
   observations, measured landmarks, paths and actual master filename. A questioned cell stays unfinished.
   Acceptable siblings continue independently. Do NOT retry during this first pass; collect compatible failures
   for a later repair bundle after fresh work is exhausted. Repository acceptance/runtime validation happens later.

Return a ZIP containing raw masters, submitted prompts, exact-x2 candidate PNGs if processed, review comparisons,
and progress.json. Include the unchanged input manifest for ID mapping. If time/tool limits prevent completion,
return ALL completed work and list the exact next sheet; do not fabricate outputs, silently omit cells, retry
finished work, or claim all {count} restored. Raw-only returns are useful: mark final fitting/review pending.

Keep commentary short: one sheet outcome with passing/questionable cell IDs is enough. Keep working through
the manifest while tools permit; this prompt does not promise that every sheet fits in a single chat turn.
"""

PROMPT = """Faithfully restore the supplied Might and Magic inventory reference sheet in place.
Exactly {grid} columns and {grid} rows; only the listed slots are occupied. Preserve the complete grid composition.
Each cell is a separate item: preserve its own silhouette, orientation, component count, symbols, openings,
colors, native canvas margins and internal proportions. Do not borrow decorations or materials from siblings.
Reconstruct continuous painted surfaces and fine faithful material detail at final x2 size; no pixel-art redraw,
enlarged squares, mosaics, repeated dot highlights, stair steps or mere blur. No redesign, invented ornament,
lettering, additional straps/studs, overlarge gems, stronger shine or speculative details.
Outside artwork and in genuine holes use opaque pure magenta RGB(255,0,255), #FF00FF. No checkerboard,
labels, borders, shadows, gradient, colored bounce or magenta fringe. Preserve genuine purple/pink artwork.
Native art is enlarged 4x in this reference ONLY for legibility; this is not the requested rendering style.
Keep its placement and proportions. Final deliverables will be exactly 2x each native canvas after extraction.
Render one detailed square master, preferably {master_edge}x{master_edge}, retaining the supplied grid proportions.
Input image role: reference.png is the edit target. The quality examples are not content to insert.

Sheet {sheet}; category: {category}. Reference canvas: {size} pixels.
Occupied slots (row-major; other slots MUST remain empty):
{cells}
"""

PORTRAIT_MASTER = """# Restore this Might and Magic portrait bundle

There are {count} target portraits on {sheets} sheets. Use the built-in image-generation/editing tool;
one sheet is one imagegen call. Read manifest.json and examples/README.md first.
These are faithful painted restorations, not new faces, photorealistic replacements or enlarged pixel art.
Preserve each native rendering style, including photographic sources already present in the registry.
Some NPC registry slots show doors, objects, symbols or elementals rather than faces: restore that actual
content and choose appropriate structural landmarks. Never invent a person where the source has none.
OPEN the current reference.png before generation. Preserve each identity, expression, gaze, head angle,
clothing, framing, background and subdued palette. Reconstruct continuous detail without beautifying,
changing age, inventing jewelry, exaggerating eyes/teeth or borrowing another portrait's facial features.

This is an independent external FIRST PASS: ALL sheets can run from the supplied native references.
Do not wait for pilot approvals, supplements, files or results from another chat. No external pilot is required.
Repository style-pilot bookkeeping is a local review concern, not a generation prerequisite for this bundle.
Preserve identity within each supplied player group. If a sheet lists native_identity_reference, OPEN it too
and submit it as a second, identity-only reference. It contains ORIGINAL portraits of this same character,
not approved restorations or extra targets. Preserve each target's own expression; do not copy a seed expression.
No spellbook page crops are included. Record sheets[SNNN].dependency_cells as an empty object because no external restored
reference was used. Review candidates honestly; final acceptance and staging happen after return to the repository.
For sheets with native identity context, retain the supplied native_identity_sources hash mapping in progress.
All required native identity context is already inside this ZIP. Do not request accepted seeds or another bundle.

For each sheet, in manifest order:
1. Read sheets/SNNN/prompt.txt and layout.json; OPEN the full-resolution reference. Submit the exact prompt
   with its listed references. NPC faces are separate identities; player frames stay within one character's group.
2. Preserve the entire rectangular painted background of EVERY portrait. Magenta #FF00FF belongs ONLY in
   grid gutters and empty slots. Do not replace face backgrounds or dark clothing with transparency.
3. Save the actual returned master unchanged in outputs/raw/SNNN.png, its real returned filename, SHA-256
   and exact submitted prompt in outputs/prompts/SNNN.txt immediately. Never reconstruct a missing prompt log.
4. Inspect the full raw sheet and every occupied cell before extraction. Run the included process_sheet.py
   if available. For these opaque portraits it crops the recorded native rectangle with one sheet transform,
   then exports exactly 2*native_width by 2*native_height. No foreground fitting, trimming or magenta cleanup
   inside portraits. If the grid drifted, flag it; do not crop off hair, chins or repaint padding to hide drift.
5. OPEN every final x2 candidate and its complete native/restored comparison. Opaque rectangle/alpha checks
   do not establish fitting: independently measure at least three separated visible features, normally both
   eyes and mouth/chin, on source and output. Record native source coordinates and x2 output coordinates;
   each axis error must be <=2 x2 pixels. Check head size, expression, framing and background visually too.
   Reject enlarged pixel blocks, blur-only output, invented facial detail, missing features or altered identity.
6. Copy progress.template.json to outputs/progress.json and update every cell as reviewed_candidate,
   needs_inspection or unattempted with actual observations, landmarks and paths. Flag weak cells and continue
   other siblings. Do not retry this first pass. Flagged cells remain unfinished for later review/repair.

Return raw masters, prompts, exact-x2 candidates if processed, comparison PNGs and progress.json, plus the
unchanged manifest.json. Preserve all completed work on interruption and name the next sheet.
Do not claim visual inspection, generation, acceptance or completion that did not happen.
Keep commentary concise. Python is for files/crops/QA only; never substitute drawing or upscalers for imagegen.
"""

PORTRAIT_PROMPT = """Faithfully restore the supplied Might and Magic painted portrait sheet in place.
Exactly {grid} columns and {grid} rows, retaining every listed native canvas rectangle and empty slot.
Preserve each person's identity, age, facial structure, expression, gaze, head angle, hairstyle, clothing,
painted background, framing, internal feature coordinates and subdued color balance. Restore smooth painted
curves and continuous fine detail visible at final x2 size, without pixel blocks, blur-only enlargement,
photorealistic restyling, beautification, invented jewelry or exaggerated eyes/teeth. Do not mix identities.
Each portrait is a complete OPAQUE rectangular painting: preserve its background edge to edge.
The native reference determines rendering style. Keep photographic source portraits photographic and retain
non-human subjects. Registry slots showing doors/objects/symbols must retain that content without invented faces.
Use flat pure magenta #FF00FF ONLY outside the portrait rectangles, in gutters and empty slots.
No labels, borders or checkerboards. Native art is enlarged 4x solely for reference legibility.
Produce one detailed square master, preferably {master_edge}x{master_edge}, with the exact input grid placement.
Use the supplied native reference directly. No approved pilot or supplement is required for this first pass.
Sheet {sheet}; category: {category}; reference canvas {size}.
Occupied slots (row-major; all other slots remain empty):
{cells}
"""


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def reserve(destination):
    manifest_path = destination / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    cells = [c for sheet in manifest['sheets'] for c in sheet['cells']]
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = queue_module.Queue()
        fresh = {c for job in q.pending_work('first-pass') for c in job['selected_cells']}
        policy = manifest.get('preparation_mode')
        if policy in ('independent_external_portrait_first_pass', 'external_portrait_native_identity_first_pass'):
            attempted = {c for a in q.state['attempts']
                         for c in json.loads(Path(a['payload']).read_text()).get('selected_cells',
                             [m['id'] for m in q.jobs[a['job']]['members']])}
            for cell in cells:
                job = q.jobs[q.members[cell][0]]
                assert job['treatment'] in ('npc_portrait_family', 'player_portrait_frames')
                allowed = ('accepted_treatment_pilot', 'accepted_seed_job') if (
                    policy == 'external_portrait_native_identity_first_pass') else ('accepted_treatment_pilot',)
                assert all(d['kind'] in allowed for d in job['dependencies'])
                if policy == 'external_portrait_native_identity_first_pass':
                    sheet = next(s for s in manifest['sheets'] if cell in s['cells'])
                    q.generation_dependencies(job, dict(dependency_policy=policy,
                        external_return=dict(bundle=destination.name),
                        native_identity_sources=sheet['native_identity_sources']))
                assert cell not in attempted and cell not in q.state['cells']
                assert job['id'] not in q.state.get('claims', {})
                fresh.add(cell)
        assignments = q.state.setdefault('external_assignments', {})
        for cell in cells:
            old = assignments.get(cell)
            assert not old or old['manifest_sha256'] == digest(manifest_path), 'Already assigned to another bundle: ' + cell
            assert cell in fresh or old and old['manifest_sha256'] == digest(manifest_path), cell
        for sheet in manifest['sheets']:
            layout = json.loads((destination / sheet['layout']).read_text())
            for cell in layout['cells']:
                assert digest(ROOT / q.members[cell['id']][1]['source_path']) == cell['original_sha256']
                assignments[cell['id']] = dict(bundle=destination.name, manifest=str(manifest_path),
                    manifest_sha256=digest(manifest_path), status='assigned')
                if policy in ('independent_external_portrait_first_pass', 'external_portrait_native_identity_first_pass'):
                    assignments[cell['id']]['dependency_policy'] = policy
        queue_module.save(q.state_path, q.state)


def export(count, destination, expanded=False, assign=False, dropbox_folder=None, portraits=False, npc_count=None,
           portrait_frames=False):
    assert not portrait_frames or portraits
    q = queue_module.Queue()
    before = digest(q.state_path)
    # Avoid both previously accepted art and repeated native appearances across namespace aliases.
    assigned = set(q.state.get('external_assignments', {}))
    seen = {a['source_sha256'] for c, (_, a) in q.members.items() if q.accepted(c) or c in assigned}
    seen_rgba = {q.targets[a['target']]['native_rgba_sha256']
                 for c, (_, a) in q.members.items() if q.accepted(c) or c in assigned}
    candidates = []
    worklist = q.pending_work('first-pass')
    if portraits:
        excluded = assigned | set(q.state['cells'])
        for attempt in q.state['attempts']:
            payload = json.loads(Path(attempt['payload']).read_text())
            excluded.update(payload.get('selected_cells', [m['id'] for m in q.jobs[attempt['job']]['members']]))
        seen.update(q.members[c][1]['source_sha256'] for c in excluded if c in q.members)
        seen_rgba.update(q.targets[q.members[c][1]['target']]['native_rgba_sha256']
                         for c in excluded if c in q.members)
        worklist = [dict(id=j['id'], treatment=j['treatment'],
                        selected_cells=[m['id'] for m in j['members'] if m['id'] not in excluded])
                    for j in q.jobs.values() if j['id'] not in q.state.get('claims', {})]
    worklist.sort(key=lambda work: work['treatment'] != 'inventory_items')
    for work in worklist:
        j = q.jobs[work['id']]
        treatments = ('npc_portrait_family', 'player_portrait_frames') if portraits else (
            ('inventory_items', 'fitted_equipment_variants') if expanded else ('inventory_items',))
        if j['treatment'] not in treatments:
            continue
        allowed = ('accepted_treatment_pilot', 'accepted_seed_job') if portrait_frames else ('accepted_treatment_pilot',)
        if any(d['kind'] not in allowed for d in j['dependencies']):
            continue
        for cell in work['selected_cells']:
            _, member = q.members[cell]
            t = q.targets[member['target']]
            supported = (t['compositing']['profiles'] == ['hud'] and member['cleanup'] == 'opaque_canvas'
                         if portraits else t['compositing']['profiles'] == ['item'] and
                         member['cleanup'] == 'alpha_cutout_or_effect')
            if ((not expanded and not portraits and
                    (t['namespace'] != 'engine' or max(member['export_region'][2:]) > 192)) or not supported or
                    member['source_sha256'] in seen or t['native_rgba_sha256'] in seen_rgba):
                continue
            assert member['source_rect'] == [0, 0, *t['native_size']]
            assert digest(ROOT / member['source_path']) == member['source_sha256']
            definitions = t.get('equipment_registration', {}).get('item_definitions', [])
            names = ' '.join(d['name'] for d in definitions).lower()
            equip = {d['equip_stat'].lower() for d in definitions}
            if portraits:
                category = ('NPC portraits: separate identities, preserve each full painted rectangle'
                            if j['treatment'] == 'npc_portrait_family' else
                            'Player identity ' + next((d['job'] for d in j['dependencies']
                                if d['kind'] == 'accepted_seed_job'), j['id']) +
                            ': preserve expressions and shared facial structure')
            elif j['treatment'] == 'fitted_equipment_variants':
                category = 'Equipped family ' + j['id'] + ': preserve each pose, material and attachment independently'
            elif 'painting' in names:
                category = 'Framed paintings: preserve face identity and framing'
            elif member['id'].split('--')[-1] in {'7item252.bmp', '7item253.bmp', '7item254.bmp',
                                                 '7item255.bmp', '7item256.bmp', '7item257.bmp', '7item258.bmp'}:
                category = 'Sealed letters: preserve exact envelope and seal symbols'
            elif equip & {'belt', 'cloak', 'helm', 'ring', 'shield', 'boots', 'gauntlets'}:
                category = 'Equipment cutouts: preserve individual material and ornament'
            else:
                category = '/'.join(sorted({d['equip_stat'] + ':' + d['skill_group'] for d in definitions}))
            candidates.append((category, member, t))
            seen.add(member['source_sha256'])
            seen_rgba.add(t['native_rgba_sha256'])
    assert len(candidates) >= count, f'Only {len(candidates)} eligible unique fresh assets'
    if portraits:
        npc = [c for c in candidates if c[1]['treatment'] == 'npc_portrait_family']
        players = [c for c in candidates if c[1]['treatment'] == 'player_portrait_frames']
        npc_count = min(count, len(npc)) if npc_count is None else npc_count
        assert 0 <= npc_count <= min(count, len(npc))
        selected = npc[:npc_count] + players[:count-npc_count]
        assert len(selected) == count
        selected_player_ids = {c[1]['id'] for c in selected if c[1]['treatment'] == 'player_portrait_frames'}
        for _, member, _ in selected:
            if member['treatment'] == 'player_portrait_frames' and not portrait_frames:
                family = q.jobs[q.members[member['id']][0]]['members']
                assert {m['id'] for m in family} <= selected_player_ids, 'Keep complete player seed groups together'
    else:
        selected = candidates[:count]
    groups = collections.defaultdict(list)
    for category, member, t in selected:
        deps = q.dependency_cells(q.jobs[q.members[member['id']][0]])
        size_class = 3 if max(t['x2_size']) <= 192 else 2 if max(t['x2_size']) <= 768 else 1
        groups[(category, t['namespace'], tuple(sorted(deps)), size_class)].append((member, t))
    batches = []
    for (category, _, _, grid), rows in groups.items():
        rows.sort(key=lambda row: math.prod(row[0]['export_region'][2:]))
        while rows:
            batch, rows = [rows[0]], rows[1:]
            area = math.prod(batch[0][0]['export_region'][2:])
            while rows and len(batch) < grid*grid and math.prod(rows[0][0]['export_region'][2:]) <= 4 * area:
                batch.append(rows.pop(0))
            batches.append((category, grid, batch))
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'sources').mkdir()
    (destination / 'sheets').mkdir()
    manifest = dict(schema_version=1, target_count=count, sheet_count=len(batches),
                    status='prepared_only_not_generated_or_accepted', bundle_id=destination.name,
                    namespaces=sorted({t['namespace'] for _, _, t in selected}),
                    source_state_sha256=before, jobs_sha256=digest(HERE / 'jobs.json'),
                    source_manifest_sha256=digest(HERE / 'expected_targets.json'),
                    selection='fresh eligible unique full-canvas item-profile cutouts; adaptive grid by size', sheets=[])
    if portraits:
        manifest.update(preparation_mode=('external_portrait_native_identity_first_pass' if portrait_frames else
                                         'independent_external_portrait_first_pass'),
                        selection=('unattempted unique opaque portraits; supplied native identity context; independent first pass'
                                   if portrait_frames else
                                   'unattempted unique opaque portraits; complete player seed groups; independent first pass'))
        write_json(destination / 'PREREQUISITES.json', {})
    ledger = dict(bundle=destination.name, sheets={}, cells={})
    for n, (category, grid, batch) in enumerate(batches, 1):
        sid = f'S{n:03d}'
        folder = destination / 'sheets' / sid
        folder.mkdir()
        edge = max(320, 2 * max(max(m['export_region'][2:]) for m, _ in batch) + 16)
        reference = Image.new('RGBA', (edge * grid, edge * grid), '#ff00ff')
        layout = dict(sheet_id=sid, category=category, grid=[grid, grid], reference_size=list(reference.size), cells=[])
        lines = []
        for i, (member, target) in enumerate(batch):
            cell = member['id']
            source = ROOT / member['source_path']
            shutil.copyfile(source, destination / 'sources' / cell)
            with Image.open(source) as im:
                native = rendered(im, 'hud' if portraits else 'item')
            native.save(destination / 'sources' / (cell + '.png'))
            w, h = native.width * 4, native.height * 4
            x, y = i % grid * edge, i // grid * edge
            left, top = x + (edge - w) // 2, y + (edge - h) // 2
            reference.alpha_composite(native.resize((w, h), Image.Resampling.NEAREST), (left, top))
            names = sorted({d['name'] for d in target.get('equipment_registration', {}).get('item_definitions', [])})
            entry = dict(id=cell, slot=i+1, slot_rect=[x, y, edge, edge],
                         native_canvas_rect=[left, top, w, h], native_size=list(native.size),
                         x2_size=target['x2_size'], native_png=f'sources/{cell}.png',
                         original_file=f'sources/{cell}', original_sha256=digest(source),
                         rendered_png_sha256=digest(destination / 'sources' / (cell + '.png')),
                         original_job=q.members[cell][0], member=member, target=target)
            layout['cells'].append(entry)
            lines.append(f'{i+1}. {cell}; native name/context: {", ".join(names[:3])}; '
                         f'native {native.width}x{native.height}; final {target["x2_size"]}; '
                         f'full native canvas rectangle in reference xywh={[left, top, w, h]}.')
            ledger['cells'][cell] = dict(sheet=sid, status='unattempted', reason='', landmarks=[], review_images=[])
        reference.convert('RGB').save(folder / 'reference.png')
        write_json(folder / 'layout.json', layout)
        master_edge = max(1920, math.ceil(max(max(t['x2_size']) for _, t in batch) * grid * 1.1 / 16)*16)
        (folder / 'prompt.txt').write_text((PORTRAIT_PROMPT if portraits else PROMPT).format(
                                                       sheet=sid, category=category, grid=grid, master_edge=master_edge,
                                                       size=list(reference.size), cells='\n'.join(lines)))
        manifest['sheets'].append(dict(id=sid, cells=[m['id'] for m, _ in batch],
                                      layout=f'sheets/{sid}/layout.json', prompt=f'sheets/{sid}/prompt.txt',
                                      reference=f'sheets/{sid}/reference.png'))
        if portraits:
            manifest['sheets'][-1]['required_accepted_cells'] = []
        ledger['sheets'][sid] = dict(status='unattempted', raw_path=None, submitted_prompt_path=None)
        if portrait_frames:
            add_native_identity(q, destination, manifest['sheets'][-1], ledger['sheets'][sid])
    delivery_prompt = ''
    if dropbox_folder:
        return_name = destination.name.replace('restoration_', 'resto_', 1) + '.zip'
        partial_name = return_name[:-4] + '_partial.zip'
        delivery = dict(provider='dropbox', folder=dropbox_folder.rstrip('/'), filename=return_name,
                        partial_filename=partial_name, fallback='Attach the verified ZIP as a downloadable chat file')
        manifest['delivery'] = delivery
        write_json(destination / 'DELIVERY.json', delivery)
        delivery_prompt = (
            '\n## Deliver the completed result to Dropbox\n\n'
            f'This request authorizes uploading this bundle\'s result ZIP to the linked Dropbox account at '
            f'`{delivery["folder"]}/{return_name}` after completing the manifest. Use exactly that filename. '
            'Keep ZIP contents relative to its root, including unchanged manifest.json, outputs/progress.json, '
            'outputs/raw/, outputs/prompts/, and any candidates/reviews. Include actual model-returned filenames '
            'and SHA-256 hashes in a provenance ledger. Save the exact prompt immediately when submitting each sheet; '
            'do not reconstruct submission history from the input prompts afterward.\n\n'
            'Before uploading, test the ZIP CRC, decode every included PNG and reconcile every target ID with '
            'the progress ledger. Regenerate corrupt comparison files from retained art; never replace raw masters '
            'with reconstructed images. Clearly distinguish generation completion from visual acceptance. '
            'A needs_inspection candidate can be a completed first-pass attempt; an unattempted sheet cannot.\n\n'
            'Use an available Dropbox upload/write action only if it actually supports creating this ZIP. '
            'If the destination folder does not exist, create the required folders using an available folder-creation '
            'action; this request authorizes creating this delivery folder. If that action is unavailable, attach '
            'the result ZIP for download instead. A missing folder must not prevent restoration. '
            'A linked search/read connector does not establish upload capability. Verify the upload response '
            'and remote filename/size, then report the actual Dropbox path/link and ZIP SHA-256. Never claim '
            'upload success without a successful write. Do not overwrite an existing result silently. '
            'If Dropbox upload is unavailable, preserve the ZIP and attach it as a downloadable file instead; '
            'state briefly that Dropbox upload was unavailable. Do not spend the generation turn troubleshooting '
            'integrations, requesting API keys or substituting an external generation API.\n\n'
            f'If interrupted, return the verified partial work as `{partial_name}` (same Dropbox folder if writable), '
            f'with all {count} cell statuses and the exact next sheet recorded. Never label a partial bundle complete.\n')
    write_json(destination / 'manifest.json', manifest)
    write_json(destination / 'progress.template.json', ledger)
    (destination / 'MASTER_PROMPT.md').write_text(
        (PORTRAIT_MASTER if portraits else MASTER).format(count=count, sheets=len(batches)) + delivery_prompt)
    add_examples(q, destination)
    shutil.copyfile(HERE / 'chat_bundle_process.py', destination / 'process_sheet.py')
    shutil.copyfile(HERE / 'matte.py', destination / 'matte.py')
    # Reuse the actual project fitting functions, without their repository-specific imports or driver.
    source = (HERE / 'pilots/boots/process.py').read_text()
    tree = ast.parse(source)
    functions = [ast.get_source_segment(source, node) for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in ('transform', 'fit')]
    (destination / 'fitting.py').write_text('import numpy as np\nfrom PIL import Image\nfrom scipy import optimize\n\n'
                                          + '\n\n'.join(functions) + '\n')
    (destination / 'requirements.txt').write_text('Pillow\nnumpy\nscipy\n')
    (destination / 'README.md').write_text(
        '# Portable imagegen restoration handoff\n\n'
        f'{count} fresh unique target images; {len(batches)} generation sheets, at most nine targets per sheet. '
        'Examples and references are extra files, not additional targets.\n\n'
        'Attach this ZIP and paste MASTER_PROMPT.md into the receiving chat. Work in sheet order. '
        'The original BMPs include their palettes; adjacent PNGs contain the recorded native rendering. '
        'No repository or absolute local path is required by the prompts/helper.\n\n'
        'Optional extraction: `python3 process_sheet.py S001 outputs/raw/S001.png`. '
        'Install requirements.txt if needed. The helper writes candidates and comparisons, never acceptance. '
        'Copy progress.template.json to outputs/progress.json and update it with actual observations.\n\n'
        'Return raw masters even if processing or final review is incomplete. Stable source IDs, hashes, '
        'original job/member/target records and crop coordinates in each layout support later repository import. '
        'Recheck current queue/source state before recording or accepting returned artwork; never overwrite '
        'work accepted elsewhere after export. Local assignment tracking prevents duplicate scheduling; '
        'preparation is never generation or acceptance.\n' + delivery_prompt)
    # Overview is for the bundle producer/recipient, never an imagegen edit target.
    for page in range(math.ceil(len(manifest['sheets']) / 12)):
        overview = Image.new('RGB', (1200, 960), '#444444')
        draw = ImageDraw.Draw(overview)
        for i, sheet in enumerate(manifest['sheets'][page*12:(page+1)*12]):
            with Image.open(destination / sheet['reference']) as im:
                im.thumbnail((285, 280))
                x, y = i % 4 * 300, i // 4 * 320
                overview.paste(im, (x, y+25))
                draw.text((x+4, y+4), f'{sheet["id"]}: {len(sheet["cells"])} targets', fill='white')
        overview.save(destination / f'overview-{page+1}.jpg')
    assert digest(q.state_path) == before, 'Queue changed during export; recheck selection'
    hashes = {str(p.relative_to(destination)): digest(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    write_json(destination / 'SHA256SUMS.json', hashes)
    archive = destination.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(destination.rglob('*')):
            if p.is_file():
                z.write(p, str(p.relative_to(destination)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    if assign:
        reserve(destination)
    print(json.dumps(dict(zip=str(archive), bytes=archive.stat().st_size,
                          targets=count, sheets=len(batches), assigned=assign), indent=2))


def add_native_identity(q, destination, sheet, ledger):
    """Supply native seed context, separately from generated targets and accepted-art dependencies."""
    jobs = {q.members[c][0] for c in sheet['cells']}
    seed_jobs = {next((d['job'] for d in q.jobs[j]['dependencies'] if d['kind'] == 'accepted_seed_job'), j)
                 for j in jobs if q.jobs[j]['treatment'] == 'player_portrait_frames'}
    assert len(seed_jobs) <= 1, 'Keep one player identity per sheet'
    members = [m for j in sorted(seed_jobs) for m in q.jobs[j]['members']]
    hashes = {m['id']: m['source_sha256'] for m in members}
    sheet['native_identity_sources'] = hashes
    ledger.update(dependency_cells={}, native_identity_sources=hashes)
    if not members:
        return
    folder = destination / 'identity' / next(iter(seed_jobs))
    reference = folder / 'native-reference.png'
    if not reference.exists():
        folder.mkdir(parents=True)
        edge = max(4 * max(q.targets[m['target']]['native_size']) for m in members) + 24
        contact = Image.new('RGB', (edge * 3, edge * math.ceil(len(members) / 3)), '#444444')
        for i, member in enumerate(members):
            source = ROOT / member['source_path']
            assert digest(source) == member['source_sha256']
            shutil.copyfile(source, folder / member['id'])
            with Image.open(source) as im:
                native = rendered(im, 'hud').convert('RGB')
            native.save(folder / (member['id'] + '.png'))
            native = native.resize((native.width * 4, native.height * 4), Image.Resampling.NEAREST)
            contact.paste(native, (i % 3 * edge + (edge-native.width)//2,
                                  i // 3 * edge + (edge-native.height)//2))
        contact.save(reference)
    sheet['native_identity_reference'] = str(reference.relative_to(destination))
    sheet['native_identity_files'] = {m['id']: str((folder / m['id']).relative_to(destination)) for m in members}
    sheet['native_identity_reference_sha256'] = digest(reference)
    prompt = destination / sheet['prompt']
    with prompt.open('a') as out:
        out.write('\nSecond image: ' + sheet['native_identity_reference'] +
            ' is ORIGINAL native identity context for this same character, not a restoration or edit target. '
            'Use it to preserve facial structure, age, hairstyle and palette across target expressions. '
            'Output ONLY the first reference grid; do not append context portraits, copy seed expressions, '
            'merge grids or change target placement. Both references are already supplied; no approval needed.\n')


def add_examples(q, destination):
    folder = destination / 'examples'
    folder.mkdir()
    examples = [('GOOD', 'item117v1', 'item117_01'), ('BAD', 'item120v1', 'item120_01')]
    for label, name, production in examples:
        cell = f'engine--icons--{name}.bmp'
        if label == 'GOOD':
            assert q.accepted(cell)
            assert q.state['cells'][cell]['sha256'] == digest(HERE / 'production' / production / (name + '.png'))
        else:
            assert q.state['cells'][cell]['status'] == 'deferred'
        member = q.members[cell][1]
        with Image.open(ROOT / member['source_path']) as im:
            native = rendered(im, 'item').resize(tuple(member['export_region'][2:]), Image.Resampling.NEAREST)
        restored = Image.open(HERE / 'production' / production / (name + '.png')).convert('RGBA')
        proof = Image.new('RGB', (620, 200), '#444444')
        draw = ImageDraw.Draw(proof)
        for x, title, im in ((5, 'Native x2 REFERENCE ONLY', native), (310, label + ' imagegen result', restored)):
            draw.text((x, 5), title, fill='white')
            for y, bg in ((25, '#eeeeee'), (100, '#111111')):
                tile = Image.new('RGBA', im.size, bg)
                tile.alpha_composite(im)
                proof.paste(tile.convert('RGB'), (x, y))
        proof.save(folder / (label + '.png'))
        shutil.copyfile(HERE / 'production' / production / (name + '-master.png'), folder / (label + '-master-crop.png'))
    (folder / 'README.md').write_text(
        '# Inspect these examples before generating\n\n'
        'GOOD.png: reviewed/accepted item117v1 belt. Smooth brown leather and restrained silver buckle/studs '
        'preserve native layout, count, silhouette and color; final canvas/landmarks passed. '
        'GOOD-master-crop.png shows actual imagegen detail before final fitting, not an enlarged native image.\n\n'
        'BAD.png: deferred item120v1. Despite passing silhouette checks, tiny scattered marks became a prominent '
        'extra right-hand star/sun, repeated diamond studs and heavier brighter gold trim. It is smooth but '
        'changes the design. BAD-master-crop.png makes the invention visible. Do not copy this embellishment.\n\n'
        'Also reject high-resolution output that merely repeats native square pixels, blurry upscaling, '
        'checkerboard backgrounds, magenta spill, missing thin parts, stretched proportions, smaller artwork '
        'surrounded by filler, clipping, swapped cells, new text and invented geometry. '
        'These examples are finish references only, not generation targets or templates for unrelated materials.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=200)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expanded', action='store_true', help='Include larger inventory and fitted equipment cutouts')
    parser.add_argument('--assign', action='store_true', help='Reserve exported cells in the local scheduling queue')
    parser.add_argument('--assign-existing', action='store_true', help='Reserve an existing bundle without rebuilding it')
    parser.add_argument('--dropbox-folder', help='Add explicit per-bundle Dropbox result upload instructions')
    parser.add_argument('--portraits', action='store_true', help='Prepare independent first-pass opaque portrait bundles')
    parser.add_argument('--portrait-frames', action='store_true', help='Include expression followers with native identity context')
    parser.add_argument('--npc-count', type=int, help='NPC count in a portrait bundle; remaining slots are whole player seed groups')
    args = parser.parse_args()
    assert args.count > 0
    if args.assign_existing:
        reserve(args.output.resolve())
    else:
        export(args.count, args.output.resolve(), args.expanded, args.assign, args.dropbox_folder,
               args.portraits, args.npc_count, args.portrait_frames)
