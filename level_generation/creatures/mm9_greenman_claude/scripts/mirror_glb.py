#!/usr/bin/env python3
"""Mirror a runtime actor GLB across the model's X axis (positions, normals, winding, joints, clips).

convert_abc_model.py keeps LithTech's left-handed coordinates as glTF numbers, so every MM9-route GLB is the mirror image
of the game's actor: MM9's `R Hand` sits on the creature's anatomical left. The Imp is the first MM9 body that shows it
(the trident). Conjugating everything by S = diag(-1, 1, 1) gives the true-handed actor with identical motion: vertex
x -> -x (normals too), triangle winding reversed, every node's TRS and every animation channel S M S (translation x
negated, quaternion y and z negated), inverse bind matrices S IB S. Bone names keep MM9's meaning (`R Hand` is the right
hand again). Usage: mirror_glb.py in.glb out.glb"""
import json, struct, sys
import numpy as np

src, dst = sys.argv[1:3]
raw = open(src, 'rb').read()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
bin_off = 20 + n + 8
blob = bytearray(raw[bin_off:])
SIZES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
COUNT = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
DT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}


def view(i):
    a = doc['accessors'][i]
    bv = doc['bufferViews'][a['bufferView']]
    k = COUNT[a['type']]
    sz = SIZES[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = bv.get('byteStride') or k * sz
    return off, st, k, sz, a['count'], DT[a['componentType']]


def read(i):
    off, st, k, sz, c, dt = view(i)
    idx = off + np.arange(c)[:, None] * st + np.arange(k)[None] * sz
    return np.frombuffer(blob, dtype=np.uint8)[(idx[..., None] + np.arange(sz))].reshape(c, k, sz).tobytes(), (c, k), dt


def get(i):
    b, sh, dt = read(i)
    return np.frombuffer(b, dt).reshape(sh).copy()


def put(i, arr):
    off, st, k, sz, c, dt = view(i)
    data = np.asarray(arr, dt).reshape(c, k)
    for r in range(c):
        blob[off + r * st:off + r * st + k * sz] = data[r].tobytes()


done = set()


def once(i, fn):
    if i is None or i in done:
        return
    done.add(i)
    fn(i)


def mirror_vec3(i):
    a = get(i)
    a[:, 0] *= -1
    put(i, a)
    acc = doc['accessors'][i]
    if 'min' in acc:
        lo, hi = acc['min'][0], acc['max'][0]
        acc['min'][0], acc['max'][0] = -hi, -lo


def flip_winding(i):
    a = get(i).reshape(-1, 3)
    put(i, a[:, ::-1].reshape(-1, 1))


def mirror_quat(i):
    a = get(i)
    a[:, 1:3] *= -1
    put(i, a)


def mirror_mat(i):
    a = get(i).reshape(-1, 4, 4)            # column major
    S = np.diag([-1.0, 1, 1, 1])
    out = np.array([S @ m.T @ S for m in a.astype(np.float64)])
    put(i, np.transpose(out, (0, 2, 1)).reshape(-1, 16))


for mesh in doc['meshes']:
    for p in mesh['primitives']:
        once(p['attributes'].get('POSITION'), mirror_vec3)
        once(p['attributes'].get('NORMAL'), mirror_vec3)
        assert 'TANGENT' not in p['attributes']
        once(p.get('indices'), flip_winding)
        for t in p.get('targets', []):
            raise SystemExit('morph targets are not handled')
for skin in doc.get('skins', []):
    once(skin.get('inverseBindMatrices'), mirror_mat)
for node in doc['nodes']:
    assert 'matrix' not in node
    if 'translation' in node:
        node['translation'][0] *= -1
    if 'rotation' in node:
        node['rotation'][1] *= -1
        node['rotation'][2] *= -1
for anim in doc.get('animations', []):
    for ch in anim['channels']:
        s = anim['samplers'][ch['sampler']]
        path = ch['target']['path']
        if path == 'translation':
            once(s['output'], mirror_vec3)
        elif path == 'rotation':
            once(s['output'], mirror_quat)
enc = json.dumps(doc, separators=(',', ':')).encode()
enc += b' ' * (-len(enc) % 4)
blob += b'\0' * (-len(blob) % 4)
doc['buffers'][0]['byteLength'] = len(blob)
enc = json.dumps(doc, separators=(',', ':')).encode()
enc += b' ' * (-len(enc) % 4)
with open(dst, 'wb') as f:
    f.write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(blob)))
    f.write(struct.pack('<II', len(enc), 0x4e4f534a) + enc)
    f.write(struct.pack('<II', len(blob), 0x004e4942) + bytes(blob))
print('MIRRORED', dst, len(doc.get('animations', [])), 'clips')
