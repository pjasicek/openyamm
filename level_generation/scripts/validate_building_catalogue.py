"""One quick consistency check of catalogue sources, bindings, images and documentation links.

No game launch, Lua execution, behavioral simulation or renderer run.
"""
from pathlib import Path
import hashlib
import json
import re
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'level_generation/catalogues/mm8_ravenshore'


def validate():
    start = time.monotonic()
    data = json.loads((OUT / 'catalogue.json').read_text())
    textures = json.loads((OUT / 'textures.json').read_text())
    for source in data['sources'] + list(textures.values()):
        path = ROOT / source['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'], f'Stale source: {path}'
    models = data['models']
    assert [m['index'] for m in models] == list(range(data['coverage']['all_bmodels']))
    assert len(models) == 121
    cards = [m for m in models if m['catalogue_building']]
    assert len(cards) == data['coverage']['building_or_entry_parts'] == 84
    assert sum(m['has_active_entry'] for m in models) == data['coverage']['directly_enterable_parts'] == 67
    active_faces = 0
    for model in models:
        faces = {f['index']: f for f in model['face_records']}
        assert len(faces) == model['faces']
        for service in model['services']:
            event = data['events'][str(service['event'])]
            assert event['houses'] == [h['id'] for h in service['houses']]
            assert event['destinations'] == service['destinations']
            for face_id in service['active_faces']:
                assert faces[face_id]['event'] == service['event']
                assert not event['hint_only']
                active_faces += 1
            for face_id in service['label_only_faces']:
                label = data['events'][str(faces[face_id]['event'])]
                assert label['hint_only'] and label['label_for_event'] == service['event']
        if model['catalogue_building']:
            assert all(f['texture'].lower() in textures for f in faces.values())
            assert (OUT / 'models' / f'{model["index"]:03d}.md').is_file()
    expected = [(f'{m["index"]:03d}', [m['index']]) for m in cards]
    expected += [('assembly_' + a['id'], a['models']) for a in data['assembly_views']]
    for name, ids in expected:
        metadata = json.loads((OUT / 'images' / (name + '.json')).read_text())
        assert metadata['models'] == ids, f'Stale render: {name}'
        with Image.open(OUT / 'images' / (name + '.png')) as im:
            assert im.size == (800, 650)
            im.verify()
    links = 0
    documents = list(OUT.rglob('*.md')) + [ROOT / 'level_generation' / name for name in [
        'VISUAL_CALIBRATION.md', 'README.md', 'REVIEW_CHECKLIST.md', 'POPULATION_AND_COMPOSITION.md']]
    for path in documents:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('http:', 'https:', '#')):
                continue
            target = target.split('#')[0]
            assert (path.parent / target).exists(), f'Broken link in {path}: {target}'
            links += 1
    reference = next(s for s in data['scale_comparison'] if s['world'] == 'mm8')['samples']
    assert len(reference) == 70 and all((s['width'], s['height']) == (128, 256) for s in reference)
    result = dict(status='pass', bmodels=len(models), rendered_parts=len(cards),
        assemblies=len(data['assembly_views']), active_entry_faces=active_faces, local_links=links,
        source_files=len(data['sources']), textures=len(textures), elapsed_seconds=round(time.monotonic() - start, 3),
        scope='Static reference evidence only; no Lua execution or game scenarios. Visual review is separate.')
    (OUT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    validate()
