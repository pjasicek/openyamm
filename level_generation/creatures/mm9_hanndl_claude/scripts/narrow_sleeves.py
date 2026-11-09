"""Hanndl = PeasantM6 (Annud's body) without the bell cuffs: MM9's PeasantM6 has 10 extra vertices per forearm, a bell
flare up to 11 cm out at the cuff, which Hanndl.abc lacks (his sleeves are fitted to the wrist). Annud's HD body has
wide sleeves along the whole forearm (his HD master), so the sleeve is narrowed onto the forearm here.

Vertex moves only (UVs, weights, attributes and topology stay). Per arm: sleeve = body-only vertices (no head/hand face)
whose strongest bone is that side's UpperArm, Forearm or Hand, with an axial position a (elbow 0 .. hand joint 1 along
the Forearm->Hand bone) above A_LO. Per 1 cm slice: the sleeve centroid (smoothed), the outer radius r_out (90th
percentile) and the forearm stub's radius r_stub around it (Annud's stub runs up the sleeve to 6 cm from the elbow).
Target outer radius R(a) = r_stub(a) + ease(a) (ease EASE_ELBOW at a = A0 .. EASE_CUFF at the sleeve end), never more
than the current one; the blend k(a) = R / r_out starts at A_LO (1) and is complete by A0. Each sleeve vertex is scaled
about the centroid line by k(a) in the plane across the arm (inner layer and outer layer alike, so the cloth keeps its
thickness ordering). Mode `upload`: the same displacement applied to a Meshy upload GLB by exact rest-position matching.
Args (Blender): master <in blend> <out blend> <report json>  |  upload <master in blend> <in glb> <out glb>
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
E_ = lambda k, d: float(os.environ.get(k, d))
A_LO, A0 = E_('A_LO', -0.15), E_('A0', 0.25)
EASE_ELBOW, EASE_CUFF = E_('EASE_ELBOW', 0.024), E_('EASE_CUFF', 0.018)
MARGIN = E_('MARGIN', 0.016)            # covers the chord sag of the low-poly sleeve ring between its vertices


def rest_master(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    body = bpy.data.objects['Body']; rig = body.parent
    if rig.animation_data: rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
    bpy.context.view_layer.update()
    return body, rig


def displacement(body, rig):
    me = body.data; mw = body.matrix_world
    P = np.array([mw @ v.co for v in me.vertices])
    L = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', L)
    n = len(me.polygons)
    ls = np.zeros(n, np.int32); me.polygons.foreach_get('loop_start', ls)
    lt = np.zeros(n, np.int32); me.polygons.foreach_get('loop_total', lt)
    hd = np.zeros(n, np.int32); me.attributes['head'].data.foreach_get('value', hd)
    hn = np.zeros(n, np.int32); me.attributes['hand'].data.foreach_get('value', hn)
    special = np.zeros(len(P), bool); plain = np.zeros(len(P), bool)
    for f in range(n):
        vs = L[ls[f]:ls[f] + lt[f]]
        if hd[f] or hn[f]: special[vs] = True
        else: plain[vs] = True
    hand_only = special & ~plain
    gname = {g.index: g.name for g in body.vertex_groups}
    top = []
    for v in me.vertices:
        gs = sorted(v.groups, key=lambda g: -g.weight)
        top.append(gname.get(gs[0].group, '') if gs else '')
    top = np.array(top)
    D = np.zeros_like(P); rep = {}
    for s in 'LR':
        bf, bh = rig.data.bones[f'Bip01 {s} Forearm'], rig.data.bones[f'Bip01 {s} Hand']
        E = np.array(rig.matrix_world @ bf.head_local); W = np.array(rig.matrix_world @ bh.head_local)
        ln = np.linalg.norm(W - E); ax = (W - E) / ln
        side = np.isin(top, [f'Bip01 {s} UpperArm', f'Bip01 {s} Forearm', f'Bip01 {s} Hand'])
        rel = P - E; a = rel @ ax / ln
        sl = np.where(plain & ~special & side & (a > A_LO - 0.1))[0]
        st = np.where(hand_only & (a > 0.0) & (a < 1.0) & (np.linalg.norm(rel - np.outer(rel @ ax, ax), axis=1) < 0.06))[0]
        a_end = a[sl].max()
        # forearm centre line and radius from the stub (Annud's forearm skin inside the sleeve): line fits over a
        sa = a[st]; good = (sa > 0.15) & (sa < a_end - 0.03)
        bins = np.arange(0.15, a_end, 0.05); cs, ag = [], []
        for g in bins:
            m = good & (np.abs(sa - g) < 0.04)
            if m.sum() >= 4: cs.append(P[st[m]].mean(0)); ag.append(g)
        cs, ag = np.array(cs), np.array(ag)
        A = np.stack([np.ones_like(ag), ag], 1); coef = np.linalg.lstsq(A, cs, rcond=None)[0]
        line = lambda x: coef[0] + np.outer(x, coef[1])
        dirl = coef[1] / np.linalg.norm(coef[1])
        def radial(idx):
            d = P[idx] - line(a[idx]); d -= np.outer(d @ dirl, dirl); return d, np.linalg.norm(d, axis=1)
        _, rst_ = radial(st[good])
        rs = []
        for g in ag:
            m = np.abs(a[st[good]] - g) < 0.04; rs.append(np.percentile(rst_[m], 90))
        rc = np.polyfit(ag, rs, 1); r_stub = lambda x: np.polyval(rc, x)
        dvec, r = radial(sl)
        ease = np.interp(a[sl], [A0, a_end], [EASE_ELBOW, EASE_CUFF])
        exc = np.maximum(r - r_stub(a[sl]), 0.0)
        new_exc = ease * (1 - np.exp(-exc / ease))
        r_new = np.where(r > r_stub(a[sl]), r_stub(a[sl]) + new_exc, r)
        # clamp (2026-11-02, sleeve_poke_gate: the right stub came 5 mm through the narrowed sleeve at rest): the stub is
        # not round, so every sleeve vertex stays MARGIN outside the stub's own radius in its direction (12 angle bins
        # per 4 cm slice around the centre line, max over the bin and its neighbours)
        ref = np.cross(dirl, [0.0, 0.0, 1.0]); ref /= np.linalg.norm(ref); ref2 = np.cross(dirl, ref)
        def ang(dv): return np.arctan2(dv @ ref2, dv @ ref)
        dst, rst = radial(st)
        ab, sb = (ang(dst) + np.pi) / (2 * np.pi) * 12, a[st]
        def stub_r(av, angv):
            bi = (angv + np.pi) / (2 * np.pi) * 12
            out = np.zeros(len(av))
            for i in range(len(av)):
                m = (np.abs(sb - av[i]) < 0.13) & ((np.abs(ab - bi[i]) % 12 < 1.5) | (np.abs(ab - bi[i]) % 12 > 10.5))
                out[i] = rst[m].max() if m.any() else r_stub(av[i])
            return out
        floor_r = stub_r(a[sl], ang(dvec)) + MARGIN
        r_new = np.maximum(r_new, np.minimum(floor_r, r))
        blend = np.clip((a[sl] - A_LO) / (A0 - A_LO), 0, 1); blend = blend * blend * (3 - 2 * blend)
        r_fin = r + blend * (r_new - r)
        D[sl] = dvec / np.maximum(r, 1e-9)[:, None] * (r_fin - r)[:, None]
        _, ro = radial(sl); prof = []
        for g in np.arange(-0.1, a_end + 0.01, 0.1):
            m = np.abs(a[sl] - g) < 0.05
            if m.sum(): prof.append([round(float(g), 1), round(float(ro[m].max()) * 100, 1), round(float(r_fin[m].max()) * 100, 1), round(float(r_stub(g)) * 100, 1)])
        rep[s] = dict(sleeve_verts=int(len(sl)), stub_verts=int(len(st)), a_end=float(a_end),
                      profile_a_rmax_before_after_stub_cm=prof,
                      max_move_cm=float(np.linalg.norm(D[sl], axis=1).max() * 100))
    return P, D, rep


if argv[0] == 'master':
    body, rig = rest_master(argv[1])
    P, D, rep = displacement(body, rig)
    inv = np.array(body.matrix_world.inverted().to_3x3())
    for i in np.where(np.abs(D).sum(1) > 0)[0]:
        body.data.vertices[i].co += Vector(inv @ D[i])
    body.data.update()
    np.save(os.path.splitext(argv[3])[0] + '_disp.npy', np.concatenate([P, D], 1))
    json.dump(rep, open(argv[3], 'w'), indent=1)
    print('NARROW', {s: (r['sleeve_verts'], r['stub_verts'], round(r['max_move_cm'], 1)) for s, r in rep.items()})
    bpy.ops.wm.save_as_mainfile(filepath=argv[2])


if argv[0] == 'upload':
    # argv: upload <disp npy (P|D from master mode)> <in glb> <out glb>
    PD = np.load(argv[1]); P0, D0 = PD[:, :3], PD[:, 3:]
    mv = np.abs(D0).sum(1) > 0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=argv[2])
    moved, worst = 0, 0.0
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        mw = o.matrix_world; inv = np.array(mw.inverted().to_3x3())
        Q = np.array([mw @ v.co for v in o.data.vertices])
        src = P0[mv]
        for i, q in enumerate(Q):
            d = np.linalg.norm(src - q, axis=1); j = int(d.argmin())
            if d[j] < 1e-4:
                o.data.vertices[i].co += Vector(inv @ D0[mv][j]); moved += 1
        # unmatched vertices near the moved region would tear: report the nearest moved-vertex distance stats
        dall = np.array([np.linalg.norm(P0 - q, axis=1).min() for q in Q[::7]])
        worst = max(worst, float(dall.max()))
        o.data.update()
    print('UPLOAD moved', moved, 'of', int(mv.sum()), 'worst unmatched sample dist', worst)
    bpy.ops.export_scene.gltf(filepath=argv[3], export_format='GLB', export_yup=True, export_apply=False,
                              export_materials='EXPORT', export_texcoords=True, export_normals=True)
