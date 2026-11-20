"""Inspect and resume prepared HUD work. This tool never calls imagegen or installs assets."""
import argparse
import collections
import fcntl
import hashlib
import json
import math
import shutil
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

from finalize_classification import HERE, ROOT, digest, read
from freeze_targets import rendered
import registration
from native_sources import native_source


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def validate_input_hashes(inputs, reconciliation, manifest_sha256, root=ROOT):
    expected = dict(inputs)
    if reconciliation:
        path = root / reconciliation['path']
        assert digest(path) == reconciliation['sha256'], 'Input reconciliation receipt changed'
        revision = json.loads(path.read_text())
        assert revision['schema'] == 'openyamm-icon-input-reconciliation-v1'
        assert revision['frozen_manifest_sha256'] == manifest_sha256, 'Reconciliation belongs to another catalog'
        for name, change in revision['inputs'].items():
            assert name in inputs, f'Unregistered reconciled input: {name}'
            assert change['frozen_sha256'] == inputs[name], f'Reconciliation baseline differs: {name}'
            for snapshot, key in [('before_snapshot', 'frozen_sha256'), ('current_snapshot', 'current_sha256')]:
                assert digest(root / change[snapshot]) == change[key], f'Reconciliation snapshot changed: {name}'
            expected[name] = change['current_sha256']
    for name, sha in expected.items():
        assert digest(root / name) == sha, f'Input drift: {name}; reconcile before continuing the queue.'


def reference_contact(entries, path):
    """Pack already accepted references without rescaling their registered pixels."""
    columns = min(2, len(entries))
    cell_width = max(image.width for _, image in entries) + 32
    cell_height = max(image.height for _, image in entries) + 48
    sheet = Image.new('RGB', (columns * cell_width, math.ceil(len(entries) / columns) * cell_height), (42, 43, 45))
    draw = ImageDraw.Draw(sheet)
    rectangles = []
    for i, (label, image) in enumerate(entries):
        x, y = i % columns * cell_width + 16, i // columns * cell_height + 32
        rgba = image.convert('RGBA')
        sheet.paste(rgba, (x, y), rgba)
        draw.text((x, y - 20), label, fill='white')
        rectangles.append(dict(label=label, xywh=[x, y, image.width, image.height]))
    sheet.save(path)
    return rectangles


def accepted_cell(cells, cell, layout_hash, checking=None):
    """Validate immutable acceptance evidence independently of current runtime UI layouts."""
    record = cells.get(cell, {})
    if record.get('status') != 'accepted':
        return False
    if record.get('layout_sha256') != layout_hash(cell):
        return False
    artifact = Path(record['artifact'])
    if not artifact.is_file() or digest(artifact) != record['sha256']:
        return False
    for name, expected in record.get('evidence_hashes', {}).items():
        if not Path(name).is_file() or digest(Path(name)) != expected:
            return False
    checking = set() if checking is None else set(checking)
    assert cell not in checking, 'Cyclic accepted dependency'
    checking.add(cell)
    for dependency, expected in record.get('dependency_cells', {}).items():
        if not accepted_cell(cells, dependency, layout_hash, checking) or cells[dependency]['sha256'] != expected:
            return False
    return True


