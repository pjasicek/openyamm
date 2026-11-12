"""Shared helpers for the follow-up 5 scripts: the glb_pose reader/writer plus image replacement and a repack that drops
buffer views nothing references any more (replaced images, superseded animation samplers)."""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402,F401


def image(g, name):
    im = next(x for x in g.json['images'] if x.get('name') == name)
    v = g.json['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(g.bin[o:o + v['byteLength']])))


def replace_image(g, name, pil):
    buf = io.BytesIO(); pil.save(buf, 'PNG', optimize=True); data = buf.getvalue()
    g.bin += b'\0' * (-len(g.bin) % 4)
    g.json['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': len(data)})
    g.bin += data
    g.json['buffers'][0]['byteLength'] = len(g.bin)
    next(x for x in g.json['images'] if x.get('name') == name)['bufferView'] = len(g.json['bufferViews']) - 1


def repack(g):
    """Drop unreferenced samplers' accessors and unreferenced buffer views; rewrite the binary tightly."""
    d = g.json
    used_acc = set()
    for m in d['meshes']:
        for p in m['primitives']:
            used_acc.update(p['attributes'].values())
            if 'indices' in p: used_acc.add(p['indices'])
            for t in p.get('targets', []): used_acc.update(t.values())
    for s in d.get('skins', []):
        if 'inverseBindMatrices' in s: used_acc.add(s['inverseBindMatrices'])
    for a in d.get('animations', []):
        used = sorted({c['sampler'] for c in a['channels']})
        remap = {o: n for n, o in enumerate(used)}
        a['samplers'] = [a['samplers'][o] for o in used]
        for c in a['channels']: c['sampler'] = remap[c['sampler']]
        for s in a['samplers']: used_acc.update((s['input'], s['output']))
    acc_order = sorted(used_acc); acc_map = {o: n for n, o in enumerate(acc_order)}
    accessors = [d['accessors'][o] for o in acc_order]
    used_views = {a['bufferView'] for a in accessors if 'bufferView' in a} | {im['bufferView'] for im in d.get('images', []) if 'bufferView' in im}
    view_order = sorted(used_views); view_map = {o: n for n, o in enumerate(view_order)}
    nb = bytearray(); views = []
    for o in view_order:
        v = dict(d['bufferViews'][o]); s = v.get('byteOffset', 0)
        nb += b'\0' * (-len(nb) % 8)
        chunk = g.bin[s:s + v['byteLength']]; v['byteOffset'] = len(nb); nb += chunk; views.append(v)
    for a in accessors:
        if 'bufferView' in a: a['bufferView'] = view_map[a['bufferView']]
    for im in d.get('images', []):
        if 'bufferView' in im: im['bufferView'] = view_map[im['bufferView']]
    for m in d['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: acc_map[v] for k, v in p['attributes'].items()}
            if 'indices' in p: p['indices'] = acc_map[p['indices']]
            if 'targets' in p: p['targets'] = [{k: acc_map[v] for k, v in t.items()} for t in p['targets']]
    for s in d.get('skins', []):
        if 'inverseBindMatrices' in s: s['inverseBindMatrices'] = acc_map[s['inverseBindMatrices']]
    for a in d.get('animations', []):
        for s in a['samplers']: s['input'] = acc_map[s['input']]; s['output'] = acc_map[s['output']]
    d['accessors'] = accessors; d['bufferViews'] = views
    g.bin = nb; d['buffers'][0]['byteLength'] = len(nb)
