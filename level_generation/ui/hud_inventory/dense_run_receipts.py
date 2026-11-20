"""Local receipts for built-in-tool dense jobs. This helper never calls an image API."""
import argparse
import datetime
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image
from dense_bundles import HERE, ROOT, read, sha, save
from catalogue_dense_returns import catalogue

BATCH = HERE/'chat_bundles/dense64_20260916'
ORDER = ['pc', 'npc_house', 'inventory', 'small_ui', 'legacy_small']


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def progress(folder):
    path = folder/'outputs/progress.json'
    return read(path) if path.exists() else read(folder/'progress.template.json')


def checkpoint(folder, data):
    path = folder/'outputs/progress.json'
    tmp = path.with_suffix('.tmp')
    save(tmp, data)
    tmp.replace(path)


def next_sheet():
    bundles = read(BATCH/'catalogue.json')['bundles']
    bundles.sort(key=lambda b: (ORDER.index(b['bundle_id'][8:-4]), b['bundle_id']))
    for bundle in bundles:
        folder = BATCH/bundle['bundle_id']
        state = progress(folder)
        for sheet in read(folder/'manifest.json')['sheets']:
            entry = state['sheets'][sheet['id']]
            if entry['status'] in ('in_progress', 'submission_uncertain'):
                raise RuntimeError(f'Reconcile pending submission: {folder.name}/{sheet["id"]}')
            if entry['status'] == 'unattempted':
                return dict(bundle=folder.name, sheet=sheet['id'])
    return dict(done=True)


def prepare(bundle, sid):
    folder = BATCH/bundle
    gate_path = BATCH/'generation_gate.json'
    gate = read(gate_path) if gate_path.exists() else None
    if gate:
        assert gate['status'] == 'ready', 'Resolve the restoration-detail gate before further generation'
    record = next(b for b in read(BATCH/'catalogue.json')['bundles'] if b['bundle_id'] == bundle)
    assert sha(folder/'manifest.json') == record['manifest_sha256']
    manifest = read(folder/'manifest.json')
    sheet = next(s for s in manifest['sheets'] if s['id'] == sid)
    for key in ('reference', 'prompt', 'layout'):
        assert sha(folder/sheet[key]) == sheet[key+'_sha256']
    for ref in sheet['identity_references']:
        assert sha(folder/ref['path']) == ref['sha256']
    layout = read(folder/sheet['layout'])
    state = read(HERE/'checkpoint/state.json')
    assert [c['id'] for c in layout['cells']] == sheet['cells']
    for cell in layout['cells']:
        assert sha(ROOT/cell['member']['source_path']) == cell['source_sha256']
        assert cell['id'] not in state['cells']
        assignment = state['external_assignments'][cell['id']]
        assert assignment['bundle'] == bundle and assignment['status'] == 'assigned'
    data = progress(folder)
    entry = data['sheets'][sid]
    assert entry['status'] == 'unattempted' and not entry['raw_path']
    assert not list((folder/'outputs/raw').glob(sid+'.*')), 'Recover existing raw instead'
    prompt = folder/'outputs/prompts'/f'{sid}.txt'
    prompt.parent.mkdir(parents=True, exist_ok=True)
    policy_path = BATCH/'RESTORATION_DETAIL_V2.txt'
    if policy_path.exists():
        prompt.write_text(policy_path.read_text()+'\n\n'+(folder/sheet['prompt']).read_text())
        entry.update(prompt_policy='restoration_detail_v2', prompt_policy_sha256=sha(policy_path),
                     original_prepared_prompt_sha256=sheet['prompt_sha256'])
    else:
        shutil.copy2(folder/sheet['prompt'], prompt)
    args = dict(prompt=prompt.read_text(), referenced_image_paths=[str(folder/sheet['reference'])]+
                [str(folder/r['path']) for r in sheet['identity_references']])
    save(folder/'outputs'/f'{sid}.submission.json', args)
    entry.update(status='in_progress', submitted_prompt_path=str(prompt.relative_to(folder)),
                 submitted_prompt_sha256=sha(prompt), tool='image_gen.imagegen', started_at=now())
    checkpoint(folder, data)
    if gate:
        gate.update(status='submission_in_progress', bundle=bundle, sheet=sid, updated_at=now())
        save(gate_path, gate)
    return dict(bundle=bundle, sheet=sid, targets=len(sheet['cells']), tool_args=args,
                reference_size=sheet['reference_size'], group=sheet['group'])


