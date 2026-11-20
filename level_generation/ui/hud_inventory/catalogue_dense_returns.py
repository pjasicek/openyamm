"""Retain and inventory dense-bundle returns; never execute helpers or accept/install art."""
import argparse
import hashlib
import json
import html
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_relative(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('Unsafe relative path: '+name)
    return p


def catalogue(batch_root, archive_path, output):
    index = json.loads((batch_root/'catalogue.json').read_text())
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None, 'ZIP CRC failure'
        assert sum(x.file_size for x in archive.infolist()) < 4*1024**3, 'Unexpected archive size'
        names = set()
        for item in archive.infolist():
            safe_relative(item.filename)
            assert item.filename not in names, 'Duplicate ZIP entry'
            names.add(item.filename)
            assert not stat.S_ISLNK(item.external_attr >> 16), 'ZIP symlink'
        returned_bytes = archive.read('manifest.json')
        returned = json.loads(returned_bytes)
        bid = returned['bundle_id']
        known = next(x for x in index['bundles'] if x['bundle_id'] == bid)
        expected_path = batch_root/safe_relative(known['manifest'])
        assert sha(expected_path) == known['manifest_sha256'], 'Local manifest changed'
        assert returned_bytes == expected_path.read_bytes(), 'Returned manifest differs from issued input'
        manifest = json.loads(expected_path.read_text())
        progress = json.loads(archive.read('outputs/progress.json'))
        assert progress['bundle'] == bid
        assert set(progress['sheets']) <= {s['id'] for s in manifest['sheets']}, 'Unknown sheet ID'
        digest = sha(archive_path)
        destination = output/(bid+'-'+digest[:12])
        destination.mkdir(parents=True, exist_ok=True)
        incoming = destination/'incoming'
        for item in archive.infolist():
            if item.is_dir():
                continue
            target = incoming/safe_relative(item.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(item)
            if target.exists():
                assert target.read_bytes() == data, 'Retained content differs'
            else:
                target.write_bytes(data)
    retained_archive = destination/'return.zip'
    if retained_archive.exists():
        assert sha(retained_archive) == digest
    else:
        shutil.copy2(archive_path, retained_archive)
    report = dict(schema='openyamm.dense-intake.v1', bundle_id=bid, archive_sha256=digest,
                  archive=str(retained_archive), sheets=[], cells=[], accepted=0,
                  note='Retained raw results only. No production acceptance, fitting, installation or queue mutation.')
    consumed = set()
    for sheet in manifest['sheets']:
        entry = progress['sheets'].get(sheet['id'], {})
        name = entry.get('raw_path')
        if not name:
            report['sheets'].append(dict(id=sheet['id'], status='unreturned', worker_notes=entry.get('notes', '')))
            report['cells'].extend(dict(id=c, sheet=sheet['id'], status='unreturned') for c in sheet['cells'])
            continue
        rel = safe_relative(name)
        assert rel.parts[:2] == ('outputs', 'raw'), 'Raw must be under outputs/raw'
        assert name not in consumed, 'One raw path assigned to two sheets'
        consumed.add(name)
        raw = incoming/rel
        prompt_name = entry.get('submitted_prompt_path')
        assert prompt_name, 'Missing exact submitted prompt path'
        prompt_rel = safe_relative(prompt_name)
        assert prompt_rel.parts[:2] == ('outputs', 'prompts')
        prompt = incoming/prompt_rel
        assert prompt.is_file() and prompt.read_text().strip(), 'Missing/empty prompt'
        raw_hash, prompt_hash = sha(raw), sha(prompt)
        if entry.get('raw_sha256'):
            assert raw_hash == entry['raw_sha256']
        if entry.get('submitted_prompt_sha256'):
            assert prompt_hash == entry['submitted_prompt_sha256']
        with Image.open(raw) as im:
            im.load()
            size = list(im.size)
            actual_format = im.format
        if entry.get('actual_dimensions'):
            assert entry['actual_dimensions'] == size, 'Dimension receipt mismatch'
        layout_path = batch_root/bid/safe_relative(sheet['layout'])
        assert sha(layout_path) == sheet['layout_sha256']
        layout = json.loads(layout_path.read_text())
        reference_size = sheet['reference_size']
        estimated_sampling = min(2*size[0]/reference_size[0], 2*size[1]/reference_size[1])
        aspect_error = abs((size[0]/size[1])/(reference_size[0]/reference_size[1])-1)
        status = 'needs_cell_sampling_and_visual_review' if estimated_sampling >= 2 and aspect_error <= .02 else 'size_or_aspect_warning'
        row = dict(id=sheet['id'], status=status, raw=str(raw), raw_sha256=raw_hash,
                   actual_size=size, actual_format=actual_format, submitted_prompt=str(prompt),
                   submitted_prompt_sha256=prompt_hash, prompt_matches_prepared=prompt_hash==sheet['prompt_sha256'],
                   nominal_sampling_only=estimated_sampling, aspect_error=aspect_error,
                   worker_notes=entry.get('notes', ''), cells=sheet['cells'])
        report['sheets'].append(row)
        for cell in layout['cells']:
            report['cells'].append(dict(id=cell['id'], sheet=sheet['id'], status=status,
                source_sha256=cell['source_sha256'], native_size=cell['native_size'],
                x2_size=cell['x2_size'], reference_rect=cell['reference_rect'], raw=str(raw)))
    report['unreferenced_raw_files'] = [str(p.relative_to(incoming)) for p in (incoming/'outputs/raw').glob('*')
                                      if p.is_file() and str(p.relative_to(incoming)) not in consumed]
    (destination/'intake.json').write_text(json.dumps(report, indent=2)+'\n')
    cards = []
    for sheet in report['sheets']:
        picture = ''
        if 'raw' in sheet:
            relative = Path(sheet['raw']).relative_to(destination).as_posix()
            picture = f'<a href="{html.escape(relative, quote=True)}"><img src="{html.escape(relative, quote=True)}"></a>'
        cards.append(f'<article><h2>{html.escape(sheet["id"])}</h2><p>{html.escape(sheet["status"])}</p>{picture}</article>')
    (destination/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Dense return inventory</title>'
        '<style>body{font:16px sans-serif;background:#222;color:#eee}article{display:inline-block;vertical-align:top;'
        'width:460px;margin:12px}img{max-width:100%}a{color:#9cf}</style>'
        f'<h1>{html.escape(bid)}</h1><p>Raw return inventory. No artwork accepted. '
        '<a href="intake.json">Full cell inventory</a></p>'+''.join(cards))
    return destination, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    destination, report = catalogue(args.batch_root.resolve(), args.archive.resolve(), args.output.resolve())
    print(json.dumps(dict(intake=str(destination/'intake.json'), returned=sum('raw' in s for s in report['sheets']),
                         unreturned=sum(s['status']=='unreturned' for s in report['sheets']), accepted=0), indent=2))


if __name__ == '__main__':
    main()
