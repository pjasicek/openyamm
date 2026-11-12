#!/usr/bin/env python3
"""Splice the grafted hands into the INSTALLED Titan GLB, key the fingers and fix the Cast recovery (2026-11-11).

Inputs: the installed GLB (work/before_rebuild/mm6_ttn.glb), graft_ttn.py's mesh+skin GLB (work/graft_v1.glb), the
composed atlas maps (textures/, compose_ttn.py) and scripts/finger_poses.json.
- LOD0 primitive replaced by the graft's (joints remapped by name; MHUV dropped), same material and variants mapping.
- 30 finger nodes (graft rest TRS) appended under LeftHand/RightHand and to the skin, with the graft's inverse binds
  (the graft's original joints must bind exactly as installed: checked).
- LOD1-3 and shadow meshes, the LOD2/3 materials and their images are dropped (build_actor_lods.py and the far-LOD
  repair rebuild them); the four LOD0 atlas images are replaced by the composed ones.
- Every clip keeps its samplers; each gets finger rotation channels from finger_poses.json (piecewise smoothstep
  between named poses, sampled on the clip's own key times). Cast: both arms' Arm/ForeArm/Hand rotations from
  `cast_fix.t0` to the end are eased (smoothstep) from the clip's pose at t0 to Standing frame 0 (the source swung the
  left hand across the belly and collapsed the left armpit at 1.6-2.05 s).
- Unreferenced buffer data is dropped.
Usage: splice_ttn.py <installed.glb> <graft.glb> <out.glb>"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
sys.path.insert(0, str(PROJ.parent / 'claude_shared' / 'floor'))
import glb_pose as gp  # noqa: E402

DT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
W = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def raw(glb, i):
    a = glb.json['accessors'][i]; v = glb.json['bufferViews'][a['bufferView']]
    dt = np.dtype(DT[a['componentType']]); w = W[a['type']]
    st = v.get('byteStride', 0) or dt.itemsize * w
    return np.ndarray((a['count'], w), dt, glb.bin, v.get('byteOffset', 0) + a.get('byteOffset', 0), (st, dt.itemsize)).copy()


def add(doc, binary, values, ctype, kind, normalized=False, minmax=False, target=None):
    values = np.ascontiguousarray(values, dtype=DT[ctype]).reshape(len(values), W[kind])
    binary.extend(b'\0' * (-len(binary) % 4))
    view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': values.nbytes}
    if target:
        view['target'] = target
    doc['bufferViews'].append(view)
    binary.extend(values.tobytes())
    acc = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': ctype, 'count': len(values), 'type': kind}
    if normalized:
        acc['normalized'] = True
    if minmax:
        acc['min'] = values.min(0).tolist(); acc['max'] = values.max(0).tolist()
    doc['accessors'].append(acc)
    return len(doc['accessors']) - 1


def gc(doc, binary):
    """Keep only referenced accessors/bufferViews; rebuild the binary."""
    used = set()
    for m in doc['meshes']:
        for p in m['primitives']:
            used.update(p['attributes'].values()); used.add(p['indices'])
    for s in doc.get('skins', []):
        if 'inverseBindMatrices' in s:
            used.add(s['inverseBindMatrices'])
    for an in doc.get('animations', []):
        for s in an['samplers']:
            used.update((s['input'], s['output']))
    acc_map = {}
    accs = []
    for i in sorted(used):
        acc_map[i] = len(accs); accs.append(doc['accessors'][i])
    views_used = sorted({a['bufferView'] for a in accs} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
    view_map = {}; views = []; out = bytearray()
    for vi in views_used:
        v = dict(doc['bufferViews'][vi]); out.extend(b'\0' * (-len(out) % 4))
        o = v.get('byteOffset', 0); out_off = len(out)
        out.extend(binary[o:o + v['byteLength']]); v['byteOffset'] = out_off
        view_map[vi] = len(views); views.append(v)
    for a in accs:
        a['bufferView'] = view_map[a['bufferView']]
    for im in doc.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = view_map[im['bufferView']]
    for m in doc['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: acc_map[v] for k, v in p['attributes'].items()}; p['indices'] = acc_map[p['indices']]
    for s in doc.get('skins', []):
        if 'inverseBindMatrices' in s:
            s['inverseBindMatrices'] = acc_map[s['inverseBindMatrices']]
    for an in doc.get('animations', []):
        for s in an['samplers']:
            s['input'] = acc_map[s['input']]; s['output'] = acc_map[s['output']]
    doc['accessors'] = accs; doc['bufferViews'] = views
    doc['buffers'] = [{'byteLength': len(out)}]
    return out


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qaxis(axis, deg):
    h = np.radians(deg) / 2
    return np.array([*(np.array(axis) * np.sin(h)), np.cos(h)])


def smooth(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def main():
    src, graft, out = (Path(a) for a in sys.argv[1:4])
    poses_cfg = json.load(open(HERE / 'finger_poses.json'))
    I = gp.Glb(src); G = gp.Glb(graft)
    doc = I.json; binary = bytearray(I.bin)
    names = [n.get('name') for n in doc['nodes']]
    gnames = [n.get('name') for n in G.json['nodes']]
    skin = doc['skins'][0]; gskin = G.json['skins'][0]
    old_joint_names = [names[j] for j in skin['joints']]
    gjoint_names = [gnames[j] for j in gskin['joints']]
    fingers = [n for n in gjoint_names if n not in old_joint_names]
    # bind spaces must agree
    ibm_old = raw(I, skin['inverseBindMatrices']).reshape(-1, 16)
    ibm_g = raw(G, gskin['inverseBindMatrices']).reshape(-1, 16)
    err = max(np.abs(ibm_old[old_joint_names.index(n)] - ibm_g[gjoint_names.index(n)]).max() for n in old_joint_names)
    assert err < 1e-4, f'bind space changed by {err}'
    # finger nodes
    for n in fingers:
        gi = gnames.index(n); gn = G.json['nodes'][gi]
        node = {'name': n, 'rotation': gn['rotation'], 'translation': gn['translation']}
        doc['nodes'].append(node); names.append(n)
    for n in fingers:
        gparent = next(i for i, x in enumerate(G.json['nodes']) if gnames.index(n) in x.get('children', []))
        p = names.index(gnames[gparent])
        doc['nodes'][p].setdefault('children', []).append(names.index(n))
    joint_names = old_joint_names + fingers
    skin['joints'] = [names.index(n) for n in joint_names]
    ibm = np.concatenate([ibm_old, np.stack([ibm_g[gjoint_names.index(n)] for n in fingers])])
    skin['inverseBindMatrices'] = add(doc, binary, ibm, 5126, 'MAT4')
    # LOD0 primitive
    gp_ = G.json['meshes'][0]['primitives'][0]; ga = gp_['attributes']
    remap = np.array([joint_names.index(n) for n in gjoint_names])
    prim = doc['meshes'][0]['primitives'][0]
    pos, nrm, uvs = raw(G, ga['POSITION']), raw(G, ga['NORMAL']), raw(G, ga['TEXCOORD_0'])
    jw = remap[raw(G, ga['JOINTS_0']).astype(np.int64)]
    wts = raw(G, ga['WEIGHTS_0']).astype(np.float64)
    wts /= wts.sum(1, keepdims=True)
    idx = raw(G, gp_['indices']).ravel()
    # follow-up 2026-11-11: the graft's bracer-rim rules (poke, rim_clean) also deleted bright gold faces of the bracer
    # rims (the dark notch at the left bracer). Installed LOD0 triangles the graft dropped that are forearm-weighted
    # and textured bracer gold come back as they were (installed vertices, weights and UVs; joint order unchanged).
    rest_cfg = poses_cfg.get('restore_bracer')
    restored = 0
    if rest_cfg:
        from PIL import Image
        from scipy.spatial import cKDTree
        ip = I.json['meshes'][0]['primitives'][0]; ia = ip['attributes']
        P0, N0, U0 = raw(I, ia['POSITION']), raw(I, ia['NORMAL']), raw(I, ia['TEXCOORD_0'])
        J0 = raw(I, ia['JOINTS_0']).astype(np.int64); W0 = raw(I, ia['WEIGHTS_0']).astype(np.float64)
        T0 = raw(I, ip['indices']).reshape(-1, 3)
        tex = np.asarray(Image.open(PROJ / 'work/src_tex/ttn_a_basecolor_1k_head_atlas.png').convert('RGB')).astype(float)
        th, tw = tex.shape[:2]
        dom = np.array([old_joint_names[J0[v][np.argmax(W0[v])]] for v in range(len(P0))])
        gone = cKDTree(pos[idx.reshape(-1, 3)].mean(1)).query(P0[T0].mean(1))[0] > 1e-4
        keep = []
        for k in np.where(gone)[0]:
            if not all(dom[v].endswith('ForeArm') for v in T0[k]):
                continue
            u, v = U0[T0[k]].mean(0); c = tex[min(int(v * th), th - 1), min(int(u * tw), tw - 1)]
            if c[0] >= rest_cfg['min_red'] and c[0] > c[2] + 100:
                keep.append(k)
        if keep:
            vs = np.unique(T0[keep]); vmap = {v: len(pos) + i for i, v in enumerate(vs)}
            pos = np.concatenate([pos, P0[vs]]); nrm = np.concatenate([nrm, N0[vs]]); uvs = np.concatenate([uvs, U0[vs]])
            jw = np.concatenate([jw, J0[vs]]); wts = np.concatenate([wts, W0[vs] / W0[vs].sum(1, keepdims=True)])
            idx = np.concatenate([idx, np.array([[vmap[v] for v in T0[k]] for k in keep]).ravel()])
            restored = len(keep)
    attrs = {}
    attrs['POSITION'] = add(doc, binary, pos, 5126, 'VEC3', minmax=True, target=34962)
    attrs['NORMAL'] = add(doc, binary, nrm, 5126, 'VEC3', target=34962)
    attrs['TEXCOORD_0'] = add(doc, binary, uvs, 5126, 'VEC2', target=34962)
    attrs['JOINTS_0'] = add(doc, binary, jw, 5121, 'VEC4', target=34962)
    attrs['WEIGHTS_0'] = add(doc, binary, wts, 5126, 'VEC4', target=34962)
    prim['attributes'] = attrs
    prim['indices'] = add(doc, binary, idx, 5125, 'SCALAR', target=34963)
    # drop LOD and shadow meshes, their materials and images
    mesh0 = doc['meshes'][0]
    mesh0.pop('extras', None)
    doc['meshes'] = [mesh0]
    keep_mats = [i for i, m in enumerate(doc['materials']) if '_LOD' not in m['name']]
    mat_map = {o: n for n, o in enumerate(keep_mats)}
    doc['materials'] = [doc['materials'][i] for i in keep_mats]
    prim['material'] = mat_map[prim['material']]
    for m in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        m['material'] = mat_map[m['material']]
    used_tex = set()
    for m in doc['materials']:
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            t = m.get('pbrMetallicRoughness', {}).get(key)
            if t:
                used_tex.add(t['index'])
        for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if key in m:
                used_tex.add(m[key]['index'])
        rm = (m.get('extras') or {}).get('openyamm_region_mask')
        if rm:
            used_tex.add(rm['index'])
    tex_keep = sorted(used_tex); tex_map = {o: n for n, o in enumerate(tex_keep)}
    doc['textures'] = [doc['textures'][i] for i in tex_keep]
    for m in doc['materials']:
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            t = m.get('pbrMetallicRoughness', {}).get(key)
            if t:
                t['index'] = tex_map[t['index']]
        for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if key in m:
                m[key]['index'] = tex_map[m[key]['index']]
        rm = (m.get('extras') or {}).get('openyamm_region_mask')
        if rm:
            rm['index'] = tex_map[rm['index']]
    img_keep = sorted({t['source'] for t in doc['textures']}); img_map = {o: n for n, o in enumerate(img_keep)}
    doc['images'] = [doc['images'][i] for i in img_keep]
    for t in doc['textures']:
        t['source'] = img_map[t['source']]
    for im in doc['images']:
        f = PROJ / 'textures' / f"{im['name']}.png"
        data = f.read_bytes()
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary.extend(data); im['bufferView'] = len(doc['bufferViews']) - 1
    # --------------------------------------------------------------- finger and Cast keys
    tmp = gp.Glb.__new__(gp.Glb); tmp.json = doc; tmp.bin = binary
    model = gp.Model(tmp)
    world = model.world({})
    frames = json.load(open(PROJ / 'work' / 'graft_v1.json'))['frames']
    report = {'frames': {}}
    side_tok = {'L': 'Left', 'R': 'Right'}
    signs = {}
    for key, tok in side_tok.items():
        nrm = np.array(frames[key]['n']); n_g = np.array([nrm[0], nrm[2], -nrm[1]])
        tips = {}
        for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
            tips[f] = world[names.index(f'{tok}Hand{f}3')][:3, 3]
        for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
            for j in (1, 2, 3):
                b = names.index(f'{tok}Hand{f}{j}'); R = world[b][:3, :3]
                ydir = (world[names.index(f'{tok}Hand{f}{j + 1}')][:3, 3] - world[b][:3, 3]) if j < 3 else None
                yerr = float(np.degrees(np.arccos(np.clip(np.dot(R[:, 1], ydir / np.linalg.norm(ydir)), -1, 1)))) if ydir is not None else 0.0
                zdot = float(np.dot(R[:, 2], n_g))
                report['frames'][f'{tok}{f}{j}'] = {'y_err_deg': round(yerr, 2), 'z_dot_palm': round(zdot, 3)}
            b1 = names.index(f'{tok}Hand{f}1'); X = world[b1][:3, 0]
            if f == 'Thumb':
                d = world[names.index(f'{tok}HandIndex1')][:3, 3] - tips['Thumb']
            elif f == 'Middle':
                d = np.zeros(3)
            else:
                d = tips[f] - tips['Middle']
            # +angle about Z moves the bone's Y toward -X: away from the middle finger (thumb: toward the index)
            signs[f'{tok}{f}'] = -1.0 if np.dot(d, X) > 0 else 1.0
    report['spread_signs'] = signs
    P = poses_cfg['poses']

    def pose_angles(name, f, tok=None):
        p = P.get(f'{name}@{tok}', P[name])        # follow-up 2026-11-11: a pose may have per-side solves, <name>@Left
        if f == 'Thumb':
            return p['thumb']                       # [t1 flex, t1 toward index, t2 flex, t3 flex]
        base = p['fingers']                        # [mcp, pip, dip]
        extra = p.get('per_finger', {}).get(f, [0, 0, 0])
        spread = p.get('spread', {}).get(f, 0.0)
        return [base[0] + extra[0], base[1] + extra[1], base[2] + extra[2], spread]

    def angles_at(track, t, f, tok=None):
        ts = [k[0] for k in track]
        if t <= ts[0]:
            return np.array(pose_angles(track[0][1], f, tok), float)
        for (t0, a), (t1, b) in zip(track, track[1:]):
            if t <= t1:
                s = smooth((t - t0) / max(t1 - t0, 1e-6))
                return (1 - s) * np.array(pose_angles(a, f, tok), float) + s * np.array(pose_angles(b, f, tok), float)
        return np.array(pose_angles(track[-1][1], f, tok), float)

    rest_q = {n: np.array(doc['nodes'][names.index(n)]['rotation'], float) for n in names if n and 'Hand' in n and n[-1].isdigit()}
    st_local = model.sample('Standing', 0.0)
    for an in doc['animations']:
        clip = an['name']
        times = sorted(set(float(x) for s in an['samplers'] for x in raw(tmp, s['input'])[:, 0]))
        T = np.array(times, np.float32)
        t_acc = add(doc, binary, T[:, None], 5126, 'SCALAR', minmax=True)
        spec = poses_cfg['clips'].get(clip, poses_cfg['clips']['default'])
        for key, tok in side_tok.items():
            track = spec.get(tok, spec.get('both'))
            for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
                vals = {j: [] for j in (1, 2, 3)}
                for t in times:
                    a = angles_at(track, t, f, tok)
                    if f == 'Thumb':
                        rots = {1: qmul(qaxis([0, 0, 1], signs[f'{tok}Thumb'] * a[1]), qaxis([1, 0, 0], a[0])),
                                2: qaxis([1, 0, 0], a[2]), 3: qaxis([1, 0, 0], a[3])}
                    else:
                        rots = {1: qmul(qaxis([0, 0, 1], signs[f'{tok}{f}'] * a[3]), qaxis([1, 0, 0], a[0])),
                                2: qaxis([1, 0, 0], a[1]), 3: qaxis([1, 0, 0], a[2])}
                    for j in (1, 2, 3):
                        vals[j].append(qmul(rest_q[f'{tok}Hand{f}{j}'], rots[j]))
                for j in (1, 2, 3):
                    q = np.array(vals[j])
                    for k in range(1, len(q)):
                        if np.dot(q[k], q[k - 1]) < 0:
                            q[k] = -q[k]
                    o_acc = add(doc, binary, q, 5126, 'VEC4')
                    an['samplers'].append({'input': t_acc, 'output': o_acc, 'interpolation': 'LINEAR'})
                    an['channels'].append({'sampler': len(an['samplers']) - 1,
                                           'target': {'node': names.index(f'{tok}Hand{f}{j}'), 'path': 'rotation'}})
        fix = poses_cfg.get('cast_fix')
        if fix and clip in fix['clips']:
            t0 = fix['t0']; tend = times[-1]
            tmp.json = doc; tmp.bin = binary
            m2 = gp.Model(tmp)
            at0 = m2.sample(clip, t0)
            for jn in fix['joints']:
                ni = names.index(jn)
                ch = next(c for c in an['channels'] if c['target']['node'] == ni and c['target']['path'] == 'rotation')
                s = an['samplers'][ch['sampler']]
                ti = raw(tmp, s['input'])[:, 0].astype(np.float64)
                qo = raw(tmp, s['output']).astype(np.float64)
                qa = at0[ni][1]; qb = st_local.get(ni, m2.rest[ni])[1]
                for k, t in enumerate(ti):
                    if t >= t0:
                        qo[k] = gp.slerp(qa, qb, float(smooth((t - t0) / (tend - t0))))
                for k in range(1, len(qo)):
                    if np.dot(qo[k], qo[k - 1]) < 0:
                        qo[k] = -qo[k]
                s['output'] = add(doc, binary, qo, 5126, 'VEC4')
            report.setdefault('cast_fix', []).append({'clip': clip, 't0': t0, 'joints': fix['joints']})
    binary = gc(doc, binary)
    tmp.json = doc; tmp.bin = binary
    tmp.write(out)
    report['fingers'] = len(fingers); report['lod0_triangles'] = int(len(idx) // 3); report['restored_bracer_faces'] = restored
    (out.parent / (out.stem + '.json')).write_text(json.dumps(report, indent=1))
    bad = {k: v for k, v in report['frames'].items() if v['y_err_deg'] > 2 or v['z_dot_palm'] < 0.7}
    print('SPLICE', out, 'fingers', len(fingers), 'tris', len(idx) // 3, 'restored bracer faces', restored, 'frame warnings', bad, 'signs', signs)


if __name__ == '__main__':
    main()
