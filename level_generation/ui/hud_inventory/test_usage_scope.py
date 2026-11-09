import unittest

from audit_usage_scope import OUT, ROOT, apply_hold_review, canonical_key, classify
from review_usage_holds import resolve
import json
from pathlib import Path
import re


class UsageScopeTests(unittest.TestCase):
    def test_explicit_unused_ui(self):
        for name in ('6arrowl1', '6backhand', '6bardata', '6book', '6buttyes1', '6convol00', 'x_ok1', 'wtr009'):
            self.assertEqual(classify(name, [], []), 'excluded_legacy_ui')

    def test_reference_wins_over_prefix(self):
        self.assertEqual(classify('6book2', [{'source': 'items.txt'}], []), 'referenced_candidate')
        self.assertEqual(classify('wtr009', [{'source': 'live.yml'}], []), 'referenced_candidate')

    def test_dynamic_and_unknown_are_not_unused(self):
        self.assertEqual(classify('npc0001', [], [{'kind': 'numeric'}]), 'dynamic_consumer_candidate')
        self.assertEqual(classify('outa1', [], []), 'usage_audit_hold')

    def test_owner_policy(self):
        engine = {'source_path': 'assets_dev/engine/icons/npc0001.bmp'}
        world = {'source_path': 'assets_dev/worlds/mm6/icons/npc0001.bmp'}
        self.assertLess(canonical_key(world), canonical_key(engine))
        engine['source_path'] = engine['source_path'].replace('npc0001', 'wand1')
        world['source_path'] = world['source_path'].replace('npc0001', 'wand1')
        self.assertLess(canonical_key(engine), canonical_key(world))

    def test_reviewed_cohort_is_complete_and_specific(self):
        review = json.loads((OUT / 'usage_hold_review.json').read_text())
        self.assertEqual(len(review['files']), 1882)
        self.assertEqual(len({r['source_path'] for r in review['files']}), 1882)
        self.assertEqual(review['statuses'], {'excluded_unreferenced_art': 1829,
                                             'dynamic_consumer_candidate': 53})
        for row in review['files']:
            self.assertEqual(len(row['source_sha256']), 64)
            self.assertTrue(row['reason'])

    def test_review_does_not_override_positive_evidence(self):
        row = dict(source_path='test', source_sha256='original', status='referenced_candidate',
                   restoration_active=True)
        decision = dict(source_sha256='original', status='excluded_unreferenced_art')
        apply_hold_review(row, decision)
        self.assertEqual(row['status'], 'referenced_candidate')
        self.assertTrue(row['restoration_active'])
        row['source_sha256'] = 'changed'
        with self.assertRaises(ValueError):
            apply_hold_review(row, decision)

    def test_context_state_and_unknown_family(self):
        row = dict(source_path='context_talk_pressed.png', historical_treatment='ui_state_set',
                   references=[], dynamic_evidence=[])
        self.assertEqual(resolve(row)[0], 'dynamic_consumer_candidate')
        row.update(source_path='unreviewed.bmp', historical_treatment=None)
        with self.assertRaises(ValueError):
            resolve(row)

    def test_excluded_table_families_are_not_currently_selected(self):
        review = json.loads((OUT / 'usage_hold_review.json').read_text())
        tables = ROOT / 'assets_dev/engine/data_tables'
        items = {f[1].lower() for line in (tables / 'items.txt').read_text(errors='replace').splitlines()
                 if len(f := line.split('\t')) > 1 and f[0].isdigit()}
        dolls = [f for line in (tables / 'character_data.txt').read_text().splitlines()
                 if len(f := line.split('\t')) > 22 and f[0].isdigit()]
        doll_assets = {f[i].lower() for f in dolls for i in (*range(8, 15), 17, 18)}
        prefixes = {f[19].lower() for f in dolls}
        for row in review['files']:
            name = Path(row['source_path']).stem
            if row['rule'] == 'unselected_equipment_layer':
                supported = re.fullmatch(r'(.+)v[1-5]a?', name)
                self.assertFalse(supported and supported[1] in items, name)
            elif row['rule'] == 'unselected_item_art':
                self.assertNotIn(name, items)
            elif row['rule'] == 'unselected_paperdoll_part':
                self.assertNotIn(name, doll_assets)
            elif row['rule'] == 'unselected_portrait_prefix':
                self.assertNotIn(name[:-2], prefixes)


if __name__ == '__main__':
    unittest.main()
