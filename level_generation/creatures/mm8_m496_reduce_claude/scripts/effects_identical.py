#!/usr/bin/env python3
"""Byte comparison of two actor GLBs except the Body node's meshes: every other node's LOD0-3 primitives (attribute and
index data, material), all images, materials, animations (sampler data), skins and sockets must match.
Images named in ALLOW_IMAGES (comma list) may differ (the repainted and padded body atlas), and animation channels in
ALLOW_CHANNELS (clip:node:path, comma list; the eased arm channels of Fidget and Hit).
Usage: [ALLOW_IMAGES=m496_body] [ALLOW_CHANNELS=Fidget:LeftArm:rotation,...] effects_identical.py <installed.glb> <reduced.glb>"""
import hashlib, json, os, struct, sys


def load(p):
    d = open(p, 'rb').read(); l = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + l]); b0 = 20 + l + 8
    def view(i):
        bv = j['bufferViews'][i]; o = b0 + bv.get('byteOffset', 0); return d[o:o + bv['byteLength']]
    def acc(i):
        a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
        raw = view(a['bufferView']); comp = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]; st = bv.get('byteStride', comp * n)
        o = a.get('byteOffset', 0)
        return b''.join(raw[o + k * st:o + k * st + comp * n] for k in range(a['count'])) + json.dumps(
            {k: a[k] for k in ('componentType', 'type', 'count', 'normalized') if k in a}).encode()
    return j, view, acc


def h(b): return hashlib.sha1(b).hexdigest()[:12]


ja, va, aa = load(sys.argv[1]); jb, vb, ab = load(sys.argv[2])
def prims(j, acc, mi):
    return [(h(b''.join(acc(p['attributes'][k]) for k in sorted(p['attributes']))), h(acc(p['indices'])),
             j['materials'][p['material']]['name']) for p in j['meshes'][mi]['primitives']]
bad = 0
for na in ja['nodes']:
    if 'mesh' not in na or na['name'] == 'Body':
        continue
    nb = next(n for n in jb['nodes'] if n.get('name') == na['name'])
    ma, mb = ja['meshes'][na['mesh']], jb['meshes'][nb['mesh']]
    la = [na['mesh']] + ma.get('extras', {}).get('openyamm_lods', []); lb = [nb['mesh']] + mb.get('extras', {}).get('openyamm_lods', [])
    same = len(la) == len(lb) and all(prims(ja, aa, x) == prims(jb, ab, y) for x, y in zip(la, lb))
    same &= {k: v for k, v in na.items() if k != 'mesh'} == {k: v for k, v in nb.items() if k != 'mesh'}
    print('NODE', na['name'], 'LODs', len(la), 'identical' if same else 'DIFFERENT'); bad += not same
allow = set(os.environ.get('ALLOW_IMAGES', '').split(','))
ia = {i.get('name'): h(va(i['bufferView'])) for i in ja['images']}; ib = {i.get('name'): h(vb(i['bufferView'])) for i in jb['images']}
diff = sorted(k for k in set(ia) | set(ib) if ia.get(k) != ib.get(k))
print('IMAGES', len(ia), 'differing:', diff or 'none', '(allowed)' if set(diff) <= allow else ''); bad += not set(diff) <= allow
mat = lambda j: json.dumps(j['materials'], sort_keys=True)
print('MATERIALS', 'identical' if mat(ja) == mat(jb) else 'DIFFERENT'); bad += mat(ja) != mat(jb)
def anims(j, acc):
    return {(a['name'], j['nodes'][c['target']['node']]['name'], c['target']['path']):
            (h(acc(a['samplers'][c['sampler']]['input'])), h(acc(a['samplers'][c['sampler']]['output'])),
             a['samplers'][c['sampler']].get('interpolation', 'LINEAR')) for a in j['animations'] for c in a['channels']}
achan = set(tuple(x.split(':')) for x in os.environ.get('ALLOW_CHANNELS', '').split(',') if x)
ca, cb = anims(ja, aa), anims(jb, ab)
cdiff = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
print('ANIMATIONS', len(ja['animations']), 'clips,', len(ca), 'channels; differing:', [':'.join(k) for k in cdiff] or 'none',
      '(allowed)' if set(cdiff) <= achan else ''); bad += not set(cdiff) <= achan
times = lambda j: [(a['name'], max(j['accessors'][s['input']]['max'][0] for s in a['samplers'])) for a in j['animations']]
print('CLIP LENGTHS', 'identical' if times(ja) == times(jb) else 'DIFFERENT'); bad += times(ja) != times(jb)
names = lambda j: sorted(n.get('name', '') for n in j['nodes'])
print('NODE NAMES', 'identical' if names(ja) == names(jb) else 'DIFFERENT'); bad += names(ja) != names(jb)
print('RESULT', 'PASS' if not bad else f'FAIL ({bad})')
