"""Exercise custom anatomical anchors against the actual reviewer checkpoint schema."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from propose_anatomical_placement import build_proposal, compile_frame


MANIFEST = {'creature': 'mm6:test', 'pixels_per_logical_pixel': 2, 'logical_pivot': [80.5, 150],
            'frames': {'pose': {'crop_origin_px': [40, 20], 'atlas_xywh': [0, 0, 100, 200]},
                       'untouched': {'crop_origin_px': [1, 1]}}, 'variants': {'1': {}}, 'regions': {}}
BOUNDS = [5, 10, 95, 190]


def annotation():
    return {'policy': 'humanoid_planted', 'reason': 'Actor-left sole stays planted; hip is independent.',
            'scale_factor': 1.1,
            'points': {'sole': {'native': [37.25, 100.25], 'restored': [40, 100]},
                       'hip': {'native': [48.25, 56.25], 'restored': [50, 60]}},
            'align': {'x': 'sole', 'y': 'sole'}, 'checks': ['hip'],
            'check_tolerance_native_px': [.26, .26]}


class AnatomicalPlacementTests(unittest.TestCase):
    def test_custom_foot_uses_bottom_serialization_without_losing_foot_pivot(self):
        result, evidence = compile_frame(MANIFEST, BOUNDS, 'pose', annotation(), {'note': 'Keep original review'})
        self.assertEqual(result['scale_anchor'], 'bottom')
        self.assertEqual(result['offset_px'], [-4, 2])
        self.assertAlmostEqual(evidence['independent_residuals_native_px']['hip'][0], .25)
        self.assertAlmostEqual(evidence['independent_residuals_native_px']['hip'][1], .25)
        self.assertTrue(result['note'].startswith('Keep original review\n'))

    def test_two_body_points_calibrate_size_and_third_checks_it(self):
        a = annotation()
        del a['scale_factor']
        a['points']['crown'] = {'native': [37.25, 12.25], 'restored': [40, 20]}
        a['scale_from'] = {'points': ['crown', 'sole'], 'axis': 'y'}
        result, _ = compile_frame(MANIFEST, BOUNDS, 'pose', a, {})
        self.assertAlmostEqual(result['scale_factor'], 1.1)

    def test_one_head_point_does_not_calibrate_flying_scale(self):
        a = annotation()
        del a['scale_factor']
        a['policy'] = 'flying'
        a['scale_from'] = {'points': ['sole', 'sole'], 'axis': 'y'}
        with self.assertRaisesRegex(ValueError, 'distinct'):
            compile_frame(MANIFEST, BOUNDS, 'pose', a, {})

    def test_fit_point_cannot_pass_as_independent_evidence(self):
        a = annotation()
        a['checks'] = ['sole']
        with self.assertRaisesRegex(ValueError, 'independent'):
            compile_frame(MANIFEST, BOUNDS, 'pose', a, {})

    def test_bad_body_proportion_cannot_be_hidden_by_fitting_a_foot(self):
        a = annotation()
        a['points']['hip']['native'][0] += 8
        with self.assertRaisesRegex(ValueError, 'anatomical residual'):
            compile_frame(MANIFEST, BOUNDS, 'pose', a, {})

    def test_renaming_an_anchor_does_not_create_an_independent_check(self):
        a = annotation()
        a['points']['hip'] = deepcopy(a['points']['sole'])
        with self.assertRaisesRegex(ValueError, 'Renaming'):
            compile_frame(MANIFEST, BOUNDS, 'pose', a, {})

    def test_occluded_alignment_axis_is_rejected(self):
        a = annotation()
        a['points']['sole']['restored'][0] = None
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            compile_frame(MANIFEST, BOUNDS, 'pose', a, {})

    def test_negative_half_pixel_rounds_like_javascript(self):
        a = annotation()
        a['scale_factor'] = 1
        a['points'] = {'sole': {'native': [39.75, 100], 'restored': [40, 100]},
                       'hip': {'native': [49.75, 60], 'restored': [50, 60]}}
        result, _ = compile_frame(MANIFEST, BOUNDS, 'pose', a, {})
        self.assertEqual(result['offset_px'], [0, 0])

    def setup_inputs(self, root):
        manifest_path = root / 'manifest.json'
        manifest_path.write_text(json.dumps(MANIFEST))
        sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        current = {'revision': 7, 'manifest_sha256': sha, 'frames': {
            'pose': {'offset_px': [2, 3], 'regenerate': False, 'scale_factor': 1, 'scale_anchor': 'bottom'},
            'untouched': {'offset_px': [6, -8], 'regenerate': False, 'scale_factor': .9, 'scale_anchor': 'bottom'}},
            'colors': {}, 'landmarks': {}, 'guides': {'x': 8, 'y': 9, 'zoom': 2}}
        data = {'schema_version': 1, 'coordinates': {}, 'families': {'mm6_test': {'art-hash': current}}}
        checkpoint = root / 'original.json'
        checkpoint.write_text(json.dumps(data))
        plan = {'schema_version': 1, 'family': 'mm6_test', 'manifest': str(manifest_path), 'manifest_sha256': sha,
                'artifact_sha256': 'art-hash', 'checkpoint': str(checkpoint),
                'checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                'frames': {'pose': annotation()}}
        family = SimpleNamespace(id='mm6_test', label='Test', root=root, manifest=deepcopy(MANIFEST),
                                 manifest_sha256=sha, artifact_sha256='art-hash', restored_bounds={'pose': BOUNDS})
        return checkpoint, plan, family

    def test_real_checkpoint_validator_preserves_sources_other_frames_and_guides(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, plan, family = self.setup_inputs(root)
            raw = source.read_bytes()
            with patch('propose_anatomical_placement.load_family', return_value=family):
                report = build_proposal(plan, root / 'proposal.json')
            self.assertEqual(source.read_bytes(), raw)
            candidate = json.loads((root / 'proposal.json').read_text())['families']['mm6_test']['art-hash']
            self.assertEqual(candidate['revision'], 8)
            self.assertEqual(candidate['frames']['untouched']['offset_px'], [6, -8])
            self.assertEqual(candidate['guides'], {'x': 8, 'y': 9, 'zoom': 2})
            self.assertEqual(report['coverage']['compiled'], 1)

    def test_stale_art_is_rejected_before_any_output(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, plan, family = self.setup_inputs(root)
            family.artifact_sha256 = 'changed-art'
            with patch('propose_anatomical_placement.load_family', return_value=family):
                with self.assertRaisesRegex(ValueError, 'changed'):
                    build_proposal(plan, root / 'proposal.json')
            self.assertFalse((root / 'proposal.json').exists())

    def test_mixed_proposal_compiles_valid_frames_and_preserves_blocked_ones(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, plan, family = self.setup_inputs(root)
            raw = source.read_bytes()
            family.restored_bounds['untouched'] = BOUNDS
            bad = annotation()
            bad['points']['hip']['native'][0] += 8
            plan['frames']['untouched'] = bad
            with patch('propose_anatomical_placement.load_family', return_value=family):
                report = build_proposal(plan, root / 'proposal.json')
            self.assertEqual(source.read_bytes(), raw)
            candidate = json.loads((root / 'proposal.json').read_text())['families']['mm6_test']['art-hash']
            self.assertEqual(report['coverage']['compiled'], 1)
            self.assertIn('untouched', report['blocked_frames_preserved'])
            self.assertEqual(candidate['frames']['untouched']['offset_px'], [6, -8])

    def test_failed_fit_records_block_and_keeps_original_checkpoint(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, plan, family = self.setup_inputs(root)
            raw = source.read_bytes()
            plan['frames']['pose']['points']['hip']['native'][0] += 8
            with patch('propose_anatomical_placement.load_family', return_value=family):
                report = build_proposal(plan, root / 'proposal.json')
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(report['coverage']['compiled'], 0)
            self.assertIn('pose', report['blocked_frames_preserved'])
            self.assertFalse((root / 'proposal.json').exists())
            self.assertTrue((root / 'proposal.evidence.json').is_file())


if __name__ == '__main__':
    unittest.main()
