"""Read-only verification of accepted exports, archived sources and imported visual data."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from queue import Queue, save
from native_sources import native_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    q = Queue()
    accepted = read(OUT / 'accepted.json')['records']
    installed = read(OUT / 'installed.json')['records']
    archive = read(OUT / 'source_archive.json')
    assert len(accepted) == len(installed) == 9920
    for target, record in accepted.items():
        contract = q.targets[target]
        assert all(q.accepted(c) for c in q.target_cells[target]), target
        assert sha(Path(record['artifact'])) == sha(ROOT / record['runtime_output_path']) == record['sha256'], target
        with Image.open(ROOT / record['runtime_output_path']) as im:
            assert list(im.size) == contract['x2_size'] == [2*v for v in contract['native_size']], target
    for contract in q.targets.values():
        assert sha(native_source(contract['source_path'])) == contract['source_sha256'], contract['id']
    for record in archive['files'].values():
        assert sha(ROOT / record['archive']) == record['sha256']
    for root in archive['roots']:
        assert not (ROOT / 'assets_dev' / root).exists()
    mm9 = [r for r in read(HUD / 'finalization_20260926/icon_coverage.json')['files']
           if r['status'] == 'mm9_outside_restoration_scope']
    assert len(mm9) == 881 and all(sha(ROOT / r['source']) == r['source_sha256'] for r in mm9)
    expected_files = {r['runtime_output_path'] for r in accepted.values()}
    actual_files = {str(p.relative_to(ROOT)) for root in archive['roots']
                    for p in (ROOT / ('assets_dev/' + root + '_x2')).rglob('*') if p.is_file()}
    assert actual_files == expected_files, (actual_files-expected_files, expected_files-actual_files)
    lines = [s for s in (ROOT / 'assets_dev/engine/data_tables/item_visuals.txt').read_text().splitlines()
             if not s.startswith('#')]
    rows = list(csv.DictReader(lines, delimiter='\t'))
    placement_rows = {(int(r['ItemId']),int(r['DollType']),r['Slot']):r for r in rows if r['Kind']=='placement'}
    inventory_rows = {int(r['ItemId']):r for r in rows if r['Kind']=='inventory'}
    placements = read(HUD / 'finalization_20260926/placements.json')
    fit = read(HUD / 'finalization_20260926/inventory_fit.json')
    for key, record in placements.items():
        if key.startswith(('grip:', 'preview:')):
            continue
        r = placement_rows[(record['item_id'],record['doll_type'],record['slot'])]
        assert [int(r['X']),int(r['Y'])] == record['delta'], key
    assert len(placement_rows) == 726 and len(inventory_rows) == len(fit['records']) == 79
    for record in fit['records']:
        r = inventory_rows[record['item_id']]
        assert [int(r['CellsX']),int(r['CellsY'])] == record['cells']
        assert float(r['InventoryScale']) == record['draw_scale']
        assert float(r['JewelryScale']) == record.get('overlay_scale',1)
        assert all(size*record['draw_scale'] <= cells*32+0.00001
                   for size,cells in zip(record['native_size'],record['cells']))
    disposition = read(OUT / 'scope_disposition.json')
    assert set(disposition['targets']) == set(q.targets)
    retired = {t for t, status in disposition['targets'].items() if status == 'archived_unused'}
    assert retired == set(q.state['retired_targets']) and len(retired) == 3924
    assert not retired.intersection(accepted)
    assert all(t in q.blockers(q.jobs[q.members[q.target_cells[t][0]][0]]) for t in retired)
    report = dict(result='PASS',accepted_installed=len(accepted), retired_unused_targets=len(retired),
        packages=dict(Counter(q.targets[t]['namespace'] for t in accepted)),
        archived_original_files=len(archive['files']), all_frozen_native_sources_verified=len(q.targets),
        mm9_native_files_unchanged=len(mm9), placement_records_retained=len(placements),
        runtime_placements=len(placement_rows), inventory_fits=len(inventory_rows),
        changed_inventory_footprints=fit['changed_footprints'],
        offsets_sha256=sha(HUD / 'finalization_20260926/placements.json'),
        runtime_visual_table_sha256=sha(ROOT / 'assets_dev/engine/data_tables/item_visuals.txt'),
        ledger_sha256=sha(q.state_path), receipts_sha256=sha(OUT / 'accepted.json'),
        original_folders_outside_runtime=True, runtime_zip_packages_rebuilt=False)
    save(OUT / 'validation.json', report)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
