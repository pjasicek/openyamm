#!/usr/bin/env python3
"""Builder 2: remove the crown-shell triangles that a player standing under the tree sees against the sky
(coordinator, 2026-10-16: tree03's flat shell slab across a sky gap in the `up` view). System Python.

Run after select_cards.py (work/<id>/shell.npz holds the carved shell faces and the kept cards). The kept cards are
taken from work/<id>/installed.glb with shell.npz's l<lod>_keep and the species' `cards.grow` (as compose.py writes
them; the LOD0 bound-card re-keep is ignored, it only adds cards). Cameras: a ring under the crown, glTF y up, trunk
axis at x = z = 0, at heights `HEIGHTS` (m, not scaled, like render.py's `up`) and radii `RADII` around the axis,
16 azimuths. For every shell face that faces a camera, rays go from the camera to its centroid and to three points
halfway to its corners. A face goes when, from one camera, at least MIN_SKY (1) of its rays reach it unblocked (no opaque texel of a kept card, bark or
moss in front) and the same ray through the original model (every card) meets nothing: the shell fills a sky gap
of the original crown there. Faces that stand in for original cards stay. LOD0 and LOD1 only (LOD2
is not seen from under the tree). The first run keeps the input as work/<id>/shell_preunder.npz and later runs start
from it, so the step is repeatable. Then run b2_finish.sh <id> (compose, gate, winding).
Usage: b2_undercarve.py <id>"""
import io, os, shutil, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, glb

HEIGHTS = (1.2, 2.0, 2.8)
RADII = (0.9, 1.8, 2.7)
AZIMUTHS = 16
READD = float(os.environ.get("B2_READD", "0"))   # m: re-keep removed cards within this of a removed face
MIN_SKY = int(os.environ.get("B2_MIN_SKY", "1"))     # samples (of 4) per face that must see an original sky gap

tid = sys.argv[1]
spec = common.load(tid); W = spec['work']; C = spec['cards']
shp = os.path.join(W, 'shell.npz'); pre = os.path.join(W, 'shell_preunder.npz')
if not os.path.exists(pre):
    shutil.copy2(shp, pre)
sh = dict(np.load(pre))
m = glb.read(os.path.join(W, 'installed.glb'))


def per_lod(v, lod):
    return v[lod] if isinstance(v, (list, tuple)) else v


def texture_alpha(prim):
    mat = m.doc['materials'][prim['material']]
    if mat.get('alphaMode') != 'MASK':
        return None
    tex = m.doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    return np.asarray(Image.open(io.BytesIO(m.images[tex])).convert('RGBA'))[..., 3] >= 128


