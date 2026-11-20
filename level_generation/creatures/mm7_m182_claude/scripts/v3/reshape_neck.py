#!/usr/bin/env python3
"""v3b head pitch and neck reshape (system Python + Blender applier), in place on work/v3/uv_master.blend after the
UV restore (topology, UVs and weights unchanged; the join is repainted by compose_v3.py from 3D positions).

1. Head pitch: the grafted head (v3part 1) turns rigidly nose-down by head_pitch_deg about the jaw hinge (the cdr1
   Jaw bone head, so the jaw still opens about its own hinge). The cdr1 Standing clip lifts the head 23.5 deg above
   its rest; the skull axis (horn base -> snout) then pointed 3.6 deg below horizontal against 13-20 deg in the native
   side flight frames (sa2 20, wb2 17.6, wd2 15.5, wf2 13.5; mean 16.6): +13 deg brings Standing to 16.6.
2. Neck profile: one smooth tube from the cdr1 cut ring to a skull plane a_max behind the (turned) head ring: Hermite
   centreline with rotation-minimising frames; each vertex of the loft and of the head's neck stub (main head surface
   behind the skull plane, jaw-owned vertices excluded) is moved radially onto r(s, angle) = blend of the cdr1 ring
   profile and the skull-slice profile (smoothstep in s); head vertices fade in with their distance behind the skull
   plane. Frill spikes rooted in the stub (radius above 1.35x the local target) follow their root rigidly.
Usage: reshape_neck.py   (dumps, computes, applies via Blender; writes work/v3b/reshape_report.json)"""
import json, subprocess, sys
import numpy as np
from pathlib import Path

