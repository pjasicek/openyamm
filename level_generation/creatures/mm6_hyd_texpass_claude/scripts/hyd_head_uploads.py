"""Per-head retexture uploads on the UV study's heads layout (work/uv_study_heads.npz): head k's triangles only, with
their study UVs, turned rigidly into the frame Meshy painted that head in for production (snout +Z, up +Y in glTF,
as mm6_hyd_claude/texturing/head<k>_st_upload.glb), so the head's own masters (references_heads/h<k>/) line up.

Frame: the Head<k> bone (joint -> rig tail, mm6_hyd_claude/work/rig.json, identical to the installed joints) turned
onto +Z with world up kept, then a similarity ICP of the rigid skull (Head<k> weight > 0.9) onto the production
Smart Topology upload refines it. Writes texturing/head<k>_upload.glb and texturing/head_frames.json.
Usage: hyd_head_uploads.py [k ...]"""
import json
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

import hyd_heads
from glb import Glb

P = hyd_heads.PROJECT
HYD = P.parent / 'mm6_hyd_claude'
HEADS = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5]
d = np.load(P / 'work' / 'lod0_before_heads.npz')
L = np.load(P / 'work' / 'uv_study_heads.npz')
head_t, _ = hyd_heads.head_of_triangle(d)
names = [str(n) for n in d['joint_names']]
rig = json.load(open(HYD / 'work' / 'rig.json'))
to_gl = lambda b: np.array([b[0], b[2], -b[1]])


def umeyama(src, dst):
    ms, md = src.mean(0), dst.mean(0)
    a, b = src - ms, dst - md
    u, s, vt = np.linalg.svd(b.T @ a / len(src))
    e = np.eye(3)
    e[2, 2] = np.sign(np.linalg.det(u @ vt))
    R = u @ e @ vt
    scale = (s * np.diag(e)).sum() / (a ** 2).sum(1).mean()
    return scale, R, md - scale * R @ ms


def write_glb(path, pos, nrm, uv, idx):
    blobs, views, accs = [], [], []
    offset = 0

    def add(arr, target, kind, comp, minmax=False):
        nonlocal offset
        data = np.ascontiguousarray(arr).tobytes()
        pad = (-len(data)) % 4
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(data), 'target': target})
        acc = {'bufferView': len(views) - 1, 'componentType': comp, 'count': len(arr), 'type': kind}
        if minmax:
            acc['min'] = arr.min(0).tolist()
            acc['max'] = arr.max(0).tolist()
        accs.append(acc)
        blobs.append(data + b'\0' * pad)
        offset += len(data) + pad
        return len(accs) - 1

    a_pos = add(pos.astype(np.float32), 34962, 'VEC3', 5126, True)
    a_nrm = add(nrm.astype(np.float32), 34962, 'VEC3', 5126)
    a_uv = add(uv.astype(np.float32), 34962, 'VEC2', 5126)
    a_idx = add(idx.astype(np.uint32).ravel(), 34963, 'SCALAR', 5125)
    doc = {'asset': {'version': '2.0', 'generator': 'mm6_hyd_texpass hyd_head_uploads.py'}, 'scene': 0,
           'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'Head'}],
           'meshes': [{'primitives': [{'attributes': {'POSITION': a_pos, 'NORMAL': a_nrm, 'TEXCOORD_0': a_uv},
                                       'indices': a_idx}]}],
           'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': offset}]}
    js = json.dumps(doc).encode()
    js += b' ' * ((-len(js)) % 4)
    binary = b''.join(blobs)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binary)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
        f.write(struct.pack('<II', len(binary), 0x004E4942) + binary)


