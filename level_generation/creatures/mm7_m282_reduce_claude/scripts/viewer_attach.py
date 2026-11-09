#!/usr/bin/env python3
"""Review only: append a rigid attachment (export/mm7_m282_bow.glb on the Bow joint, export/mm7_m282_arrow.glb on the
Arrow joint; unchanged batch I files, full-detail mesh) to a viewer GLB as a child of its joint, with that tier's
material, so the browser shows the bow in the fist and the nocked arrow (scale 0 when hidden). The runtime keeps them as
separate attachments. Usage: viewer_sword.py <viewer glb> <tier a|b|c> <attachment glb> <joint> (in place)"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
ROOT = Path(__file__).resolve().parents[4]
path, tier = Path(sys.argv[1]), 'abc'.index(sys.argv[2])
doc, binary = read_glb(path); binary = bytearray(binary)
sd, sb = read_glb(Path(sys.argv[3])); JOINT = sys.argv[4]
base = len(binary); binary += bytes(sb) + b'\0' * (-len(sb) % 4)
nv = len(doc['bufferViews']); na = len(doc['accessors']); ni = len(doc.get('images', [])); nt = len(doc.get('textures', []))
ns = len(doc.get('samplers', [])); nm = len(doc['materials'])
for v in sd['bufferViews']:
    v = copy.deepcopy(v); v['buffer'] = 0; v['byteOffset'] = v.get('byteOffset', 0) + base; doc['bufferViews'].append(v)
for a in sd['accessors']:
    a = copy.deepcopy(a); a['bufferView'] += nv; doc['accessors'].append(a)
for im in sd['images']:
    im = copy.deepcopy(im); im['bufferView'] += nv; doc.setdefault('images', []).append(im)
for s in sd.get('samplers', []):
    doc.setdefault('samplers', []).append(copy.deepcopy(s))
for t in sd['textures']:
    t = copy.deepcopy(t); t['source'] += ni
    if 'sampler' in t:
        t['sampler'] += ns
    doc.setdefault('textures', []).append(t)


def retex(o):
    if isinstance(o, dict):
        for k, x in o.items():
            if k == 'index' and isinstance(x, int):
                o[k] = x + nt
            else:
                retex(x)
    elif isinstance(o, list):
        for x in o:
            retex(x)


m = copy.deepcopy(sd['materials'][tier]); retex(m); m['name'] = 'Viewer_' + m['name']; doc['materials'].append(m)
mesh = copy.deepcopy(sd['meshes'][0]); mesh['name'] = 'Viewer_' + JOINT; mesh.pop('extras', None)
for p in mesh['primitives']:
    p['attributes'] = {k: x + na for k, x in p['attributes'].items()}
    if 'indices' in p:
        p['indices'] += na
    p['material'] = nm; p.pop('extensions', None)
doc['meshes'].append(mesh)
doc['nodes'].append({'name': 'Viewer_' + JOINT, 'mesh': len(doc['meshes']) - 1})
sock = next(n for n in doc['nodes'] if n.get('name') == JOINT)
sock.setdefault('children', []).append(len(doc['nodes']) - 1)
write_glb(path, doc, binary); print('ATTACHED', JOINT, path.name, 'tier', sys.argv[2], sum(1 for _ in mesh['primitives']), 'primitive(s)')
