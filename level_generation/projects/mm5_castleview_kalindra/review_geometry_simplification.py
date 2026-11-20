"""Validate the simplification against the preserved accepted world, including untouched geometry and bindings."""
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent
REVIEW = PROJECT/'review/geometry_simplification_v1'
sys.path.insert(0, str(PROJECT))
from audit_geometry_cost import model_metrics, parse_odm_file


def review():
    before = REVIEW/'before'
    relative = Path('implementation/runtime/worlds/mm5/maps/mm5_sw.odm')
    old = parse_odm_file(before/relative)['payload']
    new = parse_odm_file(PROJECT/relative)['payload']
    read = lambda path: json.loads(path.read_text())
    source = Path('implementation/source/mm5_sw.semantic.json')
    old_semantic, semantic = read(before/source), read(PROJECT/source)
    allowed = {'skyrope', 'kramer', 'river_crossing', 'reger_crossing'}
    allowed.update(p['id'] for p in semantic['props']
                   if p.get('kind') in ['town chest', 'source well', 'message bottle', 'melon patch'])
    unchanged_fields = []
    for key in old:
        if key not in ['bmodels', 'total_faces_count']:
            assert old[key] == new[key], ('Unrelated native field changed', key)
            unchanged_fields.append(key)
    assert len(old['bmodels']) == len(new['bmodels']) == len(semantic['bmodels']) == 326
    assert new['total_faces_count'] == sum(len(m['faces']) for m in new['bmodels'])
    events = lambda s: {e['semantic_id']: {k:v for k,v in e.items() if k != 'faces'} for e in s['events']}
    assert events(old_semantic) == events(semantic), 'Interaction identity or ownership changed'
    assert (before/'implementation/runtime/worlds/mm5/events/maps/mm5_sw.lua').read_bytes() == (
        PROJECT/'implementation/runtime/worlds/mm5/events/maps/mm5_sw.lua').read_bytes(), 'Lua behavior changed'
    records = []
    totals = [0, 0]
    changed = []
    for a, b, meaning in zip(old['bmodels'], new['bmodels'], semantic['bmodels']):
        assembly = meaning['assembly']
        am, bm = model_metrics(a), model_metrics(b)
        totals[0] += am['triangles']
        totals[1] += bm['triangles']
        assert bm['degenerateFanTriangles'] == 0, ('Degenerate fan', assembly, b['index'])
        if a != b:
            assert assembly in allowed, ('Untargeted model changed', assembly)
            assert bm['triangles'] < am['triangles'], ('No reduction', assembly)
            assert set(am['trianglesByTexture']) == set(bm['trianglesByTexture']), ('Material change', assembly)
            changed.append(b['index'])
        records.append({'index':b['index'], 'assembly':assembly, 'beforeFaces':am['faces'],
                        'afterFaces':bm['faces'], 'beforeTriangles':am['triangles'], 'afterTriangles':bm['triangles']})
    for prop in semantic['props']:
        if prop.get('kind') == 'melon patch':
            previous = next(p for p in old_semantic['props'] if p['id'] == prop['id'])
            for key in ['fruit', 'leaves', 'frontOrigin', 'eventId', 'fruitFaceRanges']:
                assert prop[key] == previous[key], (prop['id'], key)
    report = {'beforeNativeSha256':hashlib.sha256((before/relative).read_bytes()).hexdigest(),
              'nativeSha256':hashlib.sha256((PROJECT/relative).read_bytes()).hexdigest(),
              'beforeTriangles':totals[0], 'afterTriangles':totals[1], 'savedTriangles':totals[0]-totals[1],
              'unchangedNativeFields':unchanged_fields, 'changedModelIndices':changed,
              'unchangedModels':326-len(changed), 'eventsRetained':len(semantic['events']),
              'luaByteIdentical':True, 'zeroDegenerateFanTriangles':True, 'models':records,
              'limits':'Structural regression checks; native image, click and movement review are separate.'}
    (REVIEW/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print({k:v for k,v in report.items() if k not in ['models', 'changedModelIndices', 'unchangedNativeFields']})


if __name__ == '__main__':
    review()
