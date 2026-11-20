"""Explicit MM8 item selections for the two test maps; no shared item-table mutation."""
import csv
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
POOLS = {
    'lg01.odm': [5, 10, 15, 20, 25, 35, 45, 55, 60, 65, 70, 75, 88, 93, 97, 98, 103, 108, 125, 135, 145, 172],
    'lg02.blv': [4, 5, 14, 15, 19, 24, 25, 34, 35, 44, 54, 59, 64, 65, 69, 74, 87, 92, 93, 96, 102, 107, 125, 135],
}
FIXED = {'lg01.odm': [98, 103, 15, 55], 'lg02.blv': [93, 108, 65, 10]}


def apply_reward_policy(map_file, containers):
    for container in containers:
        fixed = FIXED[map_file][container['container_id']]
        container['fixed_items'] = [{'slot': 1, 'raw_mm9_item_id': 0, 'item_id': fixed}]
        container['random_item_pool'] = [item_id for item_id in POOLS[map_file] if item_id != fixed]
        container['random_item_count'] = 3 if map_file == 'lg01.odm' else 2
    table = ROOT / 'assets_dev/engine/data_tables/items.txt'
    with table.open(encoding='cp1252', newline='') as stream:
        rows = {int(row[0]): row for row in csv.reader(stream, delimiter='\t') if row and row[0].isdigit()}
    item_ids = sorted({item for pool in list(POOLS.values()) + list(FIXED.values()) for item in pool})
    assert all(0 < item < 185 and (ROOT/'assets_dev/engine/icons'/(rows[item][1]+'.bmp')).exists()
               for item in item_ids)
    manifest = dict(source_table=str(table.relative_to(ROOT)), source_table_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),
                    maps={name: dict(pool=POOLS[name], fixed_by_chest=FIXED[name], map_treasure=6 if name=='lg01.odm' else 5,
                                     draws=3 if name=='lg01.odm' else 2) for name in POOLS},
                    items={str(item): dict(mm8_source_item_id=item, name=rows[item][2], icon=rows[item][1],
                                          base_value=int(rows[item][3])) for item in item_ids},
                    policy='Native positive records: guaranteed MM8 equipment plus seeded draws without replacement. '
                           'Explicit pools bypass merged tier selection and random enchantment. Outdoor picks top ordinary '
                           'equipment; indoor mixes upper-middle equipment with a guaranteed final Headsman’s Reaver. '
                           'Map treasure6/5 still governs other native rewards; fixed chest gold1500–2250/750–1500. '
                           'MMerge global metaquest hooks remain active: an eligible party may find the existing '
                           'cross-continent Letter for YOU; it is not a generated map reward or a copied original map event.')
    (PROJECT/'source/reward_registry.json').write_text(json.dumps(manifest, indent=2)+'\n')
