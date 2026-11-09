"""Synthetic reuse guards; no production checkpoint or artwork is modified."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from finalize_classification import HERE, digest
import registration

spec = importlib.util.spec_from_file_location('hud_queue_reuse', HERE / 'queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source = root / 'native.png'
        Image.new('RGBA', (8, 8), 'brown').save(self.source)
        artifact = root / 'donor.png'
        Image.new('RGBA', (16, 16), 'brown').save(artifact)
        q = module.Queue.__new__(module.Queue)
        q.state_path = root / 'state.json'
        q.state = dict(cells={'donor': dict(status='accepted', artifact=str(artifact), sha256=digest(artifact))},
                       attempts=[])
        q.targets, q.members, q.target_cells, q.jobs = {}, {}, {}, {}
        for cell in ('donor', 'destination'):
            target = dict(id=cell, source_path=str(self.source), source_sha256=digest(self.source),
                          namespace='engine', native_size=[8, 8], x2_size=[16, 16], treatment='inventory_icon',
                          logical_canvas=[0, 0, 8, 8], placement='full canvas', frame=None,
                          native_palette_sha256=None, native_rgba_sha256='identical',
                          compositing={'profiles': ['item']}, output_path=cell + '.png')
            member = dict(id=cell, target=cell, source_path=str(self.source), source_sha256=digest(self.source),
                          source_rect=[0, 0, 8, 8], export_region=[0, 0, 16, 16], method='imagegen_sheet',
                          cleanup='alpha_cutout_or_effect')
            q.targets[cell] = target
            q.members[cell] = (cell, member)
            q.target_cells[cell] = [cell]
            q.jobs[cell] = dict(dependencies=[])
        self.q = q
        self.review = registration.evidence(q.members['destination'][1], q.targets['destination'], artifact,
                                            root / 'review')
        path = Path(self.review['registration_record'])
        import json
        record = json.loads(path.read_text())
        record.update(visual_fit_notes='Synthetic test only', landmarks=[
            dict(name=str(i), source_xy=[i, i], restored_xy=[2*i, 2*i]) for i in (1, 3, 6)])
        module.save(path, record)
        self.review.update(identity=True, registration=True, compositing=True, detail_at_x2=True,
                           state_or_animation_consistency=True, notes='Synthetic test only',
                           consumer_contract_notes='Synthetic identical full canvases')

    def test_reuse_tracks_donor_without_inventing_generation(self):
        self.q.reuse('destination', 'donor', self.review)
        self.assertTrue(self.q.accepted('destination'))
        self.assertEqual(self.q.state['attempts'], [])
        self.assertNotIn('attempt', self.q.state['cells']['destination'])
        self.assertEqual(self.q.state['cells']['destination']['reuse']['donor_cell'], 'donor')
        Path(self.q.state['cells']['donor']['artifact']).write_bytes(b'changed')
        self.assertFalse(self.q.accepted('destination'))

    def test_mismatched_contracts_are_rejected(self):
        for field, value in [('native_size', [7, 8]), ('source_sha256', 'wrong'),
                             ('compositing', {'profiles': ['hud']}), ('namespace', 'mm6')]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.q.targets['destination'])
                self.q.targets['destination'][field] = value
                with self.assertRaises(AssertionError):
                    self.q.reuse('destination', 'donor', self.review)
                self.q.targets['destination'] = original
        self.assertNotIn('destination', self.q.state['cells'])

    def test_unreviewed_and_seed_dependent_art_is_rejected(self):
        review = dict(self.review, consumer_contract_notes='')
        with self.assertRaises(AssertionError):
            self.q.reuse('destination', 'donor', review)
        self.q.jobs['destination']['dependencies'] = [{'kind': 'accepted_identity_seed', 'target': 'donor'}]
        with self.assertRaises(AssertionError):
            self.q.reuse('destination', 'donor', self.review)

    def test_exact_seed_donor_can_be_reused_and_remains_a_dependency(self):
        self.q.jobs['donor']['members'] = [self.q.members['donor'][1]]
        self.q.jobs['destination']['dependencies'] = [{'kind': 'accepted_seed_job', 'job': 'donor'}]
        self.q.reuse('destination', 'donor', self.review)
        self.assertTrue(self.q.accepted('destination'))
        self.assertEqual(self.q.state['cells']['destination']['dependency_cells'],
                         {'donor': self.q.state['cells']['donor']['sha256']})
        self.q.state['cells']['donor']['status'] = 'deferred'
        self.assertFalse(self.q.accepted('destination'))

    def seeded_siblings(self):
        q = self.q
        seed = self.source.parent / 'seed.png'
        Image.new('RGBA', (16, 16), 'green').save(seed)
        q.state['cells']['seed'] = dict(status='accepted', artifact=str(seed), sha256=digest(seed))
        q.jobs['seed'] = dict(members=[dict(id='seed')], dependencies=[])
        q.jobs['donor']['dependencies'] = [dict(kind='accepted_seed_job', job='seed')]
        q.members['destination'] = ('donor', q.members['destination'][1])
        q.state['cells']['donor']['dependency_cells'] = {'seed': digest(seed)}
        return seed

    def test_seeded_siblings_track_seed_and_donor_without_generation(self):
        seed = self.seeded_siblings()
        self.q.reuse('destination', 'donor', self.review)
        self.assertTrue(self.q.accepted('destination'))
        self.assertEqual(self.q.state['attempts'], [])
        self.assertEqual(self.q.state['cells']['destination']['dependency_cells'],
                         {'seed': digest(seed), 'donor': self.q.state['cells']['donor']['sha256']})
        Image.new('RGBA', (16, 16), 'blue').save(seed)
        self.q.state['cells']['seed']['sha256'] = digest(seed)
        self.assertFalse(self.q.accepted('donor'))
        self.assertFalse(self.q.accepted('destination'))

    def test_seeded_sibling_rejects_missing_donor_dependency_record(self):
        self.seeded_siblings()
        self.q.state['cells']['donor']['dependency_cells'] = {}
        with self.assertRaisesRegex(AssertionError, 'every current shared dependency'):
            self.q.reuse('destination', 'donor', self.review)
        self.assertNotIn('destination', self.q.state['cells'])

    def test_shared_seed_in_different_jobs_does_not_authorize_reuse(self):
        self.seeded_siblings()
        self.q.members['destination'] = ('destination', self.q.members['destination'][1])
        self.q.jobs['destination']['dependencies'] = [dict(kind='accepted_seed_job', job='seed')]
        with self.assertRaises(AssertionError):
            self.q.reuse('destination', 'donor', self.review)

    def test_same_job_does_not_allow_other_dependency_kinds(self):
        self.seeded_siblings()
        self.q.jobs['donor']['dependencies'][0]['kind'] = 'accepted_identity_seed'
        with self.assertRaises(AssertionError):
            self.q.reuse('destination', 'donor', self.review)


if __name__ == '__main__':
    unittest.main()