def occluders(lod, original=False):
    """Triangles (n, 3, 3), their UVs (n, 3, 2) and per-triangle alpha texture id (-1 = opaque). original: every
    card of the pre-pass model; else only the kept (and grown) cards."""
    mesh = m.mesh_chain()[lod]
    leaf = (m.primitive(mesh, 'LeavesFar') if lod == 2 else None) or m.primitive(mesh, 'Leaves')
    tris, uvs, tex_of, texes = [], [], [], []
    for p in m.doc['meshes'][mesh]['primitives']:
        pos = m.get(p['attributes']['POSITION']).astype(np.float64)
        idx = m.arrays[p['indices']].reshape(-1, 3)
        uv = m.get(p['attributes']['TEXCOORD_0']).astype(np.float64)
        if p is leaf and not original:
            keep = sh[f'l{lod}_keep']
            grow = per_lod(C['grow'], lod)
            q = pos.reshape(-1, 4, 3); c = q.mean(1, keepdims=True)
            pos = (c + (q - c) * grow).reshape(-1, 3)
            idx = idx[keep[idx[:, 0] // 4]]
        alpha = texture_alpha(p)
        tid_ = -1
        if alpha is not None:
            texes.append(alpha); tid_ = len(texes) - 1
        tris.append(pos[idx]); uvs.append(uv[idx]); tex_of.append(np.full(len(idx), tid_))
    return np.concatenate(tris), np.concatenate(uvs), np.concatenate(tex_of), texes


def hits(orig, dirs, tris, uvs, tex_of, texes):
    """Per ray: nearest opaque hit distance t (inf if none); orig (r, 3) ray origins, dirs (r, 3) unit directions."""
    best = np.full(len(dirs), np.inf)
    e1 = tris[:, 1] - tris[:, 0]; e2 = tris[:, 2] - tris[:, 0]
    for s in range(0, len(tris), 256):
        a, b, v0 = e1[s:s + 256], e2[s:s + 256], tris[s:s + 256, 0]
        pv = np.cross(dirs[:, None, :], b[None])                      # (r, t, 3)
        det = np.einsum('rtk,tk->rt', pv, a)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = orig[:, None, :] - v0[None]                               # (r, t, 3)
        u = np.einsum('rtk,rtk->rt', pv, tv) * inv
        qv = np.cross(tv, a[None])                                     # (r, t, 3)
        v = np.einsum('rk,rtk->rt', dirs, qv) * inv
        t = np.einsum('tk,rtk->rt', b, qv) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
        if not h.any():
            continue
        ri, ti = np.nonzero(h)
        tt = t[ri, ti]; tg = ti + s
        tx = tex_of[tg]
        opaque = tx < 0
        if (~opaque).any():
            k = ~opaque
            w0 = 1 - u[ri[k], ti[k]] - v[ri[k], ti[k]]
            uvh = (w0[:, None] * uvs[tg[k], 0] + u[ri[k], ti[k], None] * uvs[tg[k], 1] +
                   v[ri[k], ti[k], None] * uvs[tg[k], 2])
            res = np.zeros(k.sum(), bool)
            for j in np.unique(tx[k]):
                sel = tx[k] == j; al = texes[j]; hh, ww = al.shape
                px = np.clip((uvh[sel, 0] % 1.0 * ww).astype(int), 0, ww - 1)
                py = np.clip((uvh[sel, 1] % 1.0 * hh).astype(int), 0, hh - 1)
                res[sel] = al[py, px]
            opaque = opaque.copy(); opaque[k] = res
        np.minimum.at(best, ri[opaque], tt[opaque])
    return best


for lod in (0, 1):
    verts = sh[f'l{lod}_verts']; faces = sh[f'l{lod}_faces']
    if len(faces) == 0:
        continue
    fv = verts[faces]; fc = fv.mean(1)
    fn = np.cross(fv[:, 1] - fv[:, 0], fv[:, 2] - fv[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    samples = np.concatenate([fc[:, None], fc[:, None] + 0.5 * (fv - fc[:, None])], 1)    # (f, 4, 3)
    tris, uvs, tex_of, texes = occluders(lod)
    orig = occluders(lod, original=True)
    gone = np.zeros(len(faces), bool)
    for h in HEIGHTS:
        for r in RADII:
            for k in range(AZIMUTHS):
                a = 2 * np.pi * k / AZIMUTHS
                cam = np.array([r * np.sin(a), h, r * np.cos(a)])
                front = np.einsum('fk,fk->f', fn, cam - fc) > 0
                cand = np.nonzero(front & ~gone & (fc[:, 1] > cam[1]))[0]
                if len(cand) == 0:
                    continue
                p = samples[cand].reshape(-1, 3); d = p - cam; dist = np.linalg.norm(d, axis=1); d /= dist[:, None]
                # the shell face is seen (no kept card, bark or moss texel in front of it) where the original crown
                # showed sky along the whole ray: it fills an original sky gap
                o = np.repeat(cam[None], len(p), 0)
                visible = hits(o, d, tris, uvs, tex_of, texes) > dist - 1e-3
                sky = np.zeros(len(p), bool)
                vi = np.nonzero(visible)[0]
                if len(vi):
                    sky[vi] = np.isinf(hits(o[vi], d[vi], *orig))
                gone[cand[sky.reshape(-1, 4).sum(1) >= MIN_SKY]] = True
    sh[f'l{lod}_faces'] = faces[~gone]
    readd = 0
    if READD > 0 and gone.any():
        # the removed faces stood in for cards at eye level: re-keep the removed cards next to them, so the crown
        # keeps its eye-level cover (alpha-tested leaves read as leaves from below, not as a flat plane)
        from scipy.spatial import cKDTree
        mesh = m.mesh_chain()[lod]
        leaf = (m.primitive(mesh, 'LeavesFar') if lod == 2 else None) or m.primitive(mesh, 'Leaves')
        cc = m.get(leaf['attributes']['POSITION']).reshape(-1, 4, 3).mean(1)
        keep = sh[f'l{lod}_keep'].copy()
        near = cKDTree(fc[gone]).query(cc, distance_upper_bound=READD)[0] < READD
        add = near & ~keep
        keep |= add; readd = int(add.sum())
        sh[f'l{lod}_keep'] = keep
    print(f'UNDERCARVE {tid} LOD{lod} removed {int(gone.sum())} of {len(faces)} shell triangles seen against the sky '
          f'from under the crown; re-kept {readd} cards within {READD} m of them')
np.savez(shp, **sh)
print('UNDERCARVE wrote', shp)
