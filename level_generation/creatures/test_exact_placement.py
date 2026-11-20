"""Run with python3 -m unittest discover -s level_generation/creatures -p test_exact_placement.py."""
import copy
import unittest

from exact_placement import export_placement, validate_animation_bindings, validate_landmark_usage, validate_manifest


class PlacementTests(unittest.TestCase):
    def test_diagnostic_landmarks_cannot_own_exported_transform(self):
        annotation = dict(frames={'pose': dict(job='sheet', landmarks=['core', 'tip', 'tail'],
                                              diagnostic_landmarks=['tail'])},
                          calibration={'sheet': dict(frame='pose', pair=[1, 2])})
        registration = {'pose': dict(batch='sheet')}
        self.assertEqual(validate_landmark_usage(annotation, registration),
                         ['sheet: scale point marked diagnostic: tail'])
        annotation['calibration']['sheet']['pair'] = [0, 1]
        self.assertEqual(validate_landmark_usage(annotation, registration), [])
        registration['pose']['diagnostic_landmarks'] = ['core']
        self.assertEqual(validate_landmark_usage(annotation, registration),
                         ['pose: translation anchor marked diagnostic: core'])

    def test_landmark_gate_tracks_active_calibration_authority(self):
        annotation = dict(frames={
            'reference': dict(job='old', landmarks=['core', 'tip'], diagnostic_landmarks=['tip']),
            'pose': dict(job='active', landmarks=['core', 'belt'])}, calibration={
                'active': dict(frame='reference', pair=[0, 1]),
                'unused_candidate': dict(frame='reference', pair=[0, 1])})
        registration = {'pose': dict(batch='active')}
        self.assertEqual(validate_landmark_usage(annotation, registration),
                         ['active: scale point marked diagnostic: tip'])
        annotation['calibration']['active'] = dict(native=[[0, 0], [0, 10]], pair=[0, 1],
            landmarks=['core', 'belt'], diagnostic_landmarks=[])
        self.assertEqual(validate_landmark_usage(annotation, registration), [])
        annotation['calibration']['active']['pair'] = [0, 3]
        self.assertEqual(validate_landmark_usage(annotation, registration),
                         ['active: calibration point index out of range'])

    def test_landmark_gate_checks_shared_row_calibration(self):
        annotation = dict(frames={'pose': dict(job='sheet', landmarks=['head', 'foot'])},
                          calibration={'row2': dict(native=[[0, 0], [0, 10]], pair=[0, 1],
                              landmarks=['head', 'foot'], diagnostic_landmarks=['foot'])})
        registration = {'pose': dict(batch='sheet', calibration_group='row2')}
        self.assertEqual(validate_landmark_usage(annotation, registration),
                         ['row2: scale point marked diagnostic: foot'])

    def animation_fixture(self):
        source = dict(sprite_name='native', animation_length_raw=2, frames=[dict(
            texture_name='pose', frame_length_raw=2, flags=['Mirror5', 'Mirror6', 'Mirror7'])])
        action = dict(native_group='native', native_length_raw=2, sequence_ms=125, views={
            str(v): [dict(frame=f'pose{8-v if v>4 else v}', duration_ms=125,
                          mirrored=v>4, native_scale=1)] for v in range(8)})
        actions = {'walk': action}
        return dict(native_group_bindings={'1': {'actions': {'walk': source}}},
                    animations_by_palette={'1': actions}, animations=actions,
                    variants={'1': {'exact_base_bypass': True}}, frames={f'pose{v}': {} for v in range(5)})

    def test_animation_gate_detects_timing_scale_direction_and_alias_errors(self):
        manifest = self.animation_fixture()
        self.assertEqual(validate_animation_bindings(manifest), [])
        for key, value in [('duration_ms', 100), ('native_scale', .5), ('mirrored', False), ('frame', 'pose2')]:
            changed = copy.deepcopy(manifest)
            changed['animations']['walk']['views']['7'][0][key] = value
            self.assertTrue(validate_animation_bindings(changed), key)
        changed = copy.deepcopy(manifest)
        del changed['animations']['walk']['views']['6']
        self.assertTrue(validate_animation_bindings(changed))
        changed = copy.deepcopy(manifest)
        changed['animations'] = {}
        self.assertTrue(validate_animation_bindings(changed))

    def test_legacy_action_scale_and_native_null_binding(self):
        manifest = self.animation_fixture()
        source = manifest['native_group_bindings']['1']['actions']['walk']
        manifest['native_group_bindings'] = {'native': source}
        action = manifest['animations']['walk']
        action['native_frame_scale'] = 1
        for steps in action['views'].values():
            del steps[0]['native_scale']
        self.assertEqual(validate_animation_bindings(manifest), [])
        manifest['native_group_bindings']['null'] = dict(sprite_name='null', frames=[])
        manifest['animations']['corpse'] = dict(native_group='null', no_image=True,
                                                views={str(v): [] for v in range(8)})
        self.assertEqual(validate_animation_bindings(manifest), [])
        manifest['animations']['corpse']['views']['0'] = action['views']['0']
        self.assertTrue(validate_animation_bindings(manifest))

    def test_native_and_cropped_coordinates_including_mirrors(self):
        for width in (243, 244, 369, 370):
            for height in (281, 282):
                for anchor in ('bottom-center', 'center'):
                    divisor = 2 if anchor == 'center' else 1
                    reference = [(370-width)//2, (400-height)//divisor]
                    exact, origin, correction = export_placement(
                        [370, 400], [width, height], reference, [-20, -12], anchor=anchor)
                    self.assertEqual(correction, [(370-width) % 2, (400-height) % divisor])
                    for mirrored in (False, True):
                        sign = -1 if mirrored else 1
                        for x, y in ((0, 0), (17, 35), (width, height)):
                            # Register into the legacy canvas, then crop at an arbitrary origin.
                            aligned = [2*(x+reference[0])+20, 2*(y+reference[1])+12]
                            crop_origin = [origin[0]+7, origin[1]+9]
                            texel = [aligned[0]-7, aligned[1]-9]
                            exported = [sign*((crop_origin[0]+texel[0])/2-185),
                                        400/divisor-(crop_origin[1]+texel[1])/2]
                            native = [sign*(x-width/2), height/divisor-y]
                            self.assertEqual(exported, native)
                    # Re-export from the same registration basis is idempotent.
                    self.assertEqual(export_placement([370, 400], [width, height], reference,
                                                     [-20, -12], anchor=anchor)[1], origin)
                    self.assertEqual(export_placement([370, 400], [width, height], exact,
                                                     origin, anchor=anchor)[1], origin)

    def test_unrepresentable_tier_is_rejected(self):
        with self.assertRaises(ValueError):
            export_placement([370, 400], [243, 281], [63, 119], [0, 0], tier=1)

    def test_acceptance_rejects_rounded_or_double_applied_origin(self):
        frame = dict(source_canvas=[243, 281], native_offset=[63, 119],
                     aligned_canvas_origin_px=[0, 0], crop_in_aligned_px=[10, 20, 40, 60],
                     crop_origin_px=[10, 20], atlas_xywh=[100, 200, 30, 40])
        manifest = dict(pixels_per_logical_pixel=2, logical_canvas=[370, 400], logical_pivot=[185, 400],
                        frames={'pose': frame})
        registration = {'pose': dict(canvas_origin_px=[0, 0])}
        self.assertTrue(validate_manifest(manifest, registration))
        frame.update(native_offset=[63.5, 119], registration_native_offset=[63, 119],
                     aligned_canvas_origin_px=[1, 0], crop_origin_px=[11, 20])
        self.assertEqual(validate_manifest(manifest, registration), [])
        manifest['logical_pivot'][0] += 0.5
        self.assertTrue(validate_manifest(manifest, registration))
        manifest['logical_pivot'][0] -= 0.5
        frame.update(aligned_canvas_origin_px=[2, 0], crop_origin_px=[12, 20])
        self.assertTrue(validate_manifest(manifest, registration))


if __name__ == '__main__':
    unittest.main()
