"""Proposed Equip X / Y (paperdoll grip anchors, logical pixels of the x1 icon) for every MM9 weapon and shield with
the new icons, from review/doll_grip/anchors_new.yml (scripts/check_doll_grip.py: the repo's anchor generator on the
new icons). Writes runtime/equip_anchors.tsv beside the current values; nothing is installed.
Usage: python3 scripts/equip_table.py"""
import csv
from pathlib import Path
import yaml

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[3]
anchors = yaml.safe_load((PROJECT.parent / 'review/doll_grip/anchors_new.yml').read_text())['items']
table = list(csv.reader((ROOT / 'assets_dev/worlds/mm9/data_tables/items.txt').open(encoding='utf-8'), delimiter='\t'))
header = next(i for i, row in enumerate(table) if row and row[0] == 'Item #')
out = [['Item #', 'Name', 'Equip Stat', 'Skill Group', 'Old X', 'Old Y', 'New X', 'New Y', 'Reference item', 'Method']]
for row in table[header + 1:]:
    item = dict(zip(table[header], row))
    raw = int(item.get('x_mm9_raw_item_id') or 0)
    if raw in anchors:
        a = anchors[raw]
        out.append([item['Item #'], item['Name'], item['Equip Stat'], item['Skill Group'], item['Equip X'], item['Equip Y'],
                    str(a['equip_anchor'][0]), str(a['equip_anchor'][1]), str(a['reference_item_id']), a['method']])
(PROJECT / 'runtime/equip_anchors.tsv').write_text(''.join('\t'.join(r) + '\n' for r in out))
print(len(out) - 1, 'weapons and shields')
