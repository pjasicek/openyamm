"""The cut at the wrist as one skin: forearm and MPFB stub are each cut on a plane across the forearm, the stub's radii conform to the forearm ring, and the two rings are bridged, then relaxed.
Args: <hands blend> <hands json> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
IN, JS, OUT = sys.argv[sys.argv.index('--') + 1:]
A_ARM, A_STUB, FALL = -0.115, -0.075, 0.07
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
rep = json.load(open(JS))
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int['hand']; lay = bm.verts.layers.int['part']
print('WRIST world?', [round(x, 3) for x in body.matrix_world.to_translation()])
for key, Fr in rep['frames'].items():
    W, d = np.array(Fr['W']), np.array(Fr['d']); d = d / np.linalg.norm(d)
    U = np.cross(d, [0, 0, 1.0]); U /= np.linalg.norm(U); Vv = np.cross(d, U)
    al = lambda p: (p - W) @ d
    rad = lambda p: np.linalg.norm(p - W - d * al(p))
    # the arm's cut
    fs = [f for f in bm.faces if f[hl] == 0 and np.sign(f.calc_center_median().x) == np.sign(W[0]) and rad(np.array(f.calc_center_median()[:])) < 0.22 and -0.35 < al(np.array(f.calc_center_median()[:])) < 0.1 and all(v[lay] == 0 for v in f.verts)]
    vs = list({v for f in fs for v in f.verts}); es = list({e for f in fs for e in f.edges})
    r = bmesh.ops.bisect_plane(bm, geom=vs + es + fs, plane_co=W + d * A_ARM, plane_no=d, clear_outer=True)
    fs = [f for f in bm.faces if f[hl] == 1 and np.linalg.norm(np.array(f.calc_center_median()[:]) - W) < 0.7]
    vs = list({v for f in fs for v in f.verts}); es = list({e for f in fs for e in f.edges})
    r = bmesh.ops.bisect_plane(bm, geom=vs + es + fs, plane_co=W + d * A_STUB, plane_no=d, clear_inner=True)
    bm.faces.ensure_lookup_table()
    def ring(a0, handflag):
        out = []
        for e in bm.edges:
            if not e.is_boundary: continue
            ok = True
            for v in e.verts:
                p = np.array(v.co[:])
                if abs(al(p) - a0) > 0.0012 or rad(p) > 0.22: ok = False
            if ok and e.link_faces[0][hl] == handflag: out.append(e)
        return out
    ea, eb = ring(A_ARM, 0), ring(A_STUB, 1)
    va = list({v for e in ea for v in e.verts}); vb = list({v for e in eb for v in e.verts})
    Pa = np.array([v.co[:] for v in va]); Pb = np.array([v.co[:] for v in vb])
    q2 = lambda Q: np.c_[(Q - W) @ U, (Q - W) @ Vv]
    a2, b2 = q2(Pa), q2(Pb); ca, cb = a2.mean(0), b2.mean(0)
    print('WRIST', key, 'rings', len(ea), len(eb), 'c', np.round(ca, 3), np.round(cb, 3), 'ext', np.round(np.ptp(a2, 0), 3), np.round(np.ptp(b2, 0), 3))
    def polar(q, c):
        an = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]); rr = np.hypot(q[:, 1] - c[1], q[:, 0] - c[0]); o = np.argsort(an)
        return an[o], rr[o]
    aa, ra = polar(a2, ca); ab, rb = polar(b2, cb)
    per = lambda x, xp, fp: np.interp(x, np.r_[xp - 2 * np.pi, xp, xp + 2 * np.pi], np.r_[fp, fp, fp])
    stub = {v for f in bm.faces if f[hl] == 1 and np.linalg.norm(np.array(f.calc_center_median()[:]) - W) < 0.7 for v in f.verts}
    for v in stub:
        p = np.array(v.co[:]); t = al(p) - A_STUB
        if t > FALL: continue
        w = 1 - t / FALL; w = w * w * (3 - 2 * w)
        q = q2(p[None])[0]; an = np.arctan2(q[1] - cb[1], q[0] - cb[0]); rr = np.hypot(q[1] - cb[1], q[0] - cb[0])
        tgt = ca + np.array([np.cos(an), np.sin(an)]) * rr * per(an, aa, ra) / max(per(an, ab, rb), 1e-4) * 0.99
        nq = q + (tgt - q) * w
        v.co = Vector(W + d * al(p) + U * nq[0] + Vv * nq[1])
    # zip the two rings by polar angle (bridge_loops twisted them)
    def order(vv, c):
        q = q2(np.array([v.co[:] for v in vv])); an = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]); o = np.argsort(an)
        return [vv[i] for i in o], an[o]
    ra_, ana = order(va, ca); rb_, anb = order(vb, cb)
    na, nb_ = len(ra_), len(rb_)
    i = j = 0; made = []
    # start at the nearest pair
    j0 = int(np.argmin(np.abs(np.angle(np.exp(1j * (anb - ana[0]))))))
    rb_ = rb_[j0:] + rb_[:j0]; anb = np.r_[anb[j0:], anb[:j0] + 2 * np.pi]; anb = np.where(anb < ana[0] - 1, anb + 2 * np.pi, anb)
    ana2 = np.r_[ana, ana[0] + 2 * np.pi]; anb2 = np.r_[anb, anb[0] + 2 * np.pi]
    while i < na or j < nb_:
        adv_a = j >= nb_ or (i < na and ana2[i + 1] - ana2[i] + ana2[i] <= anb2[j + 1])
        a0, b0 = ra_[i % na], rb_[j % nb_]
        if adv_a:
            f = bm.faces.new((a0, ra_[(i + 1) % na], b0)); i += 1
        else:
            f = bm.faces.new((a0, rb_[(j + 1) % nb_], b0)); j += 1
        f[hl] = 0; f.smooth = True; made.append(f)
    # outward
    for f in made:
        c = np.array(f.calc_center_median()[:]); f.normal_update()
        out = c - W - d * al(c)
        if np.array(f.normal[:]) @ out < 0: f.normal_flip()
    print('WRIST zipped', len(made))
    band = [v for v in bm.verts if -0.16 < al(np.array(v.co[:])) < -0.03 and rad(np.array(v.co[:])) < 0.22 and np.sign(v.co.x) == np.sign(W[0]) and v[lay] == 0]
    for _ in range(4):
        mv = {}
        for v in band:
            nb = [e.other_vert(v).co for e in v.link_edges]
            mv[v] = sum(nb, Vector()) / len(nb)
        for v, c in mv.items(): v.co = v.co * 0.5 + c * 0.5
    # the wrist and forearm carry a wrap: the ring keeps the arm's weights by interpolation
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('WRIST done verts', len(me.vertices))