class Queue:
    def __init__(self, state_path=None):
        self.manifest = read('expected_targets.json')
        self.prepared = read('jobs.json')
        self.jobs = {j['id']: j for j in self.prepared['jobs']}
        self.targets = {t['id']: t for t in self.manifest['targets']}
        self.members = {m['id']: (j['id'], m) for j in self.jobs.values() for m in j['members']}
        self.target_cells = collections.defaultdict(list)
        for cell, (_, member) in self.members.items():
            self.target_cells[member['target']].append(cell)
        self.state_path = state_path or HERE / 'checkpoint/state.json'
        self.payload_root = (HERE / 'prepared_payloads' if self.state_path.parent == HERE / 'checkpoint'
                             else self.state_path.parent / 'payloads')
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else dict(
            schema_version=1, jobs_sha256=digest(HERE / 'jobs.json'), cells={}, attempts=[], claims={})
        assert self.state['jobs_sha256'] == digest(HERE / 'jobs.json'), 'Queue changed; reconcile state explicitly.'
        assert self.prepared['source_manifest_sha256'] == digest(HERE / 'expected_targets.json'), 'Target drift.'
        validate_input_hashes(self.manifest['inputs'], self.state.get('input_reconciliation'),
                              digest(HERE / 'expected_targets.json'))
        archive = self.state.get('native_source_archive')
        if archive:
            assert digest(ROOT / archive['path']) == archive['sha256'], 'Native source archive drift'
        self.layout = None
        self.layout_cells = set()
        revision = self.state.get('layout_revision')
        if revision:
            path = Path(revision['path'])
            assert digest(path) == revision['sha256'], 'Preview layout revision changed'
            self.layout = json.loads(path.read_text())
            for name, sha in self.layout['evidence_hashes'].items():
                assert digest(Path(name)) == sha, 'Preview layout evidence changed'
            assert digest(ROOT / self.layout['native_layout']) == self.layout['native_layout_sha256']
            assert digest(Path(self.layout['preview_layout'])) == self.layout['preview_layout_sha256']
            recipes = {}
            for target_id, change in self.layout['targets'].items():
                target = self.targets[target_id]
                assert target['treatment'] == 'spell_icon_pair'
                self.layout_cells.update(self.target_cells[target_id])
                for recipe in target['page_dependencies']:
                    assert recipe['x2_draw_rect'] == change['before_x2'], 'Unexpected original crop'
                    # Declared button dimensions can differ between the paired native bitmaps (Jump).
                    # A position revision preserves that existing logical rectangle and each native export size.
                    assert change['after_x2'][2:] == change['before_x2'][2:]
                    recipe['x2_draw_rect'] = change['after_x2']
                    recipe['native_draw_rect'] = [v / 2 for v in change['after_x2']]
                    recipes[(recipe['element'], recipe['state'])] = recipe
            for job in self.jobs.values():
                for dependency in job['dependencies']:
                    if dependency['kind'] == 'accepted_page_crop':
                        recipe = dependency['recipe']
                        key = (recipe['element'], recipe['state'])
                        if key in recipes:
                            dependency['recipe'] = recipes[key]

    def layout_hash(self, cell):
        return self.state['layout_revision']['sha256'] if cell in getattr(self, 'layout_cells', set()) else None

    def storage_root(self):
        if self.state.get('layout_revision'):
            return Path(self.state['layout_revision']['path']).parent
        return self.state_path.parent

    def accepted(self, cell, checking=None):
        return accepted_cell(self.state['cells'], cell, self.layout_hash, checking)

    def dependency_cells(self, job):
        result = set()
        for dependency in job['dependencies']:
            if 'job' in dependency:
                result.update(m['id'] for m in self.jobs[dependency['job']]['members'])
            else:
                result.update(self.target_cells[dependency['target']])
        return sorted(result)

    def blockers(self, job):
        excluded = set(self.state.get('user_excluded_targets', {})) | set(self.state.get('retired_targets', {}))
        return ([m['id'] for m in job['members'] if m['target'] in excluded]
                + [cell for cell in self.dependency_cells(job) if not self.accepted(cell)])

    def generation_dependencies(self, job, payload):
        """External portrait first passes need native art; style pilots remain local review references."""
        if payload.get('dependency_policy') == 'external_portrait_native_identity_first_pass':
            assert payload.get('external_return'), 'Native identity policy is scoped to external portrait returns'
            assert job['treatment'] in ('npc_portrait_family', 'player_portrait_frames')
            assert all(d['kind'] in ('accepted_treatment_pilot', 'accepted_seed_job') for d in job['dependencies'])
            assert payload.get('native_identity_sources') == self.native_identity_sources(job), (
                'Missing or mismatched native identity context')
            return []
        if payload.get('dependency_policy') == 'independent_external_portrait_first_pass':
            assert payload.get('external_return'), 'Independent policy is scoped to external portrait returns'
            assert job['treatment'] in ('npc_portrait_family', 'player_portrait_frames')
            assert all(d['kind'] == 'accepted_treatment_pilot' for d in job['dependencies']), (
                'Page crops and identity/animation seed dependencies cannot be waived')
            return []
        return self.dependency_cells(job)

    def native_identity_sources(self, job):
        if job['treatment'] != 'player_portrait_frames':
            return {}
        seeds = [d['job'] for d in job['dependencies'] if d['kind'] == 'accepted_seed_job'] or [job['id']]
        return {m['id']: m['source_sha256'] for j in seeds for m in self.jobs[j]['members']}

    def native_identity_acceptance(self, job, payload, review):
        """Independent generation still requires a local comparison to the accepted identity seed."""
        if payload.get('dependency_policy') != 'external_portrait_native_identity_first_pass':
            return {}, []
        cells = sorted({m['id'] for d in job['dependencies'] if d['kind'] == 'accepted_seed_job'
                        for m in self.jobs[d['job']]['members']})
        assert all(self.accepted(c) for c in cells), 'Accept and compare the identity seed before staging followers'
        hashes = {c: self.state['cells'][c]['sha256'] for c in cells}
        if hashes:
            assert review.get('identity_seed_cells') == hashes, 'Record the accepted seed hashes reviewed locally'
            assert review.get('identity_seed_review_images'), 'Retain the cross-expression identity comparison'
        return hashes, review.get('identity_seed_review_images', []) if hashes else []

    def validate(self):
        for target in self.targets.values():
            assert digest(native_source(target['source_path'])) == target['source_sha256']
            assert target['x2_size'] == [v * 2 for v in target['native_size']]
            assert self.target_cells[target['id']], f'Unscheduled target: {target["id"]}'
            # Regions must exactly partition the full source canvas, including unused atlas areas.
            rectangles = [self.members[c][1]['source_rect'] for c in self.target_cells[target['id']]]
            width, height = target['native_size']
            assert sum(w * h for _, _, w, h in rectangles) == width * height
            for index, (x, y, w, h) in enumerate(rectangles):
                assert x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height
                for a, b, c, d in rectangles[index + 1:]:
                    assert x + w <= a or a + c <= x or y + h <= b or b + d <= y, 'Overlapping export regions'
        edges = {}
        for job in self.jobs.values():
            assert digest(HERE / job['reference_path']) == job['reference_sha256']
            with Image.open(HERE / job['reference_path']) as image:
                assert list(image.size) == job['reference_size']
            for member in job['members']:
                x, y, w, h = member['reference_cell_rect']
                assert x >= 0 and y >= 0 and x + w <= job['reference_size'][0] and y + h <= job['reference_size'][1]
                assert [w, h] == [v * 2 for v in member['source_rect'][2:]]
            edges[job['id']] = {self.members[c][0] for c in self.dependency_cells(job)}
        resolved = set()
        while len(resolved) < len(edges):
            ready = {j for j, deps in edges.items() if j not in resolved and deps <= resolved}
            assert ready, 'Dependency cycle or missing job'
            resolved.update(ready)
        return dict(targets=len(self.targets), jobs=len(self.jobs), cells=len(self.members),
                    accepted=sum(self.accepted(c) for c in self.members),
                    verified_reused=sum(self.accepted(c) and 'reuse' in self.state['cells'][c] for c in self.members),
                    missing_required=[r['name'] for r in self.manifest['missing_references']
                                      if r['disposition'] == 'missing_required'],
                    generation_calls_made_by_queue=0)

    def payload(self, job_id, repair_note=None, repair_reference=None, detail_reference=None, pair_index=None,
                spell_ink_matte=False, cell_id=None):
        job = self.jobs[job_id]
        assert not self.blockers(job), f'Unaccepted dependencies: {self.blockers(job)}'
        selected_members = job['members']
        if cell_id is not None:
            assert pair_index is None and not spell_ink_matte, 'Do not split spell pairs'
            independent_legacy = (job['treatment'] == 'legacy_ui_art' and len(job['members']) == 1
                                  and all(d['kind'] == 'accepted_treatment_pilot' for d in job['dependencies']))
            assert job['treatment'] in ('fitted_equipment_variants', 'inventory_items') or independent_legacy, (
                'Single-cell selection requires equipment, inventory or an independent legacy cutout')
            selected_members = [m for m in job['members'] if m['id'] == cell_id]
            assert len(selected_members) == 1, 'Cell does not belong to this job'
            assert selected_members[0]['cleanup'] == 'alpha_cutout_or_effect', 'Single cell requires cutout cleanup'
        assert not spell_ink_matte or pair_index is not None, 'Ink matte requires a selected spell pair'
        if pair_index is not None:
            assert job['treatment'] == 'spell_icon_pair', 'Pair selection is only for spell jobs'
            assert 0 <= pair_index < len(job['members']) // 2, 'Invalid spell pair index'
            selected_members = job['members'][pair_index * 2:pair_index * 2 + 2]
        for member in job['members']:
            assert digest(native_source(member['source_path'])) == member['source_sha256'], 'Source changed'
        directory = self.payload_root / job_id
        directory.mkdir(parents=True, exist_ok=True)
        references = [str(HERE / job['reference_path'])]
        reference_roles = {references[0]: 'Native source cells; restore these identities/states and registrations.'}
        full_canvas = (len(job['members']) == 1 and job['members'][0]['cleanup'] == 'opaque_canvas'
                       and job['treatment'] in {'spellbook_page', 'ui_background', 'map_presentation'})
        execution_layout = None
        if pair_index is not None:
            width = sum(m['export_region'][2] for m in selected_members) + 16
            height = max(m['export_region'][3] for m in selected_members)
            sheet = Image.new('RGBA', (width, height), (255, 0, 255, 255))
            rectangles, x = {}, 0
            for m in selected_members:
                w, h = m['export_region'][2:]
                with Image.open(native_source(m['source_path'])) as source:
                    native = rendered(source, self.targets[m['target']]['compositing']['profiles'][0])
                sheet.alpha_composite(native.resize((w, h), Image.Resampling.NEAREST), (x, 0))
                rectangles[m['id']] = [x, 0, w, h]
                x += w + 16
            path = directory / 'native-pair.png'
            sheet.convert('RGB').save(path)
            references = [str(path.resolve())]
            reference_roles = {references[0]: 'Edit target: one native colored/sepia spell pair without labels. '
                'Exact cell geometry; pure magenta denotes native key holes and the 16px separator, not artwork.'}
            execution_layout = dict(canvas_size=[width, height], cell_rects=rectangles)
        if full_canvas:
            member = job['members'][0]
            x, y, w, h = member['source_rect']
            with Image.open(native_source(member['source_path'])) as source:
                canvas = source.convert('RGB').crop((x, y, x + w, y + h)).resize(
                    (w * 2, h * 2), Image.Resampling.NEAREST)
            path = directory / 'native-full-canvas.png'
            canvas.save(path)
            references = [str(path.resolve())]
            reference_roles = {references[0]: 'Edit target: complete native canvas at x2, without sheet labels or '
                'external gutters. Restore detail in place across this exact composition.'}
            execution_layout = dict(canvas_size=[w * 2, h * 2], cell_rects={member['id']: [0, 0, w * 2, h * 2]})
        if job['kind'] == 'imagegen_sheet' and all(
                m['cleanup'] == 'alpha_cutout_or_effect' and m['treatment'] != 'spell_icon_pair'
                for m in job['members']):
            # A label-free source on the requested matte avoids treating title space and colored cell boxes
            # as UI artwork or redistributing the subjects when omitting those labels in the generated result.
            size = selected_members[0]['export_region'][2:] if cell_id is not None else job['reference_size']
            sheet = Image.new('RGBA', tuple(size), (255, 0, 255, 255))
            for member in selected_members:
                x, y, w, h = member['source_rect']
                target = self.targets[member['target']]
                with Image.open(native_source(member['source_path'])) as source:
                    rgba = rendered(source, target['compositing']['profiles'][0]).crop((x, y, x + w, y + h))
                a, b, width, height = member['reference_cell_rect']
                if cell_id is not None:
                    a, b = 0, 0
                    width, height = size
                    execution_layout = dict(canvas_size=list(size), cell_rects={cell_id: [0, 0, width, height]})
                sheet.alpha_composite(rgba.resize((width, height), Image.Resampling.NEAREST), (a, b))
            path = directory / 'native-magenta.png'
            sheet.convert('RGB').save(path)
            references = [str(path.resolve())]
            reference_roles = {references[0]: 'Edit target: native silhouettes at exact sheet coordinates on pure '
                'magenta. Restore details in place; retain this canvas and all empty space. No labels to remove.'}
        dependency_hashes = {c: self.state['cells'][c]['sha256'] for c in self.dependency_cells(job)}
        seed_cells = sorted({m['id'] for d in job['dependencies'] if d['kind'] == 'accepted_seed_job'
                             for m in self.jobs[d['job']]['members']})
        seed_entries = []
        for cell in seed_cells:
            with Image.open(self.state['cells'][cell]['artifact']) as image:
                label = self.targets[self.members[cell][1]['target']]['runtime_name']
                if '--region-' in cell:
                    label += ' ' + cell.rsplit('--', 1)[1]
                seed_entries.append((label, image.copy()))
        reference_layouts = {}
        if seed_entries:
            path = directory / 'accepted-identity-or-sequence-seed.png'
            reference_layouts[str(path)] = reference_contact(seed_entries, path)
            references.append(str(path))
            reference_roles[str(path)] = 'Accepted seed from this same identity, item family or animation sequence.'
        seen = set()
        for member in job['members']:
            if member['context_native'] and member['source_path'] not in seen:
                seen.add(member['source_path'])
                path = directory / (hashlib.sha256(member['source_path'].encode()).hexdigest()[:12] + '-full-native.png')
                with Image.open(native_source(member['source_path'])) as image:
                    image.convert('RGBA').save(path)
                references.append(str(path))
                reference_roles[str(path)] = 'Full native atlas: registered context around each source region.'
        crop_entries, crop_records, crop_keys = [], [], set()
        for dep in job['dependencies']:
            if dep['kind'] != 'accepted_page_crop':
                continue
            if pair_index is not None:
                elements = {d['element'] for m in selected_members
                            for d in self.targets[m['target']]['page_dependencies']}
                if dep['recipe']['element'] not in elements:
                    continue
            cells = self.target_cells[dep['target']]
            assert len(cells) == 1, 'Page reconstruction required before dependent crops'
            x, y, w, h = dep['recipe']['x2_draw_rect']
            crop_key = (dep['target'], dep['recipe']['element'], x, y, w, h)
            if crop_key in crop_keys:
                continue
            crop_keys.add(crop_key)
            padding = dep['recipe']['context_pixels_x2']
            page_path = self.state['cells'][cells[0]]['artifact']
            if page_path not in references:
                references.append(page_path)
                reference_roles[page_path] = 'Accepted full school page; authoritative composition and page pixels.'
            with Image.open(page_path) as page:
                box = (max(0, x - padding), max(0, y - padding),
                       min(page.width, x + w + padding), min(page.height, y + h + padding))
                crop_entries.append((dep['recipe']['element'], page.crop(box)))
            crop_records.append(dict(element=dep['recipe']['element'], page_target=dep['target'],
                page_sha256=self.state['cells'][cells[0]]['sha256'], crop_xyxy=list(box), final_draw_xywh=[x, y, w, h],
                full_page=page_path))
        if crop_entries:
            path = directory / 'accepted-page-crops.png'
            reference_layouts[str(path)] = reference_contact(crop_entries, path)
            references.append(str(path))
            reference_roles[str(path)] = 'One accepted page crop per normal/hover pair, with 16px context.'
        if repair_reference is not None:
            assert repair_note, 'Describe the specific defect when supplying a repair master'
            path = repair_reference.resolve(strict=True)
            with Image.open(path) as image:
                image.verify()
            references.append(str(path))
            reference_roles[str(path)] = ('Previous generated master to edit for the specified defect. Native '
                'reference remains authoritative for identity, lettering and geometry; preserve already correct areas.')
        if detail_reference is not None:
            path = detail_reference.resolve(strict=True)
            with Image.open(path) as image:
                image.verify()
            references.append(str(path))
            reference_roles[str(path)] = ('Native detail reference: inspect the original small features/lettering. '
                                          'Use the full native canvas to determine their position and scale.')
        prompt = job['prompt'] + '\n\n' + registration.PROMPT
        if cell_id is not None:
            subject = ('equipped Might and Magic item variant' if job['treatment'] == 'fitted_equipment_variants'
                       else 'Might and Magic legacy UI icon' if job['treatment'] == 'legacy_ui_art'
                       else 'Might and Magic inventory icon')
            prompt = (f'Faithful x2 restoration of one {subject}. '
                'Edit the supplied single native canvas in place, preserving its design, pose, holes, '
                'attachment points, material colors, margins and internal feature positions. '
                'Restore existing detail without new ornament, texture, highlights or folds. '
                f'Only cell {cell_id} is requested. Output canvas {size[0]}x{size[1]}; '
                'the full native canvas occupies the whole reference, with no sheet gutters or labels.\n\n'
                + registration.PROMPT)
        if pair_index is not None:
            substrate = ('Extract only the restored spell artwork and ink onto uniform pure magenta #FF00FF. '
                'Remove all parchment substrate, including paper between hatch strokes and glyphs. Retain '
                'all intended fine ink, hatching, colored strokes, painted foreground surfaces and '
                'enclosed artwork. No magenta reflection or spill. The accepted page is context for its warm '
                'illumination; it will be composited beneath the cleaned artwork deterministically. Do not '
                'paint parchment or a rectangular panel in this output. '
                if spell_ink_matte else
                'Use the accepted page crop as the exact paper substrate. Do not invent a different parchment '
                'texture or draw a rectangular frame. Keep the same accepted background in both states. ')
            prompt = ('Faithful x2 restoration of one Might and Magic spell colored/sepia pair. Edit the supplied '
                'label-free native pair in place. Preserve its exact drawing, all tiny handwritten glyph strokes, '
                'hatching, color accents and state differences. No new symbols, letters or stronger shadows. '
                'Restore detail without changing geometry or margins. ' + substrate +
                'The native magenta holes and separator must '
                'stay uniform #FF00FF without spill, reflection or checkerboard. '
                f'Output whole canvas {width}x{height}; cell xywh coordinates: {json.dumps(rectangles)}. '
                'Do not redistribute panels or normalize their sizes. Only these two cells are requested.\n\n'
                + registration.PROMPT)
        if full_canvas:
            paragraphs = job['prompt'].split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if paragraph.startswith('Produce one registered sheet'):
                    paragraphs[i] = ('Directly restore the entire supplied image as one full-canvas image, '
                        f'{w * 2}x{h * 2} pixels. Preserve its exact framing, borders and all internal positions. '
                        'There are no sheet labels or external gutters to reproduce or remove.')
                elif paragraph.startswith('Cell 1:'):
                    paragraphs[i] = (f'Target {member["id"]}; native region xywh={member["source_rect"]}; '
                                     f'entire restored canvas xywh=[0, 0, {w * 2}, {h * 2}]; retain opaque artwork.')
            prompt = '\n\n'.join(paragraphs) + '\n\n' + registration.PROMPT
        if repair_note:
            prompt += '\n\nSpecific defects to repair from the reviewed previous attempt:\n' + repair_note
        if job['kind'] == 'imagegen_sheet':
            prompt += ('\n\nRestoration finish requirement: the native pixel grid is a reference for design and '
                       'placement, not the requested rendering style. Reconstruct continuous painted surfaces, '
                       'smooth curved contours and faithful material detail. Do not reproduce source pixels as '
                       'larger square blocks, mosaic patches, stair steps or repeated dot highlights. Mere '
                       'enlargement, blur or a pixel-art redraw is not restored artwork. Preserve deliberate '
                       'painted marks and straight-edged symbols. Detail must survive the final exact x2 export '
                       'without changing the design; raw masters and final cells will both be visually reviewed.')
            cutouts = [m['id'] for m in selected_members if m['cleanup'] == 'alpha_cutout_or_effect'
                       and m['treatment'] != 'spell_icon_pair']
            if cutouts:
                prompt += ('\n\nExtraction matte for these cutout cells: ' + ', '.join(cutouts) + '. '
                           'Use a perfectly uniform opaque pure magenta RGB(255,0,255), #FF00FF, in the empty '
                           'background and holes. Do not simulate transparency with a checkerboard. No background '
                           'gradient, ground shadow, colored bounce, magenta reflection or matte-colored halo. '
                           'Preserve intentional pink/purple foreground materials and soft effects; do not recolor '
                           'them to make extraction easier. Keep their native shape, extent and placement.')
            prompt += ('\n\nRetain the original opaque artwork/background in opaque_canvas cells. '
                       + ('Spell ink-matte output must contain no parchment; assembly will retain accepted page pixels. '
                          if spell_ink_matte else 'Retain the accepted page pixels in spell-icon pairs. ') +
                       'For key_aware_native_format cells preserve each distinct '
                       'native key/index region: do not collapse multiple runtime masks into one magenta key.')
        if dependency_hashes:
            prompt += '\n\nAccepted dependency version hashes:\n' + json.dumps(dependency_hashes, sort_keys=True)
        prompt += '\n\nReference roles:\n' + json.dumps(reference_roles, sort_keys=True)
        if crop_records:
            prompt += '\n\nPage crop registration:\n' + json.dumps(crop_records, sort_keys=True)
        payload = dict(job=job_id, prompt=prompt,
                       layout_sha256=self.state.get('layout_revision', {}).get('sha256'),
                       selected_cells=[m['id'] for m in selected_members],
                       spell_ink_matte=spell_ink_matte,
                       execution_layout=execution_layout,
                       repair_note=repair_note,
                       cleanup_instructions='Follow MATTE_AND_FITTING.md: inspect raw matte, soft alpha extraction, '
                           'local edge RGB unmixing, residual contour audit before and after premultiplied resizing; '
                           'protect intentional pink/purple materials, thin details and glows. Retain cleanup '
                           'parameters and light/dark edge evidence. Use compare before visual acceptance.',
                       dependency_cells=dependency_hashes,
                       reference_roles=reference_roles, reference_layouts=reference_layouts, page_crops=crop_records,
                       reference_hashes={p: digest(Path(p)) for p in references},
                       instruction='Inspect references and review checks. This payload does not authorize generation; '
                                   'submit only when the user has requested the restoration phase.')
        if job['kind'] == 'imagegen_sheet':
            payload['tool_args'] = dict(prompt=prompt, referenced_image_paths=references)
        else:
            payload['deterministic_references'] = references
            payload['instruction'] = 'Deterministic font-region job. Follow the prompt; do not submit to imagegen.'
        save(directory / 'payload.json', payload)
        (directory / 'submitted_prompt.txt').write_text(prompt)
        return payload

    def pending_work(self, phase='first-pass'):
        """Keep failed cells out of fresh scheduling; retain cell-level attempt scope across batches."""
        attempted = {}
        attempted_payloads = {}
        for attempt in self.state['attempts']:
            payload = json.loads(Path(attempt['payload']).read_text())
            for cell in payload.get('selected_cells', [m['id'] for m in self.jobs[attempt['job']]['members']]):
                attempted[cell] = attempt
                attempted_payloads[cell] = payload
        result = []
        for job in self.jobs.values():
            blocked = self.blockers(job)
            if job['id'] in self.state.get('claims', {}):
                continue
            selected, details = [], []
            for member in job['members']:
                cell = member['id']
                if member['target'] in self.state.get('retired_targets', {}):
                    continue
                if blocked:
                    payload = attempted_payloads.get(cell, {})
                    if payload.get('dependency_policy') not in ('independent_external_portrait_first_pass',
                                                               'external_portrait_native_identity_first_pass'):
                        continue
                    if any(not self.accepted(c) for c in self.generation_dependencies(job, payload)):
                        continue
                if self.accepted(cell):
                    continue
                if self.state.get('external_assignments', {}).get(cell, {}).get('status') == 'assigned':
                    continue
                state = self.state['cells'].get(cell, {})
                deferred = state.get('status') == 'deferred'
                wanted = (phase == 'retry' and deferred or
                          phase == 'review' and cell in attempted and not deferred or
                          phase == 'first-pass' and cell not in attempted and not deferred)
                if not wanted:
                    continue
                selected.append(cell)
                if cell in attempted or deferred:
                    attempt = attempted.get(cell, {})
                    details.append(dict(cell=cell, reason=state.get('reason'),
                                        attempt=attempt.get('id'), retained_raw=attempt.get('raw')))
            if selected:
                result.append(dict(id=job['id'], cells=len(selected), selected_cells=selected,
                    treatment=job['treatment'], pilot=job['pilot'],
                    next_action={'first-pass': job['kind'], 'review': 'review_retained_master',
                                 'retry': 'inspect_deferred_for_retry_batch'}[phase], details=details))
        return result

    def batch_payload(self, cells):
        """Prepare one small-item execution sheet without rewriting frozen jobs or accepted state."""
        assert 1 <= len(cells) <= 9 and len(set(cells)) == len(cells), 'Select 1–9 distinct cells'
        members = [self.members[c][1] for c in cells]
        jobs = sorted({self.members[c][0] for c in cells})
        assert all(m['treatment'] == 'inventory_items' and m['cleanup'] == 'alpha_cutout_or_effect'
                   for m in members), 'Batch command currently supports inventory cutouts only'
        assert all(max(m['export_region'][2:]) <= 192 for m in members), 'Large art needs a smaller native job'
        areas = [m['export_region'][2] * m['export_region'][3] for m in members]
        assert max(areas) <= 4 * min(areas), 'Batch similarly sized artwork'
        assert len({self.targets[m['target']]['namespace'] for m in members}) == 1, 'Keep namespace contracts together'
        assert all(self.targets[m['target']]['compositing']['profiles'] == ['item'] for m in members), (
            'Mixed consumer/key profiles require their native workflow')
        assert len({tuple(self.dependency_cells(self.jobs[j])) for j in jobs}) == 1, (
            'Batch only jobs with identical dependency contracts')
        assert all(d['kind'] == 'accepted_treatment_pilot' for j in jobs for d in self.jobs[j]['dependencies']), (
            'Seed-dependent artwork needs its native workflow')
        assert len({m['source_sha256'] for m in members}) == len(members), 'Do not generate identical source siblings'
        for cell in cells:
            assert not self.accepted(cell), 'Preserve accepted artwork'
        for job_id in jobs:
            assert not self.blockers(self.jobs[job_id]), 'Dependencies must be accepted first'
        # A fresh immutable execution ID also permits targeted retries without replacing submitted payloads.
        batch_id = 'batch-' + uuid.uuid4().hex
        directory = self.payload_root / batch_id
        directory.mkdir(parents=True)
        edge = max(320, 2 * max(max(m['export_region'][2:]) for m in members) + 16)
        sheet = Image.new('RGBA', (3 * edge, 3 * edge), (255, 0, 255, 255))
        rectangles, slots, dependencies = {}, {}, {}
        for i, member in enumerate(members):
            source = native_source(member['source_path'])
            assert digest(source) == member['source_sha256'], 'Source changed'
            x, y, w, h = member['source_rect']
            with Image.open(source) as image:
                native = rendered(image, 'item').crop((x, y, x + w, y + h))
            width, height = w * 4, h * 4
            a, b = i % 3 * edge, i // 3 * edge
            left, top = a + (edge - width) // 2, b + (edge - height) // 2
            sheet.alpha_composite(native.resize((width, height), Image.Resampling.NEAREST), (left, top))
            rectangles[member['id']] = [left, top, width, height]
            slots[member['id']] = [a, b, edge, edge]
            for dependency in self.dependency_cells(self.jobs[self.members[member['id']][0]]):
                dependencies[dependency] = self.state['cells'][dependency]['sha256']
        path = directory / 'reference.png'
        sheet.convert('RGB').save(path)
        prompt = ('Faithfully restore this Might and Magic inventory sheet in place. Exactly 3 columns and 3 rows; '
                  'one item per occupied cell, unused cells empty. Preserve each original full-canvas position, '
                  'scale, silhouette, holes, orientation, subdued colors, symbols and ornament. No new details or '
                  'stronger shine. Produce smooth continuous painted materials and refined faithful contours, not '
                  'enlarged pixel blocks, mosaics, stair steps, dot highlights, blur or a pixel-art redraw. '
                  'All empty space and genuine holes must be opaque pure magenta RGB(255,0,255), #FF00FF. '
                  'No checkerboard, labels, borders, gradients, shadows or magenta spill; protect real purple art. '
                  'Keep the exact grid composition and enough real detail for each own-native x2 export. '
                  'Render a 1920x1920 master. Do not shrink objects into filler. '
                  'Occupied cells in row-major order: ' + ', '.join(cells) + '. '
                  'Review every raw cell and final x2 export for design, internal geometry and clean edges.')
        payload = dict(job=jobs[0], jobs=jobs, batch_id=batch_id, selected_cells=cells, prompt=prompt,
                       layout_sha256=self.state.get('layout_revision', {}).get('sha256'),
                       dependency_cells=dependencies, source_hashes={m['id']: m['source_sha256'] for m in members},
                       execution_layout=dict(canvas_size=list(sheet.size), cell_rects=rectangles, slot_rects=slots),
                       reference_hashes={str(path): digest(path)},
                       tool_args=dict(prompt=prompt, referenced_image_paths=[str(path)]))
        save(directory / 'payload.json', payload)
        (directory / 'submitted_prompt.txt').write_text(prompt)
        return payload

    def record(self, job_id, raw_path):
        payload_path = self.payload_root / job_id / 'payload.json'
        assert payload_path.is_file(), 'Prepare and submit the exact payload before recording its returned master'
        payload = json.loads(payload_path.read_text())
        jobs = payload.get('jobs', [job_id])
        if payload.get('dependency_policy') == 'user_authorized_native_first_pass_review_later':
            # Retaining an explicitly authorized native-reference result does not accept its dependencies.
            assert payload.get('external_return') and payload.get('selected_cells')
            assert set(payload['selected_cells']) == set(payload['source_hashes'])
            assert payload.get('unresolved_acceptance_dependencies') is not None
            for reference in payload.get('native_family_sources', []):
                assert digest(Path(reference['source'])) == reference['sha256'], 'Native family reference changed'
        else:
            for source_job in jobs:
                assert all(self.accepted(c) for c in self.generation_dependencies(self.jobs[source_job], payload))
        for cell, sha in payload.get('source_hashes', {}).items():
            assert digest(native_source(self.members[cell][1]['source_path'])) == sha, 'Submitted source changed'
        for path, sha in payload['reference_hashes'].items():
            assert digest(Path(path)) == sha, 'Submitted reference changed'
        with Image.open(raw_path) as image:
            image.verify()
        attempt_id = uuid.uuid4().hex
        directory = self.state_path.parent / 'attempts' / attempt_id
        directory.mkdir(parents=True)
        master = directory / ('raw' + raw_path.suffix.lower())
        shutil.copy2(raw_path, master)
        retained = {}
        for i, (reference, sha) in enumerate(payload['reference_hashes'].items()):
            snapshot = directory / (f'reference-{i:02d}' + Path(reference).suffix.lower())
            shutil.copy2(reference, snapshot)
            retained[reference] = dict(path=str(snapshot.resolve()), sha256=sha)
        payload['retained_references'] = retained
        save(directory / 'payload.json', payload)
        (directory / 'submitted_prompt.txt').write_text(payload['prompt'])
        self.state['attempts'].append(dict(id=attempt_id, job=payload['job'], jobs=jobs,
                                          raw=str(master.resolve()), sha256=digest(master),
                                          payload=str((directory / 'payload.json').resolve())))
        for source_job in jobs:
            self.state.setdefault('claims', {}).pop(source_job, None)
        save(self.state_path, self.state)
        return dict(attempt=attempt_id, retained_raw=str(master))

    def accept(self, cell, artifact, review, attempt_id):
        assert self.members[cell][1]['target'] not in self.state.get('user_excluded_targets', {}), 'User excluded target'
        assert self.members[cell][1]['target'] not in self.state.get('retired_targets', {}), 'Retired unused target'
        assert not self.accepted(cell), 'This cell is already accepted; preserve it while repairing siblings'
        job_id, member = self.members[cell]
        attempt = next(a for a in self.state['attempts']
                       if a['id'] == attempt_id and job_id in a.get('jobs', [a['job']]))
        assert digest(Path(attempt['raw'])) == attempt['sha256'], 'Raw master changed'
        payload = json.loads(Path(attempt['payload']).read_text())
        assert cell in payload.get('selected_cells', [m['id'] for m in self.jobs[job_id]['members']]), (
            'This cell was not submitted in the selected attempt')
        dependency_cells = self.generation_dependencies(self.jobs[job_id], payload)
        assert all(self.accepted(c) for c in dependency_cells), 'Dependencies not accepted'
        identity_dependencies, identity_evidence = self.native_identity_acceptance(self.jobs[job_id], payload, review)
        with Image.open(artifact) as image:
            assert list(image.size) == member['export_region'][2:], 'Incorrect exact x2 region size'
        required = ['identity', 'registration', 'compositing', 'detail_at_x2', 'state_or_animation_consistency']
        assert all(review.get(k) is True for k in required), 'Every visual acceptance check must pass'
        assert review.get('notes') and review.get('registration_record') and review.get('review_images')
        evidence = [review['registration_record'], *review['review_images'], *identity_evidence]
        layout_hash = self.layout_hash(cell)
        if layout_hash and payload.get('layout_sha256') != layout_hash:
            # Reusing reviewed ink is deterministic assembly, never another imagegen attempt.
            assert payload.get('spell_ink_matte'), 'Changed layout requires new generation or retained ink assembly'
            assembly_path = Path(review['reassembly_record'])
            assembly = json.loads(assembly_path.read_text())
            assert assembly['layout_sha256'] == layout_hash and assembly['attempt'] == attempt_id
            assert assembly['cell'] == cell and assembly['artifact_sha256'] == digest(artifact)
            assert assembly['final_draw_xywh'] == self.targets[member['target']]['page_dependencies'][0]['x2_draw_rect']
            assert assembly['page_sha256'] == payload['page_crops'][0]['page_sha256']
            evidence.append(str(assembly_path))
            for name, sha in assembly['evidence_hashes'].items():
                assert digest(Path(name)) == sha, 'Reassembly source/evidence changed'
                evidence.append(name)
        assert all(Path(p).is_file() for p in evidence), 'Missing registration or visual review evidence'
        comparisons = registration.validate(member, self.targets[member['target']], artifact,
                                            Path(review['registration_record']))
        assert set(comparisons) <= set(review['review_images']), 'Review every registration comparison'
        current_dependencies = {c: self.state['cells'][c]['sha256'] for c in dependency_cells}
        assert payload['dependency_cells'] == current_dependencies, 'Generation used stale dependencies'
        current_dependencies.update(identity_dependencies)
        export = self.storage_root() / 'accepted' / (cell + artifact.suffix.lower())
        export.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, export)
        self.state['cells'][cell] = dict(status='accepted', attempt=attempt_id, artifact=str(export.resolve()),
            sha256=digest(export), review=review, evidence_hashes={p: digest(Path(p)) for p in evidence},
            dependency_cells=current_dependencies, layout_sha256=layout_hash)
        save(self.state_path, self.state)
        return dict(cell=cell, accepted=True)

    def reuse(self, cell, donor, review):
        """Copy reviewed identical full-canvas art, retaining each target's own runtime identity and placement."""
        assert cell != donor and not self.accepted(cell), 'Preserve accepted cells'
        assert self.accepted(donor), 'Reuse requires a currently accepted donor'
        job_id, member = self.members[cell]
        donor_job_id, donor_member = self.members[donor]
        same_job = job_id == donor_job_id
        target = self.targets[member['target']]
        donor_target = self.targets[donor_member['target']]
        for m, t in ((member, target), (donor_member, donor_target)):
            assert self.target_cells[t['id']] == [m['id']], 'Reuse only complete single-cell canvases'
            assert m['source_rect'] == [0, 0, *t['native_size']]
            assert m['export_region'] == [0, 0, *t['x2_size']]
            assert m['source_sha256'] == t['source_sha256']
            assert digest(native_source(m['source_path'])) == m['source_sha256'], 'Reuse source changed'
            assert not t.get('page_dependencies'), 'Page-backed art needs its own page assembly'
            for dependency in self.jobs[self.members[m['id']][0]]['dependencies']:
                same_seed = (m['id'] == cell and dependency['kind'] == 'accepted_seed_job'
                             and dependency.get('job') == donor_job_id)
                shared_seed = same_job and dependency['kind'] == 'accepted_seed_job'
                assert dependency['kind'] == 'accepted_treatment_pilot' or same_seed or shared_seed, (
                    'Reuse requires independent art, an exact seed donor or same-job seed dependencies')
        for key in ('source_sha256', 'namespace', 'native_size', 'x2_size', 'treatment', 'logical_canvas',
                    'placement', 'frame', 'native_palette_sha256', 'native_rgba_sha256', 'compositing'):
            assert target[key] == donor_target[key], f'Incompatible reuse contract: {key}'
        for key in ('source_rect', 'export_region', 'method', 'cleanup'):
            assert member[key] == donor_member[key], f'Incompatible reuse cell: {key}'
        assert not self.blockers(self.jobs[job_id]), 'Dependencies not accepted'
        if same_job:
            donor_dependencies = self.state['cells'][donor].get('dependency_cells', {})
            for dependency in self.dependency_cells(self.jobs[job_id]):
                assert donor_dependencies.get(dependency) == self.state['cells'][dependency]['sha256'], (
                    'Same-job donor must record every current shared dependency')
        assert review.get('consumer_contract_notes'), 'Review both consumers and preserve destination placement'
        required = ['identity', 'registration', 'compositing', 'detail_at_x2', 'state_or_animation_consistency']
        assert all(review.get(k) is True for k in required), 'Every visual acceptance check must pass'
        assert review.get('notes') and review.get('registration_record') and review.get('review_images')
        artifact = Path(self.state['cells'][donor]['artifact'])
        assert artifact.suffix.lower() == Path(target['output_path']).suffix.lower(), 'Output format differs'
        comparisons = registration.validate(member, target, artifact, Path(review['registration_record']))
        assert set(comparisons) <= set(review['review_images']), 'Review every destination comparison'
        evidence = [review['registration_record'], *review['review_images'],
                    str(native_source(member['source_path'])), str(native_source(donor_member['source_path']))]
        assert all(Path(p).is_file() for p in evidence), 'Missing reuse evidence'
        dependencies = {c: self.state['cells'][c]['sha256'] for c in self.dependency_cells(self.jobs[job_id])}
        assert cell not in self.state['cells'][donor].get('dependency_cells', {}), 'Cyclic reuse'
        dependencies[donor] = digest(artifact)
        export = self.storage_root() / 'accepted' / (cell + artifact.suffix.lower())
        export.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, export)
        provenance = dict(donor_cell=donor, donor_sha256=digest(artifact),
                          source_sha256=target['source_sha256'], kind='verified_identical_full_canvas')
        self.state['cells'][cell] = dict(status='accepted', reuse=provenance, artifact=str(export.resolve()),
            sha256=digest(export), review=review, evidence_hashes={p: digest(Path(p)) for p in evidence},
            dependency_cells=dependencies, layout_sha256=self.layout_hash(cell))
        save(self.state_path, self.state)
        return dict(cell=cell, accepted=True, reuse=provenance)

    def reconstruct(self, target_id):
        target = self.targets[target_id]
        cells = self.target_cells[target_id]
        assert all(self.accepted(c) for c in cells), 'Every constituent cell must be accepted first'
        destination = self.storage_root() / 'reconstructed' / target['namespace'] / Path(target['output_path']).name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if len(cells) == 1:
            source = Path(self.state['cells'][cells[0]]['artifact'])
            assert source.suffix.lower() == destination.suffix.lower(), 'Export in the manifest-selected format first'
            shutil.copy2(source, destination)
        else:
            assert target['treatment'] == 'registered_arcomage_atlas'
            with Image.open(native_source(target['source_path'])) as source:
                assert source.mode == 'RGB', 'This atlas reconstruction is for the audited RGB Arcomage source'
            canvas = Image.new('RGB', target['x2_size'])
            for cell in cells:
                x, y, width, height = self.members[cell][1]['export_region']
                with Image.open(self.state['cells'][cell]['artifact']) as region:
                    assert list(region.size) == [width, height]
                    assert region.convert('RGBA').getchannel('A').getextrema() == (255, 255), (
                        'Retain native RGB keys for multi-profile atlas regions; do not flatten them to an alpha mask')
                    canvas.paste(region.convert('RGB'), (x, y))
            canvas.save(destination)
        with Image.open(destination) as image:
            assert list(image.size) == target['x2_size']
        record = dict(target=target_id, path=str(destination.resolve()), sha256=digest(destination),
                      size=target['x2_size'], cells={c: self.state['cells'][c]['sha256'] for c in cells},
                      status='reconstructed_awaiting_full_canvas_review')
        self.state.setdefault('reconstructed_targets', {})[target_id] = record
        save(self.state_path, self.state)
        return record

    def stage(self, target_id, review):
        """Stage a reviewed complete canvas under the frozen output path; never install into runtime roots."""
        assert target_id not in self.state.get('user_excluded_targets', {}), 'User excluded target'
        assert target_id not in self.state.get('retired_targets', {}), 'Retired unused target'
        target = self.targets[target_id]
        reconstruction = self.state.get('reconstructed_targets', {}).get(target_id)
        assert reconstruction, 'Reconstruct the complete canvas before staging'
        source = Path(reconstruction['path'])
        assert source.is_file() and digest(source) == reconstruction['sha256'], 'Reconstructed canvas changed'
        assert all(self.accepted(c) and self.state['cells'][c]['sha256'] == sha
                   for c, sha in reconstruction['cells'].items()), 'Reconstruction uses stale cells'
        assert set(reconstruction['cells']) == set(self.target_cells[target_id]), 'Incomplete reconstruction'
        assert review.get('full_canvas_review') is True and review.get('notes'), 'Full canvas visual review required'
        assert review.get('artifact_sha256') == reconstruction['sha256'], 'Review must identify the exact canvas'
        evidence = review.get('review_images', [])
        assert evidence and all(Path(p).is_file() for p in evidence), 'Missing full-canvas visual evidence'
        with Image.open(source) as image:
            assert list(image.size) == target['x2_size'], 'Incorrect full x2 export size'
        relative = (ROOT / target['output_path']).resolve().relative_to((HERE / 'exports').resolve())
        export_root = HERE / 'exports' if self.state_path.parent == HERE / 'checkpoint' else self.state_path.parent / 'exports'
        if self.state.get('layout_revision'):
            export_root = self.storage_root() / 'exports'
        destination = export_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            assert digest(destination) == reconstruction['sha256'], 'Preserve existing staged art; reconcile explicitly'
        else:
            shutil.copy2(source, destination)
        record = dict(target=target_id, source_path=target['source_path'], source_sha256=target['source_sha256'],
                      artifact=str(destination.resolve()), sha256=digest(destination), native_size=target['native_size'],
                      x2_size=target['x2_size'], runtime_output_path=target['runtime_output_path'],
                      cells=reconstruction['cells'], review=review, evidence_hashes={p: digest(Path(p)) for p in evidence},
                      status='staged_for_isolated_preview_not_installed')
        record['reuse'] = {c: self.state['cells'][c]['reuse'] for c in reconstruction['cells']
                           if 'reuse' in self.state['cells'][c]}
        self.state.setdefault('staged_targets', {})[target_id] = record
        save(self.state_path, self.state)
        save(export_root / 'manifest.json', dict(targets=list(self.state['staged_targets'].values())))
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, help='Separate checkpoint, primarily for isolated queue tests')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    next_parser = sub.add_parser('next')
    next_parser.add_argument('--limit', type=int, default=3)
    next_parser.add_argument('--phase', choices=['first-pass', 'review', 'retry'], default='first-pass',
                             help='Default: fresh cells only. Review retained sheets separately; retry failures later.')
    sub.add_parser('show').add_argument('job')
    sub.add_parser('batch-payload', help='Prepare up to nine small inventory cells across frozen jobs').add_argument(
        'cells', nargs='+')
    payload = sub.add_parser('payload')
    payload.add_argument('job')
    payload.add_argument('--repair-note', help='Specific observed defects; retained in the exact submitted prompt')
    payload.add_argument('--repair-reference', type=Path, help='Previous master to repair, supplied with native references')
    payload.add_argument('--detail-reference', type=Path, help='Inspected native detail crop for ambiguous small features')
    payload.add_argument('--pair-index', type=int, help='Zero-based spell pair to retry without resubmitting siblings')
    payload.add_argument('--cell', help='One equipment or inventory cutout to restore without resubmitting siblings')
    payload.add_argument('--spell-ink-matte', action='store_true', help='Extract spell art on magenta for exact page assembly')
    sub.add_parser('target').add_argument('target')
    sub.add_parser('reconstruct').add_argument('target')
    stage = sub.add_parser('stage', help='Stage a reviewed reconstructed canvas; never modify runtime assets')
    stage.add_argument('target')
    stage.add_argument('--review', type=Path, required=True)
    claim = sub.add_parser('claim')
    claim.add_argument('job')
    claim.add_argument('--note', required=True, help='Worker/run identification or explicit retry reason')
    release = sub.add_parser('release')
    release.add_argument('job')
    release.add_argument('--reason', required=True, help='Evidence that submission finished/failed; never expire by age')
    record = sub.add_parser('record')
    record.add_argument('job')
    record.add_argument('--raw', type=Path, required=True)
    accept = sub.add_parser('accept')
    accept.add_argument('cell')
    accept.add_argument('--artifact', type=Path, required=True)
    accept.add_argument('--review', type=Path, required=True)
    accept.add_argument('--attempt', required=True)
    reuse = sub.add_parser('reuse', help='Review and copy accepted art from a verified identical full native canvas')
    reuse.add_argument('cell')
    reuse.add_argument('--donor', required=True)
    reuse.add_argument('--review', type=Path, required=True)
    compare = sub.add_parser('compare', help='Measure fitting and produce unapproved visual registration evidence')
    compare.add_argument('cell')
    compare.add_argument('--artifact', type=Path, required=True)
    compare.add_argument('--output-dir', type=Path, required=True)
    reject = sub.add_parser('defer')
    reject.add_argument('cell')
    reject.add_argument('--reason', required=True)
    args = parser.parse_args()
    if args.command in {'payload', 'batch-payload', 'claim', 'release', 'record', 'accept', 'reuse', 'defer',
                        'reconstruct', 'stage'}:
        state_path = args.state or HERE / 'checkpoint/state.json'
        state_path.parent.mkdir(parents=True, exist_ok=True)
        # Keep this descriptor alive through read-modify-write; atomic replacement alone loses concurrent updates.
        state_lock = state_path.with_suffix('.lock').open('a')
        fcntl.flock(state_lock, fcntl.LOCK_EX)
    queue = Queue(args.state)
    if args.command == 'validate':
        output = queue.validate()
    elif args.command == 'next':
        output = queue.pending_work(args.phase)[:args.limit]
    elif args.command == 'show':
        output = dict(**queue.jobs[args.job], blockers=queue.blockers(queue.jobs[args.job]))
    elif args.command == 'target':
        output = queue.targets[args.target]
    elif args.command == 'reconstruct':
        output = queue.reconstruct(args.target)
    elif args.command == 'stage':
        output = queue.stage(args.target, json.loads(args.review.read_text()))
    elif args.command == 'payload':
        output = queue.payload(args.job, args.repair_note, args.repair_reference, args.detail_reference,
                               args.pair_index, args.spell_ink_matte, args.cell)
    elif args.command == 'batch-payload':
        output = queue.batch_payload(args.cells)
    elif args.command == 'record':
        output = queue.record(args.job, args.raw)
    elif args.command == 'accept':
        output = queue.accept(args.cell, args.artifact, json.loads(args.review.read_text()), args.attempt)
    elif args.command == 'reuse':
        output = queue.reuse(args.cell, args.donor, json.loads(args.review.read_text()))
    elif args.command == 'compare':
        member = queue.members[args.cell][1]
        output = registration.evidence(member, queue.targets[member['target']], args.artifact, args.output_dir)
    elif args.command == 'claim':
        assert args.job in queue.jobs and not queue.blockers(queue.jobs[args.job])
        claims = queue.state.setdefault('claims', {})
        assert args.job not in claims, 'Already claimed; inspect the existing operation before resubmitting'
        claims[args.job] = dict(note=args.note, state='claimed',
                               warning='A claim is bookkeeping, not proof of a live external process/tool call.')
        save(queue.state_path, queue.state)
        output = claims[args.job]
    elif args.command == 'release':
        claim = queue.state.setdefault('claims', {}).pop(args.job)
        queue.state.setdefault('released_claims', []).append(dict(job=args.job, claim=claim, reason=args.reason))
        save(queue.state_path, queue.state)
        output = dict(job=args.job, released=True)
    else:
        assert args.cell in queue.members
        assert not queue.accepted(args.cell), 'Defer only failed/pending cells; accepted siblings remain intact'
        queue.state['cells'][args.cell] = dict(status='deferred', reason=args.reason)
        save(queue.state_path, queue.state)
        output = queue.state['cells'][args.cell]
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
