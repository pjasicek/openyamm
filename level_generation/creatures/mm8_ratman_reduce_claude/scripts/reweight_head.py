#!/usr/bin/env python3
"""Give the Ratman's head a neck: one smooth weight field over the head shell and the body's neck socket, in every
skinned mesh of the GLB (run it on the full-detail file before the LOD build).

The production weights put the back half of the head on B_R_Clavicle / B_L_Clavicle (mean 0.2, up to 0.78), B_Spine1
and the upper-arm twist bones, and nothing on B_Neck: raising the sword arm dragged the cheek and skull. The head is a
separate shell plugged into a dark neck socket of the body; once the head is lifted (lift_neck_clips.py), any
difference between the two layers' weights pulls them apart and shows the socket through the throat ("hole in his
neck", review 2). So both layers take one harmonic field:

- fixed: the skull (head set, t >= SKULL; t = position along the neck, 0 at the B_Neck joint, 1 at the B_Head joint)
  is B_Head 1; body vertices outside the neck zone keep their own weights (a head share there moves to B_Spine2);
- free: the rest of the head shell, and body vertices of the neck zone (t > T_LOW, within RADIUS of the neck
  segment) are solved as a harmonic interpolation (graph Laplacian) over the mesh edges plus K nearest rest-pose
  neighbours of the other layer, so overlapping shell and socket get the same weights and move together, and the
  throat stretches evenly instead of folding into shards.

Small separate pieces near the neck (fur tufts, whiskers, teeth, eyes) then become rigid on the skin under their root
(rigid_tufts). Geometry is unchanged. Usage: reweight_head.py <in.glb> <out.glb>"""
import io
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

SKULL = 0.75                 # head set beyond this point along the neck is the rigid skull
T_LOW, RADIUS = -0.4, 0.13   # body neck zone: along the neck and distance from the neck segment (m)
MANE_NEAR, MANE_FAR = map(float, __import__('os').environ.get('MANE_FALLOFF', '0.04,0.12').split(','))
K, SMALL, REACH = 8, 80, 0.45
HEAD_U = 1056 / 2080         # head texture set: right half of the merged atlas
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
N = doc['nodes']
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(i):
    a = doc['accessors'][i]
    arr = np.frombuffer(accessor_bytes(doc, binary, i), CT[a['componentType']]).reshape(a['count'], NC[a['type']])
    return arr.astype(np.float64) / np.iinfo(CT[a['componentType']]).max if a.get('normalized') else arr.astype(np.float64)


def pieces(pos, tri):
    """welded vertex ids and connected piece label per vertex, faces per piece"""
    _, weld = np.unique(np.round(pos / 1e-6).astype(np.int64), axis=0, return_inverse=True); weld = weld.ravel()
    n = weld.max() + 1; e = weld[np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])]
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    vlab = lab[weld]
    return weld, vlab, np.bincount(vlab[tri[:, 0]], minlength=lab.max() + 1)


def head_share(d):
    """share of B_Head for mane and tufts at distance d from the skull: 1 within MANE_NEAR, 0 beyond MANE_FAR"""
    h = np.clip((MANE_FAR - d) / (MANE_FAR - MANE_NEAR), 0, 1)
    return h * h * (3 - 2 * h)


def fur_mask(prim, uv, tri, weld, sel, rounds=6):
    """1 on fur, 0 on the vest's grey cloth (base colour at each vertex), smoothed over the mesh edges so the head
    share fades out across the boundary instead of tearing the sheet there"""
    tex = doc['textures'][doc['materials'][prim['material']]['pbrMetallicRoughness']['baseColorTexture']['index']]
    v = doc['bufferViews'][doc['images'][tex['source']]['bufferView']]; o = v.get('byteOffset', 0)
    im = np.asarray(Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']]))).convert('RGB')).astype(float)
    H, W = im.shape[:2]
    c = im[np.clip((uv[:, 1] * H).astype(int), 0, H - 1), np.clip((uv[:, 0] * W).astype(int), 0, W - 1)]
    f = 1.0 - ((c.max(1) - c.min(1) < 25) & (c.mean(1) > 110))
    fw = np.zeros(weld.max() + 1); cnt = np.zeros_like(fw)    # per welded vertex, so UV seams do not split it
    np.add.at(fw, weld, f); np.add.at(cnt, weld, 1); fw /= cnt
    e = weld[np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])]
    for _ in range(rounds):
        acc = fw.copy(); deg = np.ones_like(fw)
        np.add.at(acc, e[:, 0], fw[e[:, 1]]); np.add.at(deg, e[:, 0], 1)
        np.add.at(acc, e[:, 1], fw[e[:, 0]]); np.add.at(deg, e[:, 1], 1); fw = acc / deg
    return np.clip((fw[weld[sel]] - 0.3) / 0.4, 0, 1)


