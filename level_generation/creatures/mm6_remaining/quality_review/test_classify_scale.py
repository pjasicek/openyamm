"""Exercise consequential classification boundaries without changing any creature assets."""

import copy
import unittest

from classify_scale import bindings, measure, saved_measurements, screen, solve_verified, source_sampling


def annotation(factor=1.05):
    dimensions = []
    for name, axis, length, role in [('shoulders', 'x', 80, 'fit'), ('torso', 'y', 120, 'fit'),
                                     ('head', 'x', 50, 'check')]:
        dimensions.append(dict(name=name, axis=axis, native_length=length,
                               restored_length_px=2 * length / factor, native_error=0.1,
                               restored_error_px=0.2, role=role))
    return dict(provenance={'test': 'same_artifact'}, verified=True, reviewer='synthetic test', dimensions=dimensions)


def solve(data, **kwargs):
    arguments = dict(provenance={'test': 'same_artifact'}, tier=2, export_scale=0.8, sampling=2.5,
                     strict=True, blockers=[], deadband=0.01)
    arguments.update(kwargs)
    return solve_verified(data, **arguments)


class ScaleClassificationTests(unittest.TestCase):
    def test_known_scale_composes_with_export(self):
        result = solve(annotation())
        self.assertEqual(result['decision'], 'downsample_trial_candidate')
        self.assertAlmostEqual(result['proposed_export_scale'], 0.84)
        self.assertAlmostEqual(result['estimated_sampling_after'], 2.5 / 1.05)

    def test_native_pose_height_change_is_not_scale_drift(self):
        for native in [200, 170, 90]:
            evidence = [measure('height', 'y', native, native * 2, 2, 4, 2, 'test')]
            self.assertEqual(screen(evidence, 0.02), 'no_scale_signal')

    def test_translation_does_not_change_lengths(self):
        record = {'review_landmarks': {
            'head': {'native': [50, 0], 'restored_before_translation': [100, 0]},
            'foot': {'native': [50, 200], 'restored_before_translation': [100, 390]},
        }}
        original = saved_measurements(record, None, None, 2)
        for point in record['review_landmarks'].values():
            point['restored_before_translation'][0] += 213
            point['restored_before_translation'][1] -= 91
        self.assertEqual(original, saved_measurements(record, None, None, 2))

    def test_conflicting_width_and_height(self):
        data = annotation()
        data['dimensions'][0]['restored_length_px'] = 160
        self.assertEqual(solve(data)['decision'], 'proportion_or_pose_review')

    def test_withheld_feature_does_not_influence_fit(self):
        data = annotation()
        data['dimensions'][2]['restored_length_px'] = 100
        result = solve(data)
        self.assertEqual(result['decision'], 'proportion_or_pose_review')
        self.assertAlmostEqual(result['fitted_correction'], 1.05)
        self.assertIsNone(result['proposed_export_scale'])

    def test_skip_unchanged_and_small_adjustment(self):
        for factor in [1, 1.005]:
            self.assertEqual(solve(annotation(factor))['decision'], 'keep_scale')

    def test_uncertainty_prevents_unsupported_adjustment(self):
        data = annotation(1.03)
        for item in data['dimensions']:
            item['native_error'] = 4
            item['restored_error_px'] = 8
        self.assertEqual(solve(data)['decision'], 'keep_scale')

    def test_missing_horizontal_or_withheld_dimension(self):
        data = annotation()
        data['dimensions'][0]['axis'] = 'y'
        self.assertEqual(solve(data)['decision'], 'review_measurements')
        data = annotation()
        data['dimensions'].pop()
        self.assertEqual(solve(data)['decision'], 'review_measurements')

    def test_no_measured_anatomy_never_proposes_scale(self):
        result = solve(None)
        self.assertEqual(result['decision'], 'review_measurements')
        self.assertIsNone(result['proposed_export_scale'])

    def test_stale_artifacts_fail_loudly(self):
        with self.assertRaisesRegex(ValueError, 'different artifacts'):
            solve(annotation(), provenance={'test': 'new_pixels'})

    def test_sampling_gate_strict_and_inclusive(self):
        self.assertEqual(solve(annotation(1.25), sampling=2.5)['decision'], 'source_review')
        self.assertEqual(solve(annotation(1.25), sampling=2.5, strict=False)['decision'],
                         'downsample_trial_candidate')

    def test_source_blockers_and_unknown_transform(self):
        for args in [dict(blockers=['recorded_raw_clipping']), dict(export_scale=None), dict(sampling=None)]:
            self.assertEqual(solve(annotation(), **args)['decision'], 'source_review')

    def test_small_and_diagnostic_landmarks_are_excluded(self):
        record = {'diagnostic_landmarks': ['staff'], 'review_landmarks': {
            'head': {'native': [10, 20], 'restored_before_translation': [20, 40]},
            'neck': {'native': [10, 30], 'restored_before_translation': [20, 60]},
            'staff': {'native': [10, 200], 'restored_before_translation': [20, 500]},
        }}
        self.assertEqual(saved_measurements(record, None, None, 2), [])
        self.assertEqual(screen([], 0.02), 'insufficient_evidence')

    def test_small_but_resolved_vertical_drift_is_flagged(self):
        evidence = [measure('head/sole', 'y', 227, 454 / 1.02477, 2, 4, 2, 'test')]
        self.assertEqual(screen(evidence, 0.02), 'size_signal_needs_body_measurements')

    def test_unresolved_small_feature_does_not_prove_drift(self):
        evidence = [measure('head', 'x', 20, 38, 2, 4, 2, 'test')]
        self.assertEqual(screen(evidence, 0.02), 'no_scale_signal')

    def test_tier_is_not_assumed_to_be_two(self):
        item = measure('torso', 'y', 100, 400, 1, 4, 4, 'test')
        self.assertEqual(item['correction'], 1)

    def test_declared_empty_endpoint_has_no_sampling_requirement(self):
        record = dict(scale=1, effective_sampling_xy=[0, 0], empty_native_endpoint=True)
        self.assertEqual(source_sampling(record, 2, True), (None, 'not_applicable_empty_endpoint'))
        with self.assertRaisesRegex(ValueError, 'contains foreground'):
            source_sampling(record, 2, False)

    def test_invalid_sampling_is_not_replaced_by_nominal_scale(self):
        with self.assertRaisesRegex(ValueError, 'Invalid recorded effective sampling'):
            source_sampling(dict(scale=0.8, effective_sampling_xy=[0, 0]), 2, False)
        self.assertEqual(source_sampling(dict(scale=0.8), 2, False), (2.5, 'nominal_tier_divided_by_scale'))

    def test_nonfinite_and_degenerate_measurements_rejected(self):
        for value in [0, -1, float('nan'), float('inf')]:
            data = annotation()
            data['dimensions'][0]['native_length'] = value
            with self.assertRaises(ValueError):
                solve(data)

    def test_all_palette_mirrored_and_repeated_bindings_retained(self):
        animation = {'walk': {'views': {'0': [{'frame': 'a'}, {'frame': 'a'}],
                                        '7': [{'frame': 'a', 'mirrored': True}]}}}
        manifest = {'animations_by_palette': {'1': animation, '2': copy.deepcopy(animation)}}
        result = bindings(manifest)['a']
        self.assertEqual(len(result), 6)
        self.assertEqual(sum(item['mirrored'] for item in result), 2)


if __name__ == '__main__':
    unittest.main()