frames = {}
# heads whose free-scale ICP shrinks into the skull (horns, squeezed spikes and fins): scale held at s0 x factor
import os
# head 4: its squeezed fins pull the ICP off (scale 1.4 against about 2.2): the bone-axis frame alone (front view checked
# against the production upload, work/frames_all.png); head 2: free-scale ICP shrinks into the skull, so its scale is held
# at the start estimate (p50 fit 3.2 mm)
AXIS_ONLY = set(json.loads(os.environ.get("HYD_AXIS_ONLY", "[4]")))
FIXED_SCALE = {int(a): float(b) for a, b in json.loads(os.environ.get("HYD_FIXED_SCALE", "{\"2\": -1.0}")).items()}
for k in HEADS:
    chain = next(c for c in rig['chains'] if c['names'] and c['names'][-1] == f'Head{k}')
    J = np.array(chain['joints'])
    H, tail = to_gl(J[-2]), to_gl(J[-1])
    f = (tail - H) / np.linalg.norm(tail - H)
    r = np.cross([0.0, 1.0, 0.0], f)
    r /= np.linalg.norm(r)
    u = np.cross(f, r)
    R0 = np.stack([r, u, f])                      # rows: new X, Y, Z
    sel = np.nonzero(head_t == k)[0]
    tri = d['tri'][sel]
    verts = np.unique(tri)
    hw = np.array([n == f'Head{k}' for n in names])
    skull_w = np.where(hw[d['joints']], d['weights'], 0).sum(1)
    skull = d['pos'][verts[skull_w[verts] > 0.9]]
    st = Glb(HYD / 'texturing' / f'head{k}_st_upload.glb')
    pr = st.doc['meshes'][0]['primitives'][0]
    target = st.accessor(pr['attributes']['POSITION']).astype(np.float64)
    tree = cKDTree(target)
    # start: skull axis on +Z, snout tips together, skull widths matched
    src0 = (skull - H) @ R0.T
    tip_s = src0[src0[:, 2].argmax()]
    tip_t = target[target[:, 2].argmax()]
    near_t = target[target[:, 2] > tip_t[2] - (tip_s[2] - src0[:, 2].min())]
    s0 = np.ptp(near_t[:, 0]) / max(np.ptp(src0[:, 0]), 1e-9)
    scale, R, t = s0, np.eye(3), tip_t - s0 * tip_s
    fixed = FIXED_SCALE.get(k)
    if fixed is not None and fixed < 0:
        fixed = -fixed * s0
    if fixed:
        scale, t = fixed, tip_t - fixed * tip_s
    if k in AXIS_ONLY:      # the mean ICP correction of heads 1, 3 and 5 (rotation vectors 8.0/6.3/10.1 deg about X)
        from scipy.spatial.transform import Rotation as _R0
        R = _R0.from_rotvec(np.radians([8.0, 0.0, 0.0])).as_matrix()
        t = tip_t - scale * R @ tip_s
    for it in range(0 if k in AXIS_ONLY else 80):
        cur = scale * src0 @ R.T + t
        dist, j = tree.query(cur)
        keep = dist <= np.percentile(dist, 90)
        s_, R, t = umeyama(src0[keep], target[j[keep]])
        if fixed:                                   # rigid with the scale held: re-solve t for the held scale
            t = (target[j[keep]] - scale * src0[keep] @ R.T).mean(0)
        else:
            scale = s_
    if k in AXIS_ONLY:      # scale and translation only for the reported fit (rotation stays the bone frame)
        _, j = tree.query(scale * src0 @ R.T + t)
        t = (target[j] - scale * src0 @ R.T).mean(0)
    cur = scale * src0 @ R.T + t
    dist, _ = tree.query(cur)
    ang = float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))
    # whole head k in that frame
    Rfull = R @ R0
    vpos = scale * (d['pos'][verts] - H) @ Rfull.T + t
    vnrm = d['nrm'][verts] @ Rfull.T
    vnrm /= np.maximum(np.linalg.norm(vnrm, axis=1, keepdims=True), 1e-12)
    remap = np.full(len(d['pos']), -1)
    remap[verts] = np.arange(len(verts))
    corner_v = remap[tri]
    corner_uv = L['uv'][sel]
    key = np.concatenate([corner_v.reshape(-1, 1).astype(np.float64), np.round(corner_uv.reshape(-1, 2), 7)], 1)
    uniq, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    out_v = corner_v.reshape(-1)[first]
    write_glb(P / 'texturing' / f'head{k}_upload.glb', vpos[out_v], vnrm[out_v], corner_uv.reshape(-1, 2)[first],
              inv.reshape(-1, 3))
    from scipy.spatial.transform import Rotation as _Rot
    frames[k] = {'triangles': int(len(sel)), 'icp_rotation_deg': round(ang, 1),
                 'icp_rotvec_deg': np.degrees(_Rot.from_matrix(R).as_rotvec()).round(1).tolist(), 'scale': round(float(scale), 4),
                 'skull_fit_mm_p50_p90': [round(float(np.percentile(dist, 50)) * 1000 / scale, 2),
                                          round(float(np.percentile(dist, 90)) * 1000 / scale, 2)]}
    print('UPLOAD', k, frames[k])
P.joinpath('texturing').mkdir(exist_ok=True)
json.dump(frames, open(P / 'texturing' / 'head_frames.json', 'w'), indent=1)