def rigid_tufts(pos, tri, dense, vlab, faces, skull_tree):
    """Fur tufts, whiskers, teeth and eyes (pieces of up to SMALL faces within REACH of the neck joint) take the
    weights of the skin under their root, the nearest vertex of a larger piece: tufts whose root and tip carried
    different weights fanned out into upright spikes whenever the neck moved. Like the mane, tufts near the skull then
    shift to B_Head by their distance from it, or the lifted or turning skull passes through them."""
    small = (faces[vlab] <= SMALL) & (np.linalg.norm(pos - n0, axis=1) < REACH)
    used = np.zeros(len(pos), bool); used[tri.ravel()] = True
    main = np.where(used & (faces[vlab] > SMALL))[0]; tree = cKDTree(pos[main]); count = 0
    for c in np.unique(vlab[small & used]):
        vs = np.where(vlab == c)[0]
        d, j = tree.query(pos[vs]); w = dense[main[j[np.argmin(d)]]].copy(); count += 1
        h = head_share(skull_tree.query(pos[vs])[0].min()); w *= 1 - h; w[HEAD] += h; dense[vs] = w
    return count


skin = doc['skins'][0]; joints = skin['joints']
ibm = read(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
jix = {N[j]['name']: k for k, j in enumerate(joints)}
bind = lambda name: np.linalg.inv(ibm[jix[name]])[:3, 3]
n0, h0 = bind('B_Neck'), bind('B_Head'); axis = h0 - n0
HEAD, SPINE2 = jix['B_Head'], jix['B_Spine2']
skinned = {n['mesh'] for n in N if 'mesh' in n and 'skin' in n}
meshes = sorted(skinned | {i for m in skinned for key in ('openyamm_lods', 'openyamm_shadow_lods')
                           for i in doc['meshes'][m].get('extras', {}).get(key, [])})
done = {}
for mi in meshes:
    for p in doc['meshes'][mi]['primitives']:
        at = p['attributes']; key = (at['POSITION'], at['JOINTS_0'], at['WEIGHTS_0'])
        if key in done:
            at['JOINTS_0'], at['WEIGHTS_0'] = done[key]; continue
        pos = read(at['POSITION']); jnt = read(at['JOINTS_0']).astype(int); wts = read(at['WEIGHTS_0'])
        tri = read(p['indices']).astype(int)[:, 0].reshape(-1, 3)
        wts = wts / wts.sum(1, keepdims=True)
        dense = np.zeros((len(pos), len(joints))); np.add.at(dense, (np.arange(len(pos))[:, None], jnt), wts)
        headset = read(at['TEXCOORD_0'])[:, 0] > HEAD_U
        weld, vlab, faces = pieces(pos, tri)
        used = np.zeros(len(pos), bool); used[tri.ravel()] = True
        main = used & (faces[vlab] > SMALL)
        t = (pos - n0) @ axis / (axis @ axis)
        seg = n0 + np.clip(t, 0, 1)[:, None] * axis; dseg = np.linalg.norm(pos - seg, axis=1)
        skull = main & headset & (t >= SKULL)
        # the mane: the fur collar of the vest (body-set pieces other than the skin, the largest; their grey cloth is
        # masked out below); it lies behind the skull
        body_piece = np.bincount(vlab[~headset & used], minlength=len(faces)); skin_piece = np.argmax(faces * (body_piece > 0))
        mane = main & ~headset & (vlab != skin_piece)
        free = main & ((headset & (t < SKULL)) | (~headset & (t > T_LOW) & (dseg < RADIUS)))
        fixed_body = main & ~headset & ~free
        dense[fixed_body, SPINE2] += dense[fixed_body, HEAD]; dense[fixed_body, HEAD] = 0
        dense[skull] = 0; dense[skull, HEAD] = 1
        # the lifted skull moves up and back into the mane behind it: fur outside the neck zone within MANE_NEAR of the
        # skull rides the head, easing back to its own weights at MANE_FAR
        mane &= ~free; skull_tree = cKDTree(pos[skull])
        h = head_share(skull_tree.query(pos[mane])[0]) * fur_mask(p, read(at['TEXCOORD_0']), tri, weld, mane)
        dense[mane] *= (1 - h)[:, None]; dense[np.where(mane)[0], HEAD] += h
        # graph: mesh edges (welded duplicates joined) + K nearest rest-pose neighbours among main vertices
        ids = np.where(main)[0]; loc = -np.ones(len(pos), int); loc[ids] = np.arange(len(ids))
        e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]); e = e[main[e[:, 0]] & main[e[:, 1]]]
        tree = cKDTree(pos[ids]); dk, jk = tree.query(pos[ids], K + 1)
        rows = np.concatenate([loc[e[:, 0]], np.repeat(np.arange(len(ids)), K)])
        cols = np.concatenate([loc[e[:, 1]], jk[:, 1:].ravel()])
        w = np.concatenate([1 / (np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1) + 1e-3), 1 / (dk[:, 1:].ravel() + 1e-3)])
        # weld coincident duplicates (glTF splits at UV seams) with a strong link
        dup = np.where(weld[ids][:, None] == weld[ids][jk[:, 1:]].reshape(len(ids), K))
        rows = np.concatenate([rows, dup[0]]); cols = np.concatenate([cols, jk[:, 1:][dup]]); w = np.concatenate([w, np.full(len(dup[0]), 1e4)])
        A = coo_matrix((w, (rows, cols)), shape=(len(ids), len(ids))).tocsr(); A = A + A.T
        deg = np.asarray(A.sum(1)).ravel()
        f = free[ids]; c = ~f
        L = diags(deg) - A
        Lff, Lfc = L[f][:, f], L[f][:, c]
        X = dense[ids]; bones = np.where(X[c].sum(0) > 0)[0]
        sol = spsolve(Lff.tocsc(), -(Lfc @ X[c][:, bones]))
        sol = np.clip(np.asarray(sol).reshape(int(f.sum()), len(bones)), 0, None)
        Xf = np.zeros((int(f.sum()), len(joints))); Xf[:, bones] = sol; Xf /= Xf.sum(1, keepdims=True)
        dense[ids[f]] = Xf
        tufts = rigid_tufts(pos, tri, dense, vlab, faces, skull_tree)
        order = np.argsort(-dense, 1)[:, :4]; top = np.take_along_axis(dense, order, 1)
        top /= top.sum(1, keepdims=True); order[top == 0] = 0
        ja, wa = doc['accessors'][at['JOINTS_0']], doc['accessors'][at['WEIGHTS_0']]
        if wa.get('normalized'):
            mx = np.iinfo(CT[wa['componentType']]).max; q = np.round(top * mx).astype(np.int64)
            q[:, 0] += mx - q.sum(1); wbytes = q.astype(CT[wa['componentType']]).tobytes()
        else:
            wbytes = top.astype(np.float32).tobytes()
        done[key] = (append_accessor(doc, binary, ja, order.astype(CT[ja['componentType']]).tobytes()),
                     append_accessor(doc, binary, wa, wbytes))
        at['JOINTS_0'], at['WEIGHTS_0'] = done[key]
        print('MESH', doc['meshes'][mi]['name'], len(pos), 'verts:', int(skull.sum()), 'skull,', int((free & headset).sum()),
              'head shell and', int((free & ~headset & ~mane).sum()), 'socket solved,',
              int((h > 0).sum()), 'mane on the head,', tufts, 'rigid tufts')
write_glb(dst, doc, bytes(binary))
