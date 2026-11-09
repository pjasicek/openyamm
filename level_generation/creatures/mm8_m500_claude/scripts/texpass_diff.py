"""What changed between the installed and the texture-pass GLB: everything but UVs, images and ramps must match
(node, mesh, material, variant, skin, clip lists; clip and skin data byte for byte; every mesh's positions, normals,
joints and weights per triangle corner; image sizes listed). Usage: texpass_diff.py <before.glb> <after.glb>"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import accessor_bytes, floats, np, read_glb, rows, source_faces  # noqa: E402
from PIL import Image  # noqa: E402

(a, ab), (b, bb) = (read_glb(Path(p)) for p in sys.argv[1:3])
problems = []
for key, name in (('nodes', 'name'), ('meshes', 'name'), ('materials', 'name'), ('animations', 'name')):
    if [x.get(name) for x in a[key]] != [x.get(name) for x in b[key]]:
        problems.append(f'{key} names differ')
if a.get('extensions') != b.get('extensions'):
    problems.append('variants differ')
if [{k: v for k, v in n.items()} for n in a['nodes']] != [{k: v for k, v in n.items()} for n in b['nodes']]:
    problems.append('node transforms/children differ')
for i, (x, y) in enumerate(zip(a['animations'], b['animations'])):
    for sx, sy in zip(x['samplers'], y['samplers']):
        if accessor_bytes(a, ab, sx['input']) != accessor_bytes(b, bb, sy['input']) or \
                accessor_bytes(a, ab, sx['output']) != accessor_bytes(b, bb, sy['output']):
            problems.append(f'clip {x["name"]} data differs')
            break
    if [c['target'] for c in x['channels']] != [c['target'] for c in y['channels']]:
        problems.append(f'clip {x["name"]} channels differ')
for sx, sy in zip(a['skins'], b['skins']):
    if sx['joints'] != sy['joints'] or accessor_bytes(a, ab, sx['inverseBindMatrices']) != \
            accessor_bytes(b, bb, sy['inverseBindMatrices']):
        problems.append('skin differs')
for mx, my in zip(a['meshes'], b['meshes']):
    if mx.get('extras') != my.get('extras'):
        problems.append(f'mesh {mx["name"]} extras differ')
    for px, py in zip(mx['primitives'], my['primitives']):
        if px['material'] != py['material'] or px.get('extensions') != py.get('extensions'):
            problems.append(f'mesh {mx["name"]} material mapping differs')
        fx, fy = source_faces(a, ab, px), source_faces(b, bb, py)
        if len(fx) != len(fy):
            problems.append(f'mesh {mx["name"]} triangle count differs')
            continue
        for semantic in ('POSITION', 'NORMAL', 'JOINTS_0', 'WEIGHTS_0'):
            if not np.array_equal(rows(a, ab, px['attributes'][semantic])[fx], rows(b, bb, py['attributes'][semantic])[fy]):
                problems.append(f'mesh {mx["name"]} {semantic} differs per corner')
        uv_same = np.array_equal(floats(a, ab, px['attributes']['TEXCOORD_0'])[fx], floats(b, bb, py['attributes']['TEXCOORD_0'])[fy])
        print(f'{mx["name"]}: {len(fx)} triangles, vertices {a["accessors"][px["attributes"]["POSITION"]]["count"]} -> '
              f'{b["accessors"][py["attributes"]["POSITION"]]["count"]}, UVs {"same" if uv_same else "changed"}')
for mx, my in zip(a['materials'], b['materials']):
    strip = lambda m: {k: v for k, v in m.items() if k != 'extras'} | {'extras': {k: v for k, v in m['extras'].items() if k != 'openyamm_region_ramps'}}  # noqa: E731,E501
    if strip(mx) != strip(my):
        problems.append(f'material {mx["name"]} differs beyond ramps')


def size(doc, binary, image):
    v = doc['bufferViews'][image['bufferView']]
    return Image.open(io.BytesIO(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])).size


for ix, iy in zip(a['images'], b['images']):
    print(f'image {ix["name"]} {size(a, ab, ix)} -> {iy["name"]} {size(b, bb, iy)}')
print('PROBLEMS' if problems else 'OK: only UVs, images and ramps changed', problems)
