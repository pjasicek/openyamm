"""Pass 7 step B (Blender): the new head's game geometry in Fre's asm frame, from work/nh/prep.npz (symmetric Meshy pieces) and r72's head
shell (work/uv_tex2.npz component 'head', final positions).
1. Hair parting slit (Meshy cut the thick hair shell open along the parting, the skull showed through) closed: hair vertices beside the
   front-top midline move toward x = 0 by the slit's half-width, fading out 3 cm sideways; the two walls meet in the parting crease.
2. Slimmer bob (Meshy reproduced MM9's 20.7 cm wide cap; r72's was 16.2 cm): behind the face and above the jaw, hair and skull are
   narrowed by SLIM_X and the back shortened by SLIM_Y, smoothly (weight = smoothstep in y over the temples x smoothstep in z over the jaw
   line); the face, eyes and neck are not moved.
3. Neck cut: the Meshy bust is cut GAP above the slanted plane z = Z0 + SL (y - Y0); r72's shell is cut at that plane (both by
   bisection, clean planar rings). Small holes (eye-corner pinholes, midline pin holes) are closed to a point.
4. Symmetric decimation (collapse, X symmetry) per piece: face/skull/neck, hair, eyes.
5. The new neck's lowest 3.5 cm is moved radially (about the old ring's centre, per angle) onto r72's neck cross-section at the cut,
   fading upward, and the gap is bridged by one strip (zipper by angle): one connected skin from the face into r72's neck, whose bottom
   stays welded to the dress (unchanged positions).
Output npz: co, tri, piece (0 face/skull/neck, 1 hair, 2 eyes, 3 r72 neck, 4 bridge), old_wj/old_ww (r72 weights for pieces 3 and 4,
-1 elsewhere), ring_new/ring_old (vertex ids). Args: <prep npz> <out npz>   env: NH_Z0 NH_Y0 NH_SLOPE NH_GAP TRI_FACE TRI_HAIR TRI_EYES"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
E = os.environ.get
Z0, Y0, SL, GAP = float(E('NH_Z0', '0.556')), float(E('NH_Y0', '-0.05')), float(E('NH_SLOPE', '0.16')), float(E('NH_GAP', '0.004'))
TRIS = {0: int(E('TRI_FACE', '2900')), 1: int(E('TRI_HAIR', '1400')), 2: int(E('TRI_EYES', '200'))}
SLIM_X, SLIM_Y = float(E('SLIM_X', '0.10')), float(E('SLIM_Y', '0.08'))
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
D = np.load(IN); co, tri, pc = D['co'].copy(), D['tri'], D['piece']
# 1. parting slit
hv = pc == 1
WP = np.interp(co[:, 1], [-0.125, -0.115, -0.10, -0.09, -0.08, -0.07, -0.06, -0.05, -0.04, -0.03, -0.02], [0, .0045, .0045, .005, .0055, .0075, .0125, .0075, .0055, .002, 0])
ax = np.abs(co[:, 0]); k = 1 - ss(ax, WP + 0.006, WP + 0.03)
m = hv & (co[:, 2] > 0.70) & (WP > 0) & bool(int(E('SLIT_COLLAPSE', '0')))
co[m, 0] = np.sign(co[m, 0]) * np.maximum(ax[m] - WP[m] * k[m], 0)
co[m & (ax < WP + 0.0015), 0] = 0.0      # the walls land exactly on the midline: their faces are deleted and the halves welded below
print('SLIT closed: hair vertices moved', int((m & (k > 0)).sum()), 'max half-width', WP.max())
# 2. slimmer bob
w = ss(co[:, 1], -0.075, -0.015) * ss(co[:, 2], 0.585, 0.63) * np.isin(pc, [0, 1])
co[:, 0] *= 1 - SLIM_X * w; co[:, 1] -= SLIM_Y * np.maximum(co[:, 1], 0) * w
q = co[hv]; print('HAIR after slim: x', np.abs(q[:, 0]).max().round(4), 'y', q[:, 1].min().round(4), q[:, 1].max().round(4), 'z', q[:, 2].min().round(4), q[:, 2].max().round(4))
pn = Vector((0, -SL, 1)).normalized()
def build(c, t):
    me = bpy.data.meshes.new('m'); me.from_pydata(c.tolist(), [], t.tolist()); me.update()
    bm = bmesh.new(); bm.from_mesh(me); return bm
def close_small(bm, limit=8):
    seen = set(); n = 0
    for e in [e for e in bm.edges if e.is_boundary]:
        if e in seen: continue
        st = [e]; seen.add(e); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: seen.add(y); st.append(y)
        vs = list({v for x in cur for v in x.verts})
        if len(vs) <= limit:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=sum((v.co for v in vs), Vector()) / len(vs)); n += 1
    return n
def clean_nm(bm, tag, midline=False):
    """zero-area faces dissolved, then for every edge with more than two faces the smallest of them deleted (Meshy fins, welded slivers)"""
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:]); n = 0
    for _ in range(6):
        bad = [e for e in bm.edges if len(e.link_faces) > 2 and (not midline or (abs(e.verts[0].co.x) < 0.012 and abs(e.verts[1].co.x) < 0.012 and e.verts[0].co.z > 0.69))]
        if not bad: break
        kill = set()
        bm.normal_update()
        for e in bad:
            if midline:     # the parting's outer and inner hair surfaces pinch on this edge: the inner faces go (hidden inside the hair)
                kill.update(f for f in e.link_faces if f.normal.dot(f.calc_center_median() - Vector((0, 0.0, 0.68))) < 0)
            else:
                fs = sorted(e.link_faces, key=lambda f: f.calc_area())
                kill.update(fs[:len(fs) - 2])
        bmesh.ops.delete(bm, geom=list(kill), context='FACES_ONLY'); n += len(kill)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    hf = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=12)['faces']
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    print('CLEAN', tag, 'holes filled', len(hf))
    print('CLEAN', tag, 'faces deleted', n, 'nonmanifold left', sum(1 for e in bm.edges if len(e.link_faces) > 2))
def decimate(bm, target, name):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects: x.select_set(x is o)
    if len(me.polygons) > target:
        d = o.modifiers.new('D', 'DECIMATE'); d.ratio = target / len(me.polygons); d.use_symmetry = True; d.symmetry_axis = 'X'; d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='D')
    bm2 = bmesh.new(); bm2.from_mesh(o.data); bmesh.ops.triangulate(bm2, faces=[f for f in bm2.faces if len(f.verts) > 3])
    return bm2
parts = {}
for k in (0, 1, 2):
    sel = (pc[tri] == k).all(1); t = tri[sel]; u, i = np.unique(t, return_inverse=True)
    bm = build(co[u], i.reshape(-1, 3))
    if k == 1:      # hair parting slit: the slit's wall faces are deleted and the two outer edges (and the two inner edges) are bridged
                    # across the midline by mirror pairs (left and right edges are exact mirrors), a midline vertex per pair
        bm.normal_update()
        wall = [f for f in bm.faces if abs(f.normal.x) > float(E("WALL_NX", "0.25")) and all(abs(v.co.x) < 0.016 and -0.13 < v.co.y < -0.005 and v.co.z > 0.69 for v in f.verts)]
        bmesh.ops.delete(bm, geom=wall, context='FACES_ONLY'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.verts.ensure_lookup_table()
        import mathutils
        bm.verts.index_update(); VL = list(bm.verts)
        kd = mathutils.kdtree.KDTree(len(VL))
        for v in VL: kd.insert(v.co, v.index)
        kd.balance()
        def partner(v):
            co_, i_, d_ = kd.find(Vector((-v.co.x, v.co.y, v.co.z)))
            return VL[i_] if d_ < 2e-5 and VL[i_] is not v else None
        mids = {}; nb = 0
        def mid(a, b):
            k_ = (a.index, b.index)
            if k_ not in mids: mids[k_] = bm.verts.new(((a.co + b.co) / 2)); mids[k_].co.x = 0
            return mids[k_]
        bedges = [e for e in bm.edges if e.is_boundary and all(-0.13 < v.co.y < -0.005 and v.co.z > 0.69 and v.co.x < -1e-5 for v in e.verts)]
        bm.normal_update()
        bedges = [e for e in bedges if e.link_faces[0].normal.dot(e.link_faces[0].calc_center_median() - Vector((0, 0.005, 0.69))) > 0]    # outer surface only; the inner side stays open (hidden)
        for e in bedges:
            a, b = e.verts
            pa, pb = partner(a), partner(b)
            if pa is None or pb is None: print('SLIT unpaired edge', a.co[:], b.co[:]); continue
            ma, mb = mid(a, pa), mid(b, pb)
            for q in ((a, b, mb), (a, mb, ma), (pb, pa, ma), (pb, ma, mb)):
                try: bm.faces.new(q); nb += 1
                except ValueError: pass
        bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if abs(v.co.x) < 1e-6], dist=1e-5)
        seen = set(); nfill = 0
        for e in [e for e in bm.edges if e.is_boundary]:
            if e in seen: continue
            st = [e]; seen.add(e); cur = []
            while st:
                x = st.pop(); cur.append(x)
                for v in x.verts:
                    for y in v.link_edges:
                        if y.is_boundary and y not in seen: seen.add(y); st.append(y)
            if len(cur) <= 16: bmesh.ops.holes_fill(bm, edges=cur, sides=0); nfill += 1
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        print('SLIT small holes filled', nfill)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        clean_nm(bm, 'slit pinches', midline=True)
        print('SLIT walls deleted', len(wall), 'bridge faces', nb, 'hair boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2))
    if k == 0:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, Y0, Z0)) + pn * GAP, plane_no=-pn, clear_outer=True, dist=1e-6)
        print('FACE pin holes closed', close_small(bm))
    bm2 = decimate(bm, TRIS[k], f'p{k}'); bm.free()
    if k == 0: print('FACE pin holes after decimate', close_small(bm2))
    clean_nm(bm2, f'piece {k}', midline=(k == 1))
    if k == 1:      # dimples left on the welded parting: midline neighbourhood smoothed (x kept)
        Cc = Vector((0, 0.005, 0.69)); bm2.normal_update()
        junk = [f for f in bm2.faces if f.normal.dot((f.calc_center_median() - Cc).normalized()) < 0.5 and abs(f.calc_center_median().x) < 0.015
                and f.calc_center_median().z > 0.74 and -0.13 < f.calc_center_median().y < 0.03]
        bmesh.ops.delete(bm2, geom=junk, context='FACES_ONLY'); bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if not v.link_faces], context='VERTS')
        hf2 = bmesh.ops.holes_fill(bm2, edges=[e for e in bm2.edges if e.is_boundary], sides=24)['faces']
        bmesh.ops.triangulate(bm2, faces=[f for f in bm2.faces if len(f.verts) > 3]); bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
        print('HAIR parting band: inward/upright faces deleted', len(junk), 'holes filled', len(hf2), 'pin holes merged', close_small(bm2, 8))
        for P0, R0 in ((Vector((0, -0.036, 0.810)), 0.013), (Vector((0, -0.112, 0.752)), 0.010)):    # slit end pocket at the crown, notch at the hairline
            near = [v for v in bm2.verts if (v.co - P0).length < R0]
            ring = [v for v in bm2.verts if R0 * 1.2 < (v.co - P0).length < R0 * 2.2 and (v.co - Cc).length > (P0 - Cc).length - 0.006]
            if not ring: continue
            rt = sum((v.co - Cc).length for v in ring) / len(ring)
            for v in near:
                d_ = v.co - Cc; w_ = 1 - ((v.co - P0).length / R0) ** 2
                v.co = Cc + d_.normalized() * (d_.length + (max(rt, d_.length) - d_.length) * min(1.0, 1.5 * w_ + 0.5))
            print('HAIR pocket lifted at', tuple(round(x, 3) for x in P0), len(near), 'to r', round(rt, 4))
        sm = [v for v in bm2.verts if abs(v.co.x) < 0.012 and -0.125 < v.co.y < 0.0 and v.co.z > 0.72]
        for _ in range(4): bmesh.ops.smooth_vert(bm2, verts=sm, factor=0.5, use_axis_x=False, use_axis_y=True, use_axis_z=True)
    bm2.verts.ensure_lookup_table(); bm2.verts.index_update()
    parts[k] = (np.array([v.co[:] for v in bm2.verts]), np.array([[v.index for v in f.verts] for f in bm2.faces]))
    print('PIECE', k, len(parts[k][0]), 'verts', len(parts[k][1]), 'faces', 'boundary', sum(1 for e in bm2.edges if e.is_boundary))
    bm2.free()
# r72 shell below the plane
R = np.load(f'{HERE}/work/uv_tex2.npz'); W = np.load(f'{HERE}/work/weights.npz'); names = [str(x) for x in R['names']]
rco, rtri, rcomp, rorig = R['co'], R['tri'], R['comp'], R['orig']; h = names.index('head')
key = np.round(rco, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
P = np.zeros((inv.max() + 1, 3)); P[inv] = rco; src = np.zeros(inv.max() + 1, int); src[inv] = np.arange(len(rco))
ft = inv[rtri[(rcomp[rtri] == h).all(1)]]
below = P[:, 2] < Z0 + SL * (P[:, 1] - Y0) + 0.02
ft = ft[below[ft].any(1)]; u, i = np.unique(ft, return_inverse=True)
bm = build(P[u], i.reshape(-1, 3))
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, Y0, Z0)), plane_no=pn, clear_outer=True, dist=1e-6)
# largest connected piece
bm.verts.ensure_lookup_table(); seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    comps.append(cur)
comps.sort(key=len)
for c_ in comps[:-1]: bmesh.ops.delete(bm, geom=c_, context='VERTS')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
clean_nm(bm, 'r72 neck')
bm.verts.ensure_lookup_table(); bm.verts.index_update()
oc = np.array([v.co[:] for v in bm.verts]); ot = np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free()
# weights for r72 neck vertices (bisection made new ones): inverse distance over the 3 nearest original positions
_D2 = ((oc[:, None, :] - P[u][None]) ** 2).sum(2); ii = np.argsort(_D2, 1)[:, :3]; dd = np.sqrt(np.take_along_axis(_D2, ii, 1)); wsrc = src[u][ii]; wsrc = R['orig'][wsrc]
wnames = [str(x) for x in W['wnames']]; NB = len(wnames)
dense = np.zeros((len(oc), NB))
iw = 1 / np.maximum(dd, 1e-7); iw /= iw.sum(1, keepdims=True)
for kk in range(3):
    for c_ in range(4): np.add.at(dense, (np.arange(len(oc)), W['wj'][wsrc[:, kk], c_]), iw[:, kk] * W['ww'][wsrc[:, kk], c_])
def loops(t):
    e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1); uu, cc = np.unique(e, axis=0, return_counts=True); b = uu[cc == 1]
    adj = {}
    for a, b_ in b: adj.setdefault(a, []).append(b_); adj.setdefault(b_, []).append(a)
    seen = set(); out = []
    for s in adj:
        if s in seen: continue
        st = [s]; cur = []; seen.add(s)
        while st:
            x = st.pop(); cur.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); st.append(y)
        out.append(np.array(cur))
    return out
def plane_h(p): return (p - np.array([0, Y0, Z0])) @ np.array(pn)
ol = loops(ot); ring_o = max(ol, key=lambda l: plane_h(oc[l]).mean()); print('OLD loops', [len(l) for l in ol], 'top ring', len(ring_o), 'h', plane_h(oc[ring_o]).round(4).max())
fco, ftri = parts[0]; fl = loops(ftri); ring_n = min(fl, key=lambda l: plane_h(fco[l]).mean())
print('FACE loops', sorted(len(l) for l in fl), 'bottom ring', len(ring_n), 'h', plane_h(fco[ring_n]).min().round(4), plane_h(fco[ring_n]).max().round(4))
# 5. radial fit of the new neck onto r72's neck cross-section
C = oc[ring_o].mean(0)
def polar(p): d_ = p[:, :2] - C[:2]; return np.arctan2(d_[:, 1], d_[:, 0]), np.hypot(d_[:, 0], d_[:, 1])
def rad_of(ring_p):
    a, r = polar(ring_p); o_ = np.argsort(a); a, r = a[o_], r[o_]
    return lambda q: np.interp(q, np.r_[a - 2 * np.pi, a, a + 2 * np.pi], np.r_[r, r, r])
ro, rn = rad_of(oc[ring_o]), rad_of(fco[ring_n])
a, r = polar(fco); hh = plane_h(fco); fade = 1 - ss(hh, GAP, GAP + 0.035)
dr = (ro(a) - rn(a)) * fade
print('RADIAL fit: ring difference cm', np.round(100 * np.percentile(ro(a[ring_n]) - rn(a[ring_n]), [0, 50, 100]), 2), 'vertices moved', int((np.abs(dr) > 1e-4).sum()))
fco = fco.copy(); fco[:, 0] += dr * np.cos(a); fco[:, 1] += dr * np.sin(a)
parts[0] = (fco, ftri)
# assemble and bridge
allc, allt, allp = [], [], []
for k in (0, 1, 2):
    allt.append(parts[k][1] + sum(len(x) for x in allc)); allc.append(parts[k][0]); allp.append(np.full(len(parts[k][0]), k))
base_old = sum(len(x) for x in allc); allt.append(ot + base_old); allc.append(oc); allp.append(np.full(len(oc), 3))
co2 = np.vstack(allc); tri2 = np.vstack(allt); pc2 = np.concatenate(allp)
rn_i, ro_i = ring_n.copy(), ring_o + base_old
an, _ = polar(co2[rn_i]); ao, _ = polar(co2[ro_i]); rn_i, an = rn_i[np.argsort(an)], np.sort(an); ro_i, ao = ro_i[np.argsort(ao)], np.sort(ao)
bt = []; i_, j_ = 0, 0; NN, NO = len(rn_i), len(ro_i)
while i_ < NN or j_ < NO:
    an_next = an[(i_ + 1) % NN] + (2 * np.pi if i_ + 1 >= NN else 0); ao_next = ao[(j_ + 1) % NO] + (2 * np.pi if j_ + 1 >= NO else 0)
    if (j_ >= NO) or (i_ < NN and an_next <= ao_next):
        bt.append([rn_i[i_ % NN], rn_i[(i_ + 1) % NN], ro_i[j_ % NO]]); i_ += 1
    else:
        bt.append([rn_i[i_ % NN], ro_i[(j_ + 1) % NO], ro_i[j_ % NO]]); j_ += 1
bt = np.array(bt)
# orient: bridge normals point away from the neck axis
p3 = co2[bt]; nrm = np.cross(p3[:, 1] - p3[:, 0], p3[:, 2] - p3[:, 0]); out_ = p3.mean(1) - C; out_[:, 2] = 0
bt[(nrm * out_).sum(1) < 0] = bt[(nrm * out_).sum(1) < 0][:, ::-1]
pb = np.full(len(bt), 4)
tri3 = np.vstack([tri2, bt]); fpiece = np.r_[pc2[tri2[:, 0]], pb]
# consistent outward winding for the whole skin (face + r72 neck + bridge) and hair/eyes: Blender recalc
me = bpy.data.meshes.new('all'); me.from_pydata(co2.tolist(), [], tri3.tolist()); me.update()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
tri4 = np.array([[v.index for v in f.verts] for f in bm.faces])
print('BOUNDARY edges', sum(1 for e in bm.edges if e.is_boundary), 'NONMANIFOLD', sum(1 for e in bm.edges if len(e.link_faces) > 2)); bm.free()
old_dense = np.full((len(co2), NB), -1.0); old_dense[base_old:] = dense
np.savez(OUT, co=co2, tri=tri4, fpiece=fpiece, piece=pc2, comp=pc2, old_dense=old_dense, wnames=np.array(wnames), ring_new=rn_i, ring_old=ro_i, centre=C,
         z0=Z0, y0=Y0, slope=SL, gap=GAP)
for k in range(5): print('FACES piece', k, int((fpiece == k).sum()))
print('TOTAL faces', len(tri4), 'verts', len(co2))
