"""Focused preparation checks; test artifacts stay in TemporaryDirectory, never the real queue."""
import collections
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops
import numpy as np

from finalize_classification import HERE, digest, read
from freeze_targets import rendered, spell_crops, frame_metadata
from prepare_queue import layout, parts, family
import native_metadata
import registration

spec = importlib.util.spec_from_file_location('hud_queue', HERE / 'queue.py')
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)


class PreparationTests(unittest.TestCase):
    def test_native_identity_first_pass_requires_context_and_local_seed_review(self):
        q = queue_module.Queue.__new__(queue_module.Queue)
        seed = dict(id='seed', treatment='player_portrait_frames', dependencies=[],
                    members=[dict(id='seed-face', source_sha256='native-hash')])
        follower = dict(id='follower', treatment='player_portrait_frames',
                        dependencies=[dict(kind='accepted_seed_job', job='seed')])
        q.jobs = dict(seed=seed, follower=follower)
        payload = dict(dependency_policy='external_portrait_native_identity_first_pass',
                       external_return=dict(bundle='test'), native_identity_sources={'seed-face': 'native-hash'})
        self.assertEqual(q.generation_dependencies(follower, payload), [])
        self.assertEqual(q.generation_dependencies(seed, payload), [])
        with self.assertRaises(AssertionError):
            q.generation_dependencies(follower, dict(payload, native_identity_sources={}))
        with self.assertRaises(AssertionError):
            q.generation_dependencies(dict(follower, dependencies=[dict(kind='accepted_page_crop')]), payload)
        q.accepted = lambda cell: False
        with self.assertRaises(AssertionError):
            q.native_identity_acceptance(follower, payload, {})
        q.accepted = lambda cell: True
        q.state = dict(cells={'seed-face': dict(sha256='accepted-hash')})
        with self.assertRaises(AssertionError):
            q.native_identity_acceptance(follower, payload, {})
        review = dict(identity_seed_cells={'seed-face': 'accepted-hash'}, identity_seed_review_images=['compare.png'])
        self.assertEqual(q.native_identity_acceptance(follower, payload, review),
                         ({'seed-face': 'accepted-hash'}, ['compare.png']))
        self.assertEqual(q.native_identity_acceptance(seed, payload, {}), ({}, []))

    def test_independent_return_reaches_review_without_style_pilot(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = Path(directory) / 'payload.json'
            payload.write_text(json.dumps(dict(selected_cells=['face'],
                dependency_policy='independent_external_portrait_first_pass', external_return=dict(bundle='test'))))
            q = queue_module.Queue.__new__(queue_module.Queue)
            q.jobs = {'npc': dict(id='npc', kind='imagegen_sheet', treatment='npc_portrait_family', pilot=False,
                members=[dict(id='face')], dependencies=[dict(kind='accepted_treatment_pilot', job='pilot')])}
            q.state = dict(cells={}, attempts=[dict(id='attempt', job='npc', payload=str(payload), raw='raw.png')],
                           external_assignments={'face': dict(status='returned')})
            q.blockers = lambda job: ['missing-style-pilot']
            self.assertEqual(q.pending_work('review')[0]['selected_cells'], ['face'])
            self.assertEqual(q.pending_work('first-pass'), [])

    def test_external_portrait_first_pass_waives_only_style_pilot_generation_dependencies(self):
        q = queue_module.Queue.__new__(queue_module.Queue)
        q.jobs = {'pilot': dict(members=[dict(id='pilot-face')])}
        job = dict(treatment='npc_portrait_family',
                   dependencies=[dict(kind='accepted_treatment_pilot', job='pilot')])
        external = dict(dependency_policy='independent_external_portrait_first_pass',
                        external_return=dict(bundle='restoration_200_015'))
        self.assertEqual(q.generation_dependencies(job, {}), ['pilot-face'])
        self.assertEqual(q.generation_dependencies(job, external), [])
        for kind in ('accepted_seed_job', 'accepted_page_crop'):
            dependent = dict(treatment='player_portrait_frames', dependencies=[dict(kind=kind, job='pilot')])
            with self.assertRaises(AssertionError):
                q.generation_dependencies(dependent, external)
        with self.assertRaises(AssertionError):
            q.generation_dependencies(dict(treatment='spell_icon_pair', dependencies=[]), external)
        with self.assertRaises(AssertionError):
            q.generation_dependencies(job, dict(dependency_policy=external['dependency_policy']))

    def test_external_assignment_skips_only_assigned_cells_until_released(self):
        with tempfile.TemporaryDirectory() as directory:
            q = queue_module.Queue(Path(directory) / 'state.json')
            job = q.jobs['inventory_items-ddfa61bc2549']
            job['dependencies'] = []
            cells = [member['id'] for member in job['members']]
            q.state['external_assignments'] = {cells[0]: dict(status='assigned', bundle='test')}
            fresh = next(row for row in q.pending_work() if row['id'] == job['id'])
            self.assertEqual(fresh['selected_cells'], cells[1:])
            self.assertFalse(q.accepted(cells[0]))
            q.state['external_assignments'][cells[0]]['status'] = 'returned'
            fresh = next(row for row in q.pending_work() if row['id'] == job['id'])
            self.assertEqual(fresh['selected_cells'], cells)

    def test_first_pass_excludes_deferred_and_only_submitted_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            q = queue_module.Queue(Path(directory) / 'state.json')
            job = q.jobs['inventory_items-ddfa61bc2549']
            job['dependencies'] = []
            cells = [m['id'] for m in job['members']]
            payload = Path(directory) / 'attempt.json'
            payload.write_text(json.dumps(dict(selected_cells=cells[:2])))
            q.state['attempts'] = [dict(id='one-call', job=job['id'], payload=str(payload), raw='retained.png')]
            q.state['cells'][cells[0]] = dict(status='deferred', reason='Gem shifted')
            fresh = next(r for r in q.pending_work() if r['id'] == job['id'])
            self.assertEqual(fresh['selected_cells'], cells[2:])
            review = next(r for r in q.pending_work('review') if r['id'] == job['id'])
            self.assertEqual(review['selected_cells'], [cells[1]])
            retry = next(r for r in q.pending_work('retry') if r['id'] == job['id'])
            self.assertEqual(retry['selected_cells'], [cells[0]])
            self.assertEqual(retry['details'][0]['reason'], 'Gem shifted')
            self.assertEqual(retry['details'][0]['attempt'], 'one-call')

    def test_nine_item_batch_retains_cross_job_scope_and_rejects_large_art(self):
        with tempfile.TemporaryDirectory() as directory:
            q = queue_module.Queue(Path(directory) / 'state.json')
            cells = ['engine--icons--' + n + '.bmp' for n in
                     ['6helm3', '6helm4', '6helm5', *[f'7item{i:03}' for i in range(89, 95)]]]
            for cell in cells:
                q.jobs[q.members[cell][0]]['dependencies'] = []
            payload = q.batch_payload(cells)
            self.assertEqual(len(payload['jobs']), 3)
            self.assertEqual(payload['selected_cells'], cells)
            self.assertEqual(payload['execution_layout']['canvas_size'], [960, 960])
            self.assertEqual(len(payload['execution_layout']['slot_rects']), 9)
            raw = Path(directory) / 'raw.png'
            Image.new('RGB', (1254, 1254), 'magenta').save(raw)
            result = q.record(payload['batch_id'], raw)
            self.assertEqual(len(q.state['attempts']), 1)  # One call, not three frozen-job attempts.
            self.assertEqual(q.state['attempts'][0]['jobs'], payload['jobs'])
            # A selected cell from a non-primary job reaches normal visual validation.
            cell = cells[-1]
            artifact = Path(directory) / 'cell.png'
            Image.new('RGBA', tuple(q.members[cell][1]['export_region'][2:])).save(artifact)
            with self.assertRaisesRegex(AssertionError, 'Every visual acceptance'):
                q.accept(cell, artifact, {}, result['attempt'])
            sibling = 'engine--icons--7item095.bmp'
            with self.assertRaisesRegex(AssertionError, 'not submitted'):
                q.accept(sibling, artifact, {}, result['attempt'])
            with self.assertRaisesRegex(AssertionError, 'distinct cells'):
                q.batch_payload(cells + [cells[0]])
            q.members[cells[0]][1]['export_region'][2] = 300
            with self.assertRaisesRegex(AssertionError, 'Large art'):
                q.batch_payload(cells)

    def test_single_inventory_payload_keeps_native_holes_and_excludes_siblings(self):
        with tempfile.TemporaryDirectory() as directory:
            q = queue_module.Queue(Path(directory) / 'state.json')
            job_id = 'inventory_items-cd4ee5a81623'
            q.jobs[job_id]['dependencies'] = []
            cell = 'engine--icons--7item134.bmp'
            payload = q.payload(job_id, cell_id=cell)
            self.assertEqual(payload['selected_cells'], [cell])
            self.assertEqual(payload['execution_layout'], dict(canvas_size=[66, 72],
                             cell_rects={cell: [0, 0, 66, 72]}))
            source = rendered(Image.open(HERE.parents[2] / q.members[cell][1]['source_path']), 'item')
            expected = Image.new('RGBA', (66, 72), (255, 0, 255, 255))
            expected.alpha_composite(source.resize((66, 72), Image.Resampling.NEAREST))
            reference = Image.open(payload['tool_args']['referenced_image_paths'][0]).convert('RGB')
            self.assertIsNone(ImageChops.difference(reference, expected.convert('RGB')).getbbox())
            self.assertIn('inventory icon', payload['prompt'])
            self.assertNotIn('7item285', payload['prompt'])
            self.assertNotIn('amulet1', payload['prompt'])
            self.assertIn('pure magenta', payload['prompt'])
            q.members[cell][1]['cleanup'] = 'key_aware_native_format'
            with self.assertRaisesRegex(AssertionError, 'cutout cleanup'):
                q.payload(job_id, cell_id=cell)

    def test_independent_legacy_cutout_uses_full_canvas_without_splitting_groups(self):
        with tempfile.TemporaryDirectory() as directory:
            q = queue_module.Queue(Path(directory) / 'state.json')
            job_id = 'legacy_ui_art-fa62585e62aa'
            cell = 'engine--icons--6anot2off.bmp'
            payload = q.payload(job_id, cell_id=cell)
            self.assertEqual(payload['execution_layout'], dict(canvas_size=[78, 72],
                             cell_rects={cell: [0, 0, 78, 72]}))
            self.assertIn('legacy UI icon', payload['prompt'])
            with Image.open(payload['tool_args']['referenced_image_paths'][0]) as reference:
                self.assertEqual(reference.size, (78, 72))
            q.jobs[job_id]['members'].append(dict(q.jobs[job_id]['members'][0]))
            with self.assertRaisesRegex(AssertionError, 'independent legacy cutout'):
                q.payload(job_id, cell_id=cell)

    def test_single_equipment_payload_preserves_canvas_and_excludes_siblings(self):
        with tempfile.TemporaryDirectory() as directory:
            q = queue_module.Queue(Path(directory) / 'state.json')
            job_id = 'fitted_equipment_variants-901cd20a3a0a'
            q.jobs[job_id]['dependencies'] = []  # Isolate selection from production pilot state.
            cell = 'engine--icons--6cape5v4a.bmp'
            payload = q.payload(job_id, cell_id=cell)
            self.assertEqual(payload['selected_cells'], [cell])
            self.assertEqual(payload['execution_layout'], dict(canvas_size=[260, 562],
                             cell_rects={cell: [0, 0, 260, 562]}))
            reference = Image.open(payload['tool_args']['referenced_image_paths'][0])
            source = rendered(Image.open(HERE.parents[2] / q.members[cell][1]['source_path']), 'item')
            expected = Image.new('RGBA', (260, 562), (255, 0, 255, 255))
            expected.alpha_composite(source.resize((260, 562), Image.Resampling.NEAREST))
            self.assertIsNone(ImageChops.difference(reference, expected.convert('RGB')).getbbox())
            self.assertNotIn('6cape5v1a', payload['prompt'])
            with self.assertRaisesRegex(AssertionError, 'does not belong'):
                q.payload(job_id, cell_id='wrong-cell')
            with self.assertRaisesRegex(AssertionError, 'Do not split'):
                q.payload(job_id, cell_id=cell, pair_index=0)

    def test_palette_zero_is_an_index_not_a_color(self):
        image = Image.new('P', (3, 1))
        palette = [90, 40, 20, 90, 40, 20, 0, 255, 255] + [0] * (768 - 9)
        image.putpalette(palette)
        image.putdata([0, 1, 2])
        self.assertEqual(list(rendered(image, 'item').getchannel('A').getdata()), [0, 255, 0])
        self.assertEqual(list(rendered(image, 'hud').getchannel('A').getdata()), [255, 255, 0])

    def test_menu_pcx_uses_additional_keys(self):
        image = Image.new('RGB', (3, 1))
        image.putdata([(0, 0, 255), (255, 56, 255), (50, 60, 70)])
        self.assertEqual(list(rendered(image, 'menu_pcx').getchannel('A').getdata()), [0, 0, 255])
        self.assertEqual(list(rendered(image, 'menu_bmp').getchannel('A').getdata()), [255, 0, 255])
        self.assertEqual(list(rendered(image, 'hud').getchannel('A').getdata()), [255, 255, 255])

    def test_pair_layout_keeps_siblings_adjacent_despite_different_sizes(self):
        members = [dict(source_rect=[0, 0, w, h], treatment='spell_icon_pair')
                   for w, h in [(125, 137), (126, 137), (130, 140), (129, 139)]]
        size = layout(members)
        self.assertEqual(members[0]['reference_cell_rect'][1], members[1]['reference_cell_rect'][1])
        self.assertEqual(members[2]['reference_cell_rect'][1], members[3]['reference_cell_rect'][1])
        self.assertNotEqual(members[0]['reference_cell_rect'][1], members[2]['reference_cell_rect'][1])
        self.assertEqual(members[0]['reference_cell_rect'][2:], [250, 274])
        self.assertLessEqual(members[-1]['reference_cell_rect'][1] + 278, size[1])

    def test_actual_torchlight_center_anchor(self):
        manifest = read('expected_targets.json')
        selected = [t for t in manifest['targets'] if t['runtime_name'] in {'sbf000', 'sbf01a', 'sbf01b'}]
        spell_crops(selected)
        icon = next(t for t in selected if t['runtime_name'] == 'sbf01a')
        self.assertEqual(icon['page_dependencies'][0]['x2_draw_rect'], [655, 596, 266, 300])
        self.assertEqual({r['state'] for r in icon['page_dependencies']}, {'highlighted', 'pressed'})

    def test_registered_atlas_covers_bottom_partial_row(self):
        target = dict(id='atlas', source_path='assets_dev/engine/icons/Sprites.PCX', source_sha256='unused',
                      native_size=[960, 2500], atlas={'card_slots': {}},
                      treatment='registered_arcomage_atlas', compositing={'cleanup': 'key_aware_native_format'})
        regions = parts(target)
        self.assertEqual(sum(r['source_rect'][2] * r['source_rect'][3] for r in regions), 960 * 2500)
        self.assertEqual(regions[-1]['source_rect'], [864, 2396, 96, 104])
        self.assertEqual(regions[-1]['export_region'], [1728, 4792, 192, 208])

    def test_changed_page_invalidates_dependent_acceptance_only(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            queue = queue_module.Queue.__new__(queue_module.Queue)
            queue.state = {'cells': {}}
            for name in ['page', 'icon', 'sibling']:
                path = directory / (name + '.png')
                Image.new('RGB', (2, 2), 'red').save(path)
                queue.state['cells'][name] = dict(status='accepted', artifact=str(path), sha256=digest(path))
            queue.state['cells']['icon']['dependency_cells'] = {'page': queue.state['cells']['page']['sha256']}
            self.assertTrue(queue.accepted('icon'))
            Image.new('RGB', (2, 2), 'blue').save(directory / 'page.png')
            self.assertFalse(queue.accepted('icon'))
            self.assertTrue(queue.accepted('sibling'))

    def test_checkpoint_rejects_queue_drift_without_resetting_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            original = {'jobs_sha256': 'stale', 'cells': {'accepted-sibling': {'status': 'accepted'}}}
            path.write_text(json.dumps(original))
            with self.assertRaisesRegex(AssertionError, 'reconcile'):
                queue_module.Queue(path)
            self.assertEqual(json.loads(path.read_text()), original)

    def test_layout_revision_invalidates_only_affected_cells_without_erasing_art(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'retained.png'
            Image.new('RGB', (2, 2), 'red').save(path)
            queue = queue_module.Queue.__new__(queue_module.Queue)
            queue.layout_cells = {'spell'}
            record = dict(status='accepted', artifact=str(path), sha256=digest(path))
            queue.state = dict(layout_revision={'sha256': 'new-layout'},
                               cells={'spell': dict(record), 'unrelated': dict(record)})
            self.assertFalse(queue.accepted('spell'))
            self.assertTrue(queue.accepted('unrelated'))
            self.assertEqual(digest(path), record['sha256'])
            queue.state['cells']['spell']['layout_sha256'] = 'new-layout'
            self.assertTrue(queue.accepted('spell'))
            queue.state['layout_revision']['sha256'] = 'later-layout'
            self.assertFalse(queue.accepted('spell'))

    def test_effective_crop_revision_preserves_variant_native_canvas_and_frozen_files(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_path = directory / 'state.json'
            queue = queue_module.Queue(state_path)
            target_id = 'engine--icons--sba05a.bmp'
            target = queue.targets[target_id]
            before = target['page_dependencies'][0]['x2_draw_rect']
            self.assertEqual(target['x2_size'], [250, 274])
            self.assertEqual(before[2:], [252, 274])  # Existing button width differs from this state's bitmap.
            native_layout = 'assets_dev/engine/ui/gameplay/spellbook.yml'
            native = queue_module.ROOT / native_layout
            revision = dict(native_layout=native_layout, native_layout_sha256=digest(native),
                preview_layout=str(native), preview_layout_sha256=digest(native), evidence_hashes={},
                targets={target_id: dict(before_x2=before, after_x2=[936, 666, *before[2:]])})
            path = directory / 'revision.json'
            queue_module.save(path, revision)
            queue.state['layout_revision'] = dict(path=str(path), sha256=digest(path))
            queue_module.save(state_path, queue.state)
            revised = queue_module.Queue(state_path)
            self.assertEqual(revised.targets[target_id]['x2_size'], [250, 274])
            self.assertEqual(revised.targets[target_id]['page_dependencies'][0]['x2_draw_rect'], [936, 666, 252, 274])
            recipes = [d['recipe'] for j in revised.jobs.values() for d in j['dependencies']
                       if d['kind'] == 'accepted_page_crop' and d['recipe']['element'] ==
                       target['page_dependencies'][0]['element'] and d['recipe']['state'] in {'highlighted', 'pressed'}]
            self.assertTrue(recipes)
            self.assertTrue(all(r['x2_draw_rect'] == [936, 666, 252, 274] for r in recipes))
            self.assertEqual(digest(native), revision['native_layout_sha256'])
            path.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'revision changed'):
                queue_module.Queue(state_path)

    def test_frozen_jobs_do_not_claim_artwork_acceptance(self):
        # Production progress belongs in checkpoint/, not the immutable preparation manifest.
        self.assertTrue(all(j['initial_state'] == 'pending' for j in read('jobs.json')['jobs']))

    def test_record_accept_defer_and_resume_use_separate_checkpoint(self):
        with tempfile.TemporaryDirectory(prefix='hud-queue-fixture-') as directory:
            directory = Path(directory)
            state_path = directory / 'state.json'
            queue = queue_module.Queue(state_path)
            job = next(j for j in queue.jobs.values() if j['pilot'] and len(j['members']) >= 2
                       and not queue.blockers(j))
            queue.payload(job['id'])
            raw = directory / 'synthetic-test-master.png'
            Image.new('RGB', job['reference_size'], (80, 80, 80)).save(raw)
            attempt = queue.record(job['id'], raw)['attempt']
            member = job['members'][0]
            artifact = directory / 'synthetic-test-cell.png'
            Image.new('RGBA', (1, 1)).save(artifact)
            with self.assertRaisesRegex(AssertionError, 'exact x2'):
                queue.accept(member['id'], artifact, {}, attempt)
            target = queue.targets[member['target']]
            with Image.open(queue_module.ROOT / member['source_path']) as native:
                rendered(native, target['compositing']['profiles'][0]).resize(
                    tuple(member['export_region'][2:]), Image.Resampling.NEAREST).save(artifact)
            fitting = registration.evidence(member, target, artifact, directory / 'fitting')
            registration_path = Path(fitting['registration_record'])
            report = json.loads(registration_path.read_text())
            report['visual_fit_notes'] = 'Synthetic fixture only; native enlargement is not restored artwork.'
            report['landmarks'] = [dict(name=str(i), source_xy=[i, i], restored_xy=[i * 2, i * 2])
                                   for i in range(3)]
            registration_path.write_text(json.dumps(report))
            review = dict(identity=True, registration=True, compositing=True, detail_at_x2=True,
                          state_or_animation_consistency=True, notes='Synthetic state-machine fixture, not artwork.',
                          registration_record=str(registration_path), review_images=fitting['review_images'])
            queue.accept(member['id'], artifact, review, attempt)
            sibling = job['members'][1]['id']
            result = subprocess.run([sys.executable, str(HERE / 'queue.py'), '--state', str(state_path),
                                     'defer', sibling, '--reason', 'Synthetic fixture defect'],
                                    check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(result.stdout)['status'], 'deferred')
            resumed = queue_module.Queue(state_path)
            self.assertTrue(resumed.accepted(member['id']))
            self.assertEqual(resumed.state['cells'][sibling]['status'], 'deferred')
            self.assertTrue(Path(resumed.state['attempts'][0]['raw']).is_file())
            complete = resumed.reconstruct(member['target'])
            full_review = dict(full_canvas_review=True, notes='Synthetic canvas fixture only.',
                               artifact_sha256=complete['sha256'], review_images=fitting['review_images'])
            with self.assertRaisesRegex(AssertionError, 'exact canvas'):
                resumed.stage(member['target'], dict(full_review, artifact_sha256='stale'))
            staged = resumed.stage(member['target'], full_review)
            self.assertIn(directory, Path(staged['artifact']).parents)
            self.assertEqual(digest(Path(staged['artifact'])), complete['sha256'])
            self.assertEqual(staged['status'], 'staged_for_isolated_preview_not_installed')
            with self.assertRaisesRegex(AssertionError, 'already accepted'):
                resumed.accept(member['id'], artifact, review, attempt)

    def test_cutout_payload_requires_magenta_and_keeps_background_exceptions(self):
        with tempfile.TemporaryDirectory(prefix='hud-matte-fixture-') as directory:
            queue = queue_module.Queue(Path(directory) / 'state.json')
            job = next(j for j in queue.jobs.values() if j['treatment'] == 'fitted_equipment_variants'
                       and not queue.blockers(j))
            payload = queue.payload(job['id'])
            self.assertIn('pure magenta RGB(255,0,255)', payload['prompt'])
            self.assertIn('Do not simulate transparency with a checkerboard', payload['prompt'])
            self.assertIn('preserve each distinct native key/index region', payload['prompt'])
            self.assertIn('MATTE_AND_FITTING.md', payload['cleanup_instructions'])
            self.assertIn('Do not shrink the subject', payload['prompt'])

    def test_full_canvas_payload_and_repair_references_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            queue = queue_module.Queue(directory / 'state.json')
            job = queue.jobs['spellbook_page-928106ac2fea']
            repair, detail = directory / 'repair.png', directory / 'detail.png'
            Image.new('RGB', (640, 480), '#aa8866').save(repair)
            Image.new('RGB', (40, 40), '#775533').save(detail)
            payload = queue.payload(job['id'], repair_note='Repair missing AIR title',
                                    repair_reference=repair, detail_reference=detail)
            self.assertEqual(payload['execution_layout']['canvas_size'], [1280, 960])
            self.assertEqual(payload['execution_layout']['cell_rects'][job['members'][0]['id']],
                             [0, 0, 1280, 960])
            reference = Path(payload['tool_args']['referenced_image_paths'][0])
            with Image.open(reference) as image:
                self.assertEqual(image.size, (1280, 960))
            self.assertNotIn('sheet xywh=', payload['prompt'])
            self.assertEqual(payload['reference_hashes'][str(repair.resolve())], digest(repair))
            self.assertEqual(payload['reference_hashes'][str(detail.resolve())], digest(detail))
            attempt = queue.record(job['id'], repair)['attempt']
            record = next(a for a in queue.state['attempts'] if a['id'] == attempt)
            submitted = json.loads(Path(record['payload']).read_text())
            self.assertEqual(submitted['reference_hashes'], payload['reference_hashes'])

    def test_spell_payload_uses_exact_page_crops_and_no_unrelated_pilot_faces(self):
        with tempfile.TemporaryDirectory(prefix='hud-page-fixture-') as directory:
            directory = Path(directory)
            queue = queue_module.Queue(directory / 'state.json')
            job = next(j for j in queue.jobs.values() if any(
                queue.targets[m['target']]['runtime_name'] == 'sbf01a' for m in j['members']))
            with self.assertRaisesRegex(AssertionError, 'Unaccepted dependencies'):
                queue.payload(job['id'])
            for i, cell in enumerate(queue.dependency_cells(job)):
                member = queue.members[cell][1]
                width, height = member['export_region'][2:]
                y, x = np.indices((height, width))
                pixels = np.stack([x % 256, y % 256, np.full_like(x, 17)], axis=-1).astype('uint8')
                path = directory / f'fixture-{i}.png'
                Image.fromarray(pixels).save(path)
                queue.state['cells'][cell] = dict(status='accepted', artifact=str(path), sha256=digest(path))
            payload = queue.payload(job['id'])
            self.assertLessEqual(len(payload['tool_args']['referenced_image_paths']), 4)
            elements = {r['element'] for r in payload['page_crops']}
            self.assertEqual(len(elements) * 2, len(job['members']))
            crop_path = next(p for p in payload['reference_layouts'] if p.endswith('accepted-page-crops.png'))
            with Image.open(crop_path) as sheet:
                for rectangle, crop in zip(payload['reference_layouts'][crop_path], payload['page_crops']):
                    x, y, width, height = rectangle['xywh']
                    sx, sy, ex, ey = crop['crop_xyxy']
                    self.assertEqual([width, height], [ex - sx, ey - sy])
                    self.assertEqual(sheet.getpixel((x, y)), (sx % 256, sy % 256, 17))
                    if crop['element'] == 'SpellbookPageFireSpellTorchlight':
                        self.assertEqual(crop['final_draw_xywh'], [655, 596, 266, 300])
                        self.assertEqual(crop['crop_xyxy'], [639, 580, 937, 912])
            self.assertTrue(all(directory in Path(p).parents or p.endswith(job['reference_path'])
                                for p in payload['reference_hashes']))
            pair = queue.payload(job['id'], pair_index=0, spell_ink_matte=True)
            self.assertEqual(pair['selected_cells'], [m['id'] for m in job['members'][:2]])
            self.assertEqual(len(pair['page_crops']), 1)
            self.assertIn('Remove all parchment substrate', pair['prompt'])
            self.assertNotIn('Use the accepted page crop as the exact paper substrate', pair['prompt'])
            for member in job['members'][:2]:
                self.assertEqual(pair['execution_layout']['cell_rects'][member['id']][2:],
                                 member['export_region'][2:])
            raw = directory / 'synthetic-pair.png'
            Image.new('RGB', tuple(pair['execution_layout']['canvas_size']), '#ff00ff').save(raw)
            attempt = queue.record(job['id'], raw)['attempt']
            with self.assertRaisesRegex(AssertionError, 'not submitted'):
                queue.accept(job['members'][2]['id'], raw, {}, attempt)
            with self.assertRaisesRegex(AssertionError, 'Invalid spell pair'):
                queue.payload(job['id'], pair_index=999)
            with self.assertRaisesRegex(AssertionError, 'requires a selected spell pair'):
                queue.payload(job['id'], spell_ink_matte=True)

    def test_native_bindings_include_mm9_offsets_and_real_frame_ticks(self):
        metadata = native_metadata.load()
        self.assertEqual(metadata['icons']['fr1'][0]['frame_ticks'], 8)
        self.assertEqual(metadata['icons']['fr1'][0]['animation_ticks'], 240)
        self.assertTrue(any('worlds/mm9/' in row['source'] for rows in metadata['complex_items'].values()
                            for row in rows))
        self.assertEqual(sum(len(v) for v in metadata['cards'].values()), 102)

    def test_nonstandard_portrait_prefix_retains_one_identity(self):
        frame = frame_metadata(dict(path='assets_dev/engine/icons/girla07.bmp',
            usages=[dict(kind='portrait_table_family', prefix='girla', character_id='39')]))
        self.assertEqual(frame['ordinal'], 7)
        self.assertEqual(family(dict(runtime_name='girla07', treatment='player_portrait_frames', frame=frame)), 'girla')

    def test_parallel_cli_updates_preserve_both_cells(self):
        with tempfile.TemporaryDirectory(prefix='hud-lock-fixture-') as directory:
            path = Path(directory) / 'state.json'
            queue = queue_module.Queue(path)
            cells = list(queue.members)[:2]
            processes = [subprocess.Popen([sys.executable, str(HERE / 'queue.py'), '--state', str(path),
                'defer', cell, '--reason', 'Concurrent synthetic fixture'], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True) for cell in cells]
            for process in processes:
                stdout, stderr = process.communicate(timeout=30)
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(set(json.loads(path.read_text())['cells']), set(cells))

    def test_atlas_reconstruction_retains_all_rgb_keys_and_full_canvas(self):
        with tempfile.TemporaryDirectory(prefix='hud-atlas-fixture-') as directory:
            directory = Path(directory)
            queue = queue_module.Queue(directory / 'state.json')
            target = next(t for t in queue.targets.values() if t['treatment'] == 'registered_arcomage_atlas')
            with self.assertRaisesRegex(AssertionError, 'constituent'):
                queue.reconstruct(target['id'])
            with Image.open(HERE.parents[2] / target['source_path']) as source:
                expected = source.resize(target['x2_size'], Image.Resampling.NEAREST).convert('RGB')
            for i, cell in enumerate(queue.target_cells[target['id']]):
                x, y, width, height = queue.members[cell][1]['export_region']
                path = directory / f'synthetic-region-{i}.png'
                expected.crop((x, y, x + width, y + height)).save(path)
                queue.state['cells'][cell] = dict(status='accepted', artifact=str(path), sha256=digest(path))
            record = queue.reconstruct(target['id'])
            with Image.open(record['path']) as result:
                self.assertEqual(result.size, (1920, 5000))
                self.assertIsNone(ImageChops.difference(result.convert('RGB'), expected).getbbox())
            self.assertEqual(record['status'], 'reconstructed_awaiting_full_canvas_review')


if __name__ == '__main__':
    unittest.main()