def record(bundle, sid, source, notes):
    folder = BATCH/bundle
    data = progress(folder)
    entry = data['sheets'][sid]
    assert entry['status'] == 'in_progress'
    source = Path(source).resolve()
    with Image.open(source) as im:
        im.load()
        size = list(im.size)
        suffix = {'PNG':'.png', 'JPEG':'.jpg', 'WEBP':'.webp'}[im.format]
    destination = folder/'outputs/raw'/(sid+suffix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists()
    shutil.copy2(source, destination)
    entry.update(status='generated_needs_review', raw_path=str(destination.relative_to(folder)),
                 raw_sha256=sha(destination), actual_dimensions=size, original_filename=str(source),
                 finished_at=now(), notes=notes or 'Raw retained; visual review pending.')
    checkpoint(folder, data)
    gate_path = BATCH/'generation_gate.json'
    if gate_path.exists():
        gate = read(gate_path)
        gate.update(status='needs_visual_detail_review', bundle=bundle, sheet=sid, updated_at=now())
        save(gate_path, gate)
    return dict(bundle=bundle, sheet=sid, raw=str(destination), size=size)


def package(bundle):
    folder = BATCH/bundle
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive = BATCH/'returns'/f'{bundle}_{stamp}.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    files = [folder/'manifest.json'] + sorted(p for p in (folder/'outputs').rglob('*') if p.is_file())
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, path.relative_to(folder))
    destination, report = catalogue(BATCH, archive, HERE/'dense_returns')
    return dict(archive=str(archive), inventory=str(destination/'index.html'),
                returned=sum('raw' in s for s in report['sheets']),
                unreturned=sum(s['status']=='unreturned' for s in report['sheets']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['next', 'prepare', 'record', 'note', 'review', 'fail', 'package'])
    parser.add_argument('--bundle')
    parser.add_argument('--sheet')
    parser.add_argument('--source')
    parser.add_argument('--notes', default='')
    parser.add_argument('--status', default='failed')
    parser.add_argument('--detail', choices=['pass', 'fail', 'uncertain'])
    args = parser.parse_args()
    if args.action == 'next':
        result = next_sheet()
    elif args.action == 'prepare':
        result = prepare(args.bundle, args.sheet)
    elif args.action == 'record':
        result = record(args.bundle, args.sheet, args.source, args.notes)
    elif args.action == 'package':
        result = package(args.bundle)
    else:
        folder = BATCH/args.bundle
        data = progress(folder)
        entry = data['sheets'][args.sheet]
        entry['notes'] = args.notes
        if args.action == 'review':
            assert args.detail and args.notes and entry.get('raw_path')
            entry.update(restoration_detail_review=args.detail, detail_reviewed_at=now())
            gate_path = BATCH/'generation_gate.json'
            gate = read(gate_path)
            assert gate.get('bundle') == args.bundle and gate.get('sheet') == args.sheet
            gate.update(status='ready' if args.detail == 'pass' else 'paused_detail_failure',
                        detail_review=args.detail, notes=args.notes, updated_at=now())
            save(gate_path, gate)
        if args.action == 'fail':
            assert args.status in ('failed', 'rejected', 'submission_uncertain')
            entry.update(status=args.status, finished_at=now())
        checkpoint(folder, data)
        result = dict(bundle=args.bundle, sheet=args.sheet, status=entry['status'])
    print(json.dumps(result))


if __name__ == '__main__':
    main()
