"""Read-only native/source geometry census for the accepted MM5 environment and MM8 references."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT/'review/geometry_cost_audit'
sys.path.insert(0, str(ROOT/'util'))
from map_export import parse_odm_file


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_metrics(model):
    sizes = collections.Counter()
    triangles = invisible = small = degenerate = 0
    textures = collections.Counter()
    for face in model['faces']:
        ids = face['vertex_indices']
        assert face['vertex_count'] == len(ids)
        points = [tuple(model['vertices'][i][axis] for axis in ['x', 'y', 'z']) for i in ids]
        count = max(0, len(points)-2)
        triangles += count
        if face['attributes'] & 0x2000:
            invisible += count
        textures[face['texture_name'].lower()] += count
        sizes[len(points)] += 1
        for i in range(1, len(points)-1):
            a = [points[i][j]-points[0][j] for j in range(3)]
            b = [points[i+1][j]-points[0][j] for j in range(3)]
            cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
            squared = sum(v*v for v in cross)
            degenerate += squared == 0
            small += 0 < squared < 4*64*64
    return {
        'faces': len(model['faces']), 'triangles': triangles, 'invisibleTriangles': invisible,
        'nonzeroTrianglesBelow64SquareUnits': small, 'degenerateFanTriangles': degenerate,
        'textureCount': len(textures), 'trianglesByTexture': dict(textures),
        'polygonSizes': dict(sizes), 'boundsSize': [model['bounds_max'][axis]-model['bounds_min'][axis]
                                                  for axis in ['x', 'y', 'z']],
    }


def main():
    native_path = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    native_hash = digest(native_path)
    release = json.loads((PROJECT/'delivery/latest.json').read_text())
    assert native_hash == release['nativeSha256'], 'Audit the accepted release, not an unreviewed intermediate.'
    native = parse_odm_file(native_path)['payload']
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    geometry = json.loads((PROJECT/'implementation/source/mm5_sw.geometry.yml').read_text())
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    identities = {r['id']: r for r in spec['buildings']+spec['props']+spec['bridges']+spec['gates']}
    models = []
    groups = {}
    assert len(native['bmodels']) == len(semantic['bmodels']) == len(geometry['bmodels'])
    for model, meaning, source in zip(native['bmodels'], semantic['bmodels'], geometry['bmodels']):
        assert model['index'] == meaning['index'] == source['runtime_bmodel_index']
        path = Path(source['source']['asset_path'])
        polygons = [line.split()[1:] for line in path.read_text().splitlines() if line.startswith('f ')]
        metrics = model_metrics(model)
        metrics.update({'index': model['index'], 'name': model['name'], 'assembly': meaning['assembly'],
                        'source': str(path.relative_to(PROJECT)), 'sourceSha256': digest(path),
                        'sourceFaces': len(polygons), 'sourceTriangles': sum(len(face)-2 for face in polygons)})
        metrics['sourceNativeCountsMatch'] = (metrics['faces'] == metrics['sourceFaces']
                                            and metrics['triangles'] == metrics['sourceTriangles'])
        models.append(metrics)
        identity = identities.get(meaning['assembly'], {})
        group = groups.setdefault(meaning['assembly'], {
            'id': meaning['assembly'], 'title': identity.get('title', meaning['assembly']),
            'kind': identity.get('kind', identity.get('form', 'infrastructure')),
            'models': [], 'faces': 0, 'triangles': 0, 'invisibleTriangles': 0,
            'nonzeroTrianglesBelow64SquareUnits': 0, 'degenerateFanTriangles': 0,
        })
        group['models'].append(model['index'])
        for key in ['faces', 'triangles', 'invisibleTriangles', 'nonzeroTrianglesBelow64SquareUnits',
                    'degenerateFanTriangles']:
            group[key] += metrics[key]
    total = sum(m['triangles'] for m in models)
    for group in groups.values():
        group['modelTriangleSharePercent'] = round(100*group['triangles']/total, 3)

    references = {}
    for label, map_name in [('Ravenshore', 'out02'), ('Garrote Gorge', 'out05')]:
        path = ROOT/'assets_dev/worlds/mm8/maps'/(map_name+'.odm')
        data = parse_odm_file(path)['payload']
        records = [{'index': m['index'], 'name': m['name'], **model_metrics(m)} for m in data['bmodels']]
        references[label] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path), 'models': records}

    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {'nativeSha256': native_hash, 'allSourceNativeCountsMatch': all(m['sourceNativeCountsMatch'] for m in models),
              'totals': {key: sum(m[key] for m in models) for key in
                         ['faces', 'triangles', 'invisibleTriangles', 'nonzeroTrianglesBelow64SquareUnits',
                          'degenerateFanTriangles']},
              'assemblies': sorted(groups.values(), key=lambda g: g['triangles'], reverse=True),
              'models': models, 'references': references,
              'method': 'Stored polygons and renderer triangle fans. Small triangles have nonzero area below 64 native square units; this is a geometric screening threshold, not a measured pixel size or defect.',
              'limits': 'No camera culling, GPU timings, draw-call inference, collider simplification or asset changes.'}
    (OUTPUT/'inventory.json').write_text(json.dumps(report, indent=2)+'\n')
    fields = ['index', 'name', 'assembly', 'source', 'faces', 'triangles', 'textureCount',
              'invisibleTriangles', 'nonzeroTrianglesBelow64SquareUnits', 'degenerateFanTriangles',
              'sourceFaces', 'sourceTriangles', 'sourceNativeCountsMatch']
    with (OUTPUT/'models.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(sorted(models, key=lambda m: m['triangles'], reverse=True))
    assert digest(native_path) == native_hash
    print(json.dumps({'totals': report['totals'], 'allSourceNativeCountsMatch': report['allSourceNativeCountsMatch'],
                      'output': str(OUTPUT)}, indent=2))


if __name__ == '__main__':
    main()