P = Path(__file__).resolve().parents[2]; W = P / 'work/v3b'; W.mkdir(parents=True, exist_ok=True)
prm = json.loads((P / 'work/v3/graft_params.json').read_text())
PITCH, AMAX = np.radians(prm.get('head_pitch_deg', 13.0)), prm.get('skull_plane_m', 0.05)
if '--apply' not in sys.argv:
    from scipy.spatial import cKDTree
    subprocess.run(['blender', '-b', '--factory-startup', str(P / 'work/v3/uv_master.blend'), '-P', str(P / 'scripts/v3/dump.py'), '--', str(W / 'pre_reshape.npz')], check=True, capture_output=True)
    d = np.load(W / 'pre_reshape.npz'); co = d['co'].copy(); part = d['pa_v3part']; hp = d['pa_hpiece']; Wt = d['W']; B = [str(b) for b in d['bones']]
    A = np.load(P / 'work/v3/src.npz'); Jc = A['heads'][list(A['bones']).index('Jaw')]
    pl = json.loads((P / 'work/v3/cut_plane.json').read_text()); c0 = np.array(pl['centre']); n0 = np.array(pl['normal'])
    tri = d['tri']; E = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    # rings: cdr1 ring = body vertices on the cut plane next to loft vertices; head ring = head vertices next to loft vertices
    adj_loft = np.zeros(len(co), bool); lm = part[E[:, 0]] == 2; adj_loft[E[lm, 1]] = True; lm = part[E[:, 1]] == 2; adj_loft[E[lm, 0]] = True
    ring0 = np.where(adj_loft & (part == 0) & (np.abs((co - c0) @ n0) < 1e-4))[0]
    ring1 = np.where(adj_loft & (part == 1))[0]
    # 1. pitch
    a = PITCH; R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    h = part == 1; co[h] = Jc + (co[h] - Jc) @ R.T
    c1 = co[ring1].mean(0); _, _, vt = np.linalg.svd(co[ring1] - c1); n1 = vt[2] * np.sign(vt[2] @ n0); c1[0] = 0
    cs = c1 + n1 * AMAX
    # 2. fairing: the loft and the head's neck stub (main head surface behind the plane through the jaw hinge,
    # perpendicular to the skull axis, offset BACK m; jaw-owned vertices excluded) are refitted as a minimum-curvature
    # (bi-Laplacian) surface between the cdr1 neck and the skull, so the v2 throat skin (shaped for v2's vertical neck)
    # no longer folds into a collar. Frill spikes rooted in the patch (painted frill texels at their UVs) follow
    # their root rigidly. Everything else is fixed (two rings on each side give a smooth tangent).
    import scipy.sparse as sp
    from scipy.sparse.linalg import spsolve
    snout = np.where(h & (hp == 1))[0]; tip = co[snout[np.argmin(co[snout, 1])]]
    axis = tip - Jc; axis[0] = 0; axis /= np.linalg.norm(axis)               # skull axis direction (forward)
    BACK = prm.get('stub_plane_back_m', 0.02)
    jaw = Wt[:, B.index('Jaw')]
    behind = (Jc - co) @ axis - BACK                                     # > 0: behind the stub plane
    # frill spikes: head vertices whose corners sample the Meshy head paint as frill (yellow-green or pale)
    from PIL import Image
    img = np.asarray(Image.open(P / 'meshy/head_retexture_v3/texture_urls_0_base_color.png').convert('HSV'), float) / 255
    Hn = img.shape[0]; uvc = d['uv']; mat = d['mat']; votes = np.zeros(len(co)); cnt = np.zeros(len(co))
    for c in range(3):
        sel = mat == 1; px = np.clip((uvc[sel, c, 0] * Hn).astype(int), 0, Hn - 1); py = np.clip(((1 - uvc[sel, c, 1]) * Hn).astype(int), 0, Hn - 1)
        hh, ss, vv = img[py, px, 0] * 360, img[py, px, 1], img[py, px, 2]
        fr = ((hh > 62) & (hh < 110) & (ss > .30) & (vv > .35)) | ((ss < .2) & (vv > .6))     # not the gold throat (35-60 deg)
        np.add.at(votes, tri[sel, c], fr); np.add.at(cnt, tri[sel, c], 1)
    spike = (cnt > 0) & (votes / np.maximum(cnt, 1) > .5) & (part == 1) & (hp == 1)
    # mirror partners of the (exactly symmetric) head: spike flags and the final positions are symmetrised
    hv_ = np.where(h)[0]; dmir, pidx = cKDTree(co[hv_]).query(co[hv_] * [-1, 1, 1]); partner = np.full(len(co), -1)
    partner[hv_[dmir < 1e-5]] = hv_[pidx[dmir < 1e-5]]
    sp2 = spike.copy(); has = partner >= 0; sp2[has] |= spike[partner[has]]; spike = sp2
    patch = (part == 2) | (h & (hp == 1) & (behind > 0) & (jaw < .2))
    free = patch & ~spike
    n = len(co); Ei = np.unique(np.sort(E, axis=1), axis=0)
    A_ = sp.coo_matrix((np.ones(2 * len(Ei)), (np.r_[Ei[:, 0], Ei[:, 1]], np.r_[Ei[:, 1], Ei[:, 0]])), shape=(n, n)).tocsr()
    A_.data[:] = 1; deg = np.asarray(A_.sum(1)).ravel()
    L = sp.identity(n) - sp.diags(1 / np.maximum(deg, 1)) @ A_
    M = (L.T @ L).tocsr(); F = np.where(free)[0]; X = np.where(~free)[0]
    MFF = M[F][:, F]; MFX = M[F][:, X]
    before = co.copy(); sol = np.column_stack([spsolve(MFF.tocsc(), -MFX @ co[X][:, k]) for k in range(3)])
    co[F] = sol
    disp = co - before
    sv = np.where(patch & spike)[0]
    if len(sv):
        nn = cKDTree(before[F]).query(before[sv])[1]; co[sv] = before[sv] + disp[F][nn]
    disp = co - before
    # separate head pieces (cheek/neck spikes, hpiece 3) rooted on the refitted stub follow their root
    sys.path.insert(0, str(P / 'scripts/v3')); from meshutil import components
    comp = components(tri, len(co)); moved_pieces = 0
    mainh = np.where(h & (hp == 1))[0]; mt = cKDTree(before[mainh])
    for c in np.unique(comp[h & (hp >= 2)]):
        vs = np.where(comp == c)[0]; dd, ii = mt.query(before[vs]); root = mainh[ii[np.argmin(dd)]]
        if np.linalg.norm(disp[root]) > 1e-5: co[vs] = before[vs] + disp[root]; moved_pieces += 1
    has = np.where(partner >= 0)[0]; co[has] = .5 * (co[has] + co[partner[has]] * [-1, 1, 1])
    # dorsal blades (v3part 3) rooted on the refitted loft/stub follow their root (they floated after v3b's first fit)
    d_ = co - before; blades = 0; base = np.where(part != 3)[0]; bt_ = cKDTree(before[base])
    for c in np.unique(comp[part == 3]):
        vs = np.where(comp == c)[0]; dd, ii = bt_.query(before[vs]); root = base[ii[np.argmin(dd)]]
        if np.linalg.norm(d_[root]) > 1e-5: co[vs] = before[vs] + d_[root]; blades += 1
    disp = co - before
    D = float(np.linalg.norm(c1 - c0)); zone = patch; spike_n = int((patch & spike).sum())
    np.save(W / 'neck_patch.npy', patch)
    sp_pt = Jc - axis * BACK
    ring_end = h & (hp == 1) & ~spike & (jaw < .2) & (np.abs((co - sp_pt) @ axis) < .01)
    end_c = co[ring_end].mean(0); end_c[0] = 0
    rep = {'neck_end_centre': end_c.tolist(), 'stub_plane_point': (Jc - axis * BACK).tolist(), 'skull_axis': axis.tolist(), 'jaw_hinge': Jc.tolist(), 'pitch_deg': float(np.degrees(PITCH)), 'skull_plane_m': AMAX, 'ring0': len(ring0), 'ring1': len(ring1), 'patch_vertices': int(zone.sum()), 'free_vertices': int(len(F)),
           'spike_vertices_rigid': spike_n, 'separate_pieces_moved': moved_pieces, 'dorsal_blades_moved': blades, 'max_move_mm': round(float(np.linalg.norm(disp, axis=1).max()) * 1000, 1), 'stub_plane_back_m': BACK}
    np.save(W / 'reshape_co.npy', co.astype(np.float32)); (W / 'reshape_report.json').write_text(json.dumps(rep, indent=1))
    print('RESHAPE', json.dumps(rep))
    r = subprocess.run(['blender', '-b', '--factory-startup', '-P', str(Path(__file__)), '--', '--apply'], capture_output=True, text=True)
    print([l for l in r.stdout.splitlines() + r.stderr.splitlines() if 'APPLIED' in l or 'rror' in l])
else:
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
    me = bpy.data.objects['Body'].data; co = np.load(W / 'reshape_co.npy')
    assert len(co) == len(me.vertices)
    me.vertices.foreach_set('co', co.ravel()); me.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/v3/uv_master.blend')); print('APPLIED', len(co))
