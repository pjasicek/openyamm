"""Small fixtures for the staged decoration audit; no maps or stage files are changed."""
import unittest

from check_decoration_ids import compare_entities


class DecorationIdChecks(unittest.TestCase):
    def test_indoor_uses_marker_name_and_zero_based_native_id(self):
        ids = {'hes_lamp': 674, 'd07_cable_1': 675}
        source = [{'id': 'hes_lamp_0', 'decoration_list_id': 999}, {'id': 'd07_cable_1_1'}]
        native = [dict(index=0, name='d07_cable_1_1', decoration_list_id=674),
                  dict(index=1, name='hes_lamp_0', decoration_list_id=673)]
        rows = compare_entities(native, source, ids, True)
        self.assertEqual([row['expected'] for row in rows], ['d07_cable_1', 'hes_lamp'])
        self.assertTrue(all(not row['problem'] for row in rows))
        native[0]['decoration_list_id'] = 673
        self.assertEqual(compare_entities(native, source, ids, True)[0]['problem'], 'wrong decoration ID')
        native[0]['decoration_list_id'] = 14
        self.assertEqual(compare_entities(native, source, ids, True)[0]['problem'], 'wrong decoration ID')

    def test_outdoor_repeated_names_use_placement_indices(self):
        ids = {'hes_lamp': 674, 'hes_crate': 675}
        source = [dict(entity_index=0, name='Party Start', position=dict(x=0, y=0, z=0)),
                  dict(entity_index=1, name='hes_lamp', position=dict(x=1, y=0, z=0)),
                  dict(entity_index=2, name='hes_lamp', position=dict(x=2, y=0, z=0))]
        native = [dict(index=e['entity_index'], name=e['name'], position=e['position'],
                       decoration_list_id=14 if i == 0 else 673) for i, e in enumerate(source)]
        self.assertEqual(len(compare_entities(native, source, ids, False)), 2)
        native[2]['decoration_list_id'] = 674
        rows = compare_entities(native, source, ids, False)
        self.assertEqual([row['problem'] for row in rows], ['', 'wrong decoration ID'])
        native[1]['position'] = dict(x=9, y=0, z=0)
        self.assertIn('position differs', compare_entities(native, source, ids, False)[0]['problem'])

    def test_missing_or_ambiguous_source_fails(self):
        ids = {'hes_lamp': 674}
        native = [dict(index=0, name='missing_0', decoration_list_id=673)]
        source = [{'id': 'hes_lamp_0'}]
        self.assertEqual(compare_entities(native, source, ids, True)[0]['problem'], 'no matching source placement')
        with self.assertRaises(ValueError):
            compare_entities(native, [], ids, True)
        with self.assertRaises(ValueError):
            compare_entities(native * 2, source * 2, ids, True)


if __name__ == '__main__':
    unittest.main()
