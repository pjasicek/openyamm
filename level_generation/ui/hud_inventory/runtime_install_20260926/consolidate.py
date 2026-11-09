"""Consolidate reviewed icons without altering earlier receipts; install only verified exports."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote
from PIL import Image

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
PRIOR = HUD / 'finalization_20260926'
sys.path.insert(0, str(HUD))
from queue import Queue, save


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().removesuffix(';'))


def collect(q):
    audit = read(PRIOR / 'icon_coverage.json')
    records = {t: copy.deepcopy(r) for t, r in audit['approved'].items()
               if q.targets[t]['namespace'] != 'worlds/mm9'}
    catalog = js(HUD / 'paperdoll_review/catalog.js')
    for row in audit['blockers']:
        target = row['target']
        if row['status'] == 'paperdoll_background_needs_approval':
            asset = catalog['assets'][Path(row['source']).stem]
            path = (HUD / 'paperdoll_review' / unquote(asset['candidate'].split('?')[0])).resolve()
            authority = 'Explicit user acceptance of all displayed remaining backgrounds, 2026-09-26'
            assert sha(path) == asset['candidateHash']
        else:
            assert target == 'engine--icons--7item344.bmp'
            path = OUT / 'shadow_mask/7item344.png'
            authority = ('New missing-sprite restoration under user authorization to finish the slice; '
                         'agent visual review of complete mask/straps at 100x110. No earlier user image signoff claimed.')
        records[target] = dict(target=target, artifact=str(path), sha256=sha(path),
            source_sha256=q.targets[target]['source_sha256'], authority=authority,
            x2_size=q.targets[target]['x2_size'])
    for row in audit['files']:
        if row['status'] != 'approved_identical_source_alias':
            continue
        target = row['target']
        source = ROOT / row['source']
        assert sha(source) == row['source_sha256'] == sha(ROOT / row['canonical_source'])
        records[target] = dict(target=target, artifact=row['approved_artifact'], sha256=row['approved_sha256'],
            source_sha256=q.targets[target]['source_sha256'], x2_size=q.targets[target]['x2_size'],
            authority='Same-name byte-identical native alias of approved artwork', canonical_source=row['canonical_source'])
    for target, record in records.items():
        contract = q.targets[target]
        assert sha(ROOT / contract['source_path']) == record['source_sha256'] == contract['source_sha256'], target
        path = Path(record['artifact'])
        assert sha(path) == record['sha256'], path
        with Image.open(path) as im:
            im.load()
            assert list(im.size) == contract['x2_size'], target
        record.update(source=contract['source_path'], runtime_output_path=contract['runtime_output_path'])
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accept', action='store_true')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    with (HUD / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = Queue()
        if args.install and q.state.get('accepted_icon_index'):
            current = read(ROOT / q.state['accepted_icon_index']['path'])['records']
            historical = read(OUT / 'accepted.json')['records']
            if any(current.get(t, {}).get('sha256') != r['sha256'] for t, r in historical.items()):
                raise SystemExit('This historical snapshot is superseded. Redeploy the current accepted workspace with '
                                 'python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install')
        accepted_path = OUT / 'accepted.json'
        if accepted_path.exists():
            records = read(accepted_path)['records']
            for target, record in records.items():
                assert sha(Path(record['artifact'])) == record['sha256']
                assert all(q.accepted(c) for c in q.target_cells[target]), target
        else:
            records = collect(q)
            if not args.accept:
                print(json.dumps(dict(validated=len(records), mutation=False)))
                return
            if (OUT / 'checkpoint.before.json').exists():
                assert sha(q.state_path) == sha(OUT / 'checkpoint.before.json'), 'Ledger changed during import'
            else:
                shutil.copy2(q.state_path, OUT / 'checkpoint.before.json')
            authority = dict(schema='openyamm-icon-acceptance-v1', date='2026-09-26',
                instruction='OK accepted everything, ledger it and continue with the overall acceptance and new icons preparation.',
                prior_coverage_sha256=sha(PRIOR / 'icon_coverage.json'),
                shadow_mask='Newly restored omitted image; agent visually reviewed, separate from prior user approvals.',
                offsets='All original placement/fit receipts retained; item_visuals.txt imports their active values.')
            save(OUT / 'authority.json', authority)
            for target, record in records.items():
                contract = q.targets[target]
                destination = OUT / 'stage' / Path(contract['runtime_output_path']).relative_to('assets_dev')
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(record['artifact'], destination)
                destination.chmod(0o644)
                receipt = OUT / 'receipts' / (target + '.json')
                save(receipt, record)
                record['reviewed_artifact'] = record['artifact']
                record['artifact'] = str(destination)
                evidence = {str(receipt):sha(receipt), str(OUT / 'authority.json'):sha(OUT / 'authority.json')}
                cells = q.target_cells[target]
                if len(cells) == 1:
                    cell = cells[0]
                    q.state['cells'][cell] = dict(status='accepted', artifact=str(destination), sha256=record['sha256'],
                        acceptance_method='consolidated_review_receipts_20260926', layout_sha256=q.layout_hash(cell),
                        dependency_cells={}, evidence_hashes=evidence,
                        review=dict(authority=record['authority'], decision=str(receipt)))
                else:
                    assert target == 'engine--icons--sprites.pcx' and len(cells) == 187
                    assert all(q.accepted(c) for c in cells)
                staged = dict(target=target, source_path=contract['source_path'], source_sha256=record['source_sha256'],
                    artifact=str(destination), sha256=record['sha256'], native_size=contract['native_size'],
                    x2_size=contract['x2_size'], runtime_output_path=contract['runtime_output_path'],
                    cells={c:q.state['cells'][c]['sha256'] for c in cells}, review=dict(authority=record['authority']),
                    evidence_hashes=evidence, status='accepted_staged')
                q.state.setdefault('staged_targets', {})[target] = staged
                q.state.setdefault('reconstructed_targets', {})[target] = dict(target=target, path=str(destination),
                    sha256=record['sha256'], size=contract['x2_size'], cells=staged['cells'], status='accepted_full_canvas')
                excluded = q.state.get('user_excluded_targets', {}).get(target)
                if excluded:
                    # Only source-identical aliases supersede a previous duplicate exclusion.
                    assert 'canonical_source' in record, (target, excluded)
                    q.state.setdefault('exclusion_history', {})[target] = excluded
                    del q.state['user_excluded_targets'][target]
                if target in q.state.get('restoration_inventory', {}):
                    q.state['restoration_inventory'][target].update(status='accepted', canonical_artifact=str(destination),
                        canonical_sha256=record['sha256'], acceptance_receipt=str(receipt))
            save(q.state_path, q.state)
            save(q.storage_root() / 'exports/manifest.json', dict(targets=list(q.state['staged_targets'].values())))
            save(accepted_path, dict(records=records, count=len(records), authority=str(OUT / 'authority.json')))
        if args.install:
            installed = []
            for target, record in records.items():
                destination = ROOT / record['runtime_output_path']
                if destination.exists() and sha(destination) != record['sha256']:
                    backup = OUT / 'previous_runtime' / destination.relative_to(ROOT / 'assets_dev')
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    if backup.exists():
                        assert sha(backup) == sha(destination)
                    else:
                        shutil.copy2(destination, backup)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(record['artifact'], destination)
                destination.chmod(0o644)
                assert sha(destination) == record['sha256']
                installed.append(dict(target=target, path=record['runtime_output_path'], sha256=record['sha256']))
            save(OUT / 'installed.json', dict(count=len(installed), records=installed))
        print(json.dumps(dict(accepted=len(records), installation_performed_this_run=args.install, ledger_sha256=sha(q.state_path))))


if __name__ == '__main__':
    main()
