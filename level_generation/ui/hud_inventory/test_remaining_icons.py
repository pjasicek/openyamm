"""Packing invariants for remaining-icon preparation; no generated or accepted fixtures."""
import unittest

from prepare_remaining_icons import pack, reuse_key


def entry(index, kind='inventory_items', size=(32, 32), job='job', dependencies=None, mode='opaque_canvas'):
    target = dict(id=f't{index}', namespace='engine', treatment=kind, native_size=list(size),
                  source_sha256=f'sha{index}', compositing=dict(cleanup=mode, profiles=['hud'],
                  preserve_indexed_keys=False, fingerprints={'hud': {'rgba_sha256': f'pixels{index}'}}))
    member = dict(id=f'c{index}', target=target['id'], source_rect=[0, 0, *size],
                  method='imagegen_sheet', cleanup=mode)
    contract = dict(id=job, dependencies=dependencies or [], members=[member], family=['engine', kind, job])
    return dict(target=target, member=member, job=contract)


class RemainingPacking(unittest.TestCase):
    def test_dense_budget_and_unique_coverage(self):
        items = [entry(i) for i in range(130)]
        sheets, deterministic = pack(items)
        self.assertFalse(deterministic)
        self.assertEqual(sorted(len(s['entries']) for s in sheets), [2, 64, 64])
        self.assertEqual({e['member']['id'] for s in sheets for e in s['entries']}, {f'c{i}' for i in range(130)})
        self.assertTrue(all(s['grid']['predicted_sampling'] >= 2.15 for s in sheets))

    def test_portrait_identity_groups_share_dense_sheets(self):
        items = []
        for group, count in enumerate([49, 5, 5, 5, 5, 5, 5, 5, 6, 6, 4, 4, 4, 3, 1, 1, 1]):
            items.extend(entry(len(items) + i, 'player_portrait_frames', (59, 79),
                               job=f'portrait{group}',
                               dependencies=[dict(kind='accepted_seed_job', job=f'seed{group}')])
                         for i in range(count))
        sheets, _ = pack(items)
        self.assertEqual(len(sheets), 2)
        self.assertEqual(sorted(len(s['entries']) for s in sheets), [50, 64])
        self.assertTrue(all(s['grid']['predicted_sampling'] >= 2.15 for s in sheets))
        for group in range(17):
            self.assertEqual(sum(any(e['job']['id'] == f'portrait{group}' for e in s['entries'])
                                 for s in sheets), 1)

    def test_equal_opaque_consumers_do_not_force_singletons(self):
        a = entry(0, 'player_portrait_frames', (59, 79), job='a')
        b = entry(1, 'player_portrait_frames', (59, 79), job='b')
        b['target']['compositing']['profiles'].append('menu_bmp')
        b['target']['compositing']['fingerprints']['menu_bmp'] = dict(
            b['target']['compositing']['fingerprints']['hud'])
        sheets, _ = pack([a, b])
        self.assertEqual(len(sheets), 1)

    def test_large_background_stays_whole_and_is_flagged(self):
        sheets, _ = pack([entry(0, 'ui_background', (1672, 941))])
        self.assertEqual(len(sheets), 1)
        self.assertTrue(sheets[0]['requires_large_master'])
        self.assertEqual(sheets[0]['entries'][0]['member']['source_rect'], [0, 0, 1672, 941])

    def test_equipment_seed_and_body_groups_are_not_merged(self):
        items = [entry(i, 'fitted_equipment_variants', job=f'body{i}',
                       dependencies=[dict(kind='accepted_seed_job', job=f'seed{i}')]) for i in range(3)]
        sheets, _ = pack(items)
        self.assertEqual(len(sheets), 3)

    def test_whole_small_groups_can_share_a_sheet(self):
        sheets, _ = pack([entry(i, job=f'j{i}') for i in range(4)])
        self.assertEqual(len(sheets), 1)
        self.assertEqual(len(sheets[0]['entries']), 4)

    def test_spell_pairs_keep_adjacent_states_and_order(self):
        items = [entry(i, 'spell_icon_pair', (180, 180)) for i in range(8)]
        job = items[0]['job']
        job['members'] = [e['member'] for e in items]
        for e in items:
            e['job'] = job
        items[0]['member']['cleanup'] = 'alpha_cutout_or_effect'
        sheets, _ = pack(items)
        for s in sheets:
            self.assertEqual(s['grid']['columns'] % 2, 0)
            ids = [e['member']['id'] for e in s['entries']]
            self.assertEqual(len(ids) % 2, 0)
            for a, b in zip(ids[::2], ids[1::2]):
                self.assertEqual(int(b[1:]), int(a[1:]) + 1)

    def test_deterministic_atlas_is_not_imagegen(self):
        e = entry(0, 'registered_arcomage_atlas')
        e['member']['method'] = 'deterministic_font_regions'
        sheets, deterministic = pack([e])
        self.assertFalse(sheets)
        self.assertEqual(deterministic[0]['cells'], ['c0'])

    def test_reuse_requires_namespace_and_full_profile_match(self):
        a = entry(0)['target']
        b = dict(a, namespace='worlds/mm6')
        self.assertNotEqual(reuse_key(a), reuse_key(b))
        b = dict(a, compositing=dict(a['compositing'], fingerprints={'hud': {'rgba_sha256': 'different'}}))
        self.assertNotEqual(reuse_key(a), reuse_key(b))


if __name__ == '__main__':
    unittest.main()
