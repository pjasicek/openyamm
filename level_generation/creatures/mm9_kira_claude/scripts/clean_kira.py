"""Kira (from mm9_njam_claude/scripts/clean_nj.py): clean and reduce the Meshy return: scale to MM9's height on MM9's floor, label
pieces on the WHOLE return first (Meshy units), keep the figure's RIGHT half (x < 0: Meshy's face has a lip blob on the left mouth
corner and the left vambrace is a loose piece), fill pin holes, reduce per garment with the joints protected, mirror (MM9 is symmetric
apart from the braid, which is rebuilt). The head stays (face 20, hair 21, eyes 22); Meshy's braid stub over the right collar goes.
Parts: 1 armour shell (cuirass, sleeves, vambraces, mail skirt: skirt 7 split by height afterwards), 4 gloves (by position, replaced by
the MPFB graft), 5 legs (leggings and boots), 9 belt + buckle, 10 medallion, 11 knee cops, 12 pauldron lames, 13 tasset panel.
Args: <meshy glb> <mm9 src glb> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MESHY, MM9, OUT, REP = a
rep = {}
NAMES = {1: 'armour', 4: 'glove', 5: 'legs', 9: 'belt', 10: 'medallion', 11: 'kneecop', 12: 'pauldron', 13: 'tasset', 15: 'drop',
         20: 'face', 21: 'hair', 22: 'eye'}
RATIO = {1: 0.7, 4: 1.0, 5: 0.6, 9: 0.6, 10: 0.5, 11: 0.7, 12: 0.7, 13: 0.7, 15: 1.0, 20: 1.0, 21: 0.8, 22: 1.0}
# joints kept dense, figure's right (x < 0), Meshy's A-pose scaled: shoulder, elbow, wrist, hip, knee, ankle
JOINTS = [(-.21, .0, .53), (-.33, .0, .35), (-.43, .0, .19), (-.09, .0, .0), (-.12, .0, -.40), (-.15, .0, -.72)]


def label(q):
    """Meshy units (height 1, centred), Blender axes, the whole return."""
    lo, hi = q.min(0), q.max(0); e = hi - lo; c = q.mean(0); n = len(q)
    if n > 2000: return 1                                     # armour shell with arms and gloves
    if n > 1000 and lo[2] < -0.4: return 5                    # legs and boots
    if lo[2] > 0.32 and e[0] < 0.12 and n > 500: return 20    # face and neck skin
    if lo[2] > 0.15 and hi[2] > 0.48 and n > 400: return 21   # hair
    if lo[2] > 0.4 and hi[2] < 0.45 and n < 120: return 22    # eyeballs
    if abs(c[0]) < 0.02 and 0.27 < c[2] < 0.36: return 10     # medallion
    if 0.13 < lo[2] and hi[2] < 0.18: return 9                # belt and buckle
    if -0.02 < lo[2] < 0.0 and 0.14 < hi[2] < 0.16: return 13 # tasset panel
    if hi[2] < -0.15 and lo[2] > -0.3: return 11              # knee cops
    if 0.23 < lo[2] and hi[2] < 0.37 and abs(c[0]) > 0.07: return 12   # pauldron lames
    if abs(c[0]) > 0.15: return 4                             # loose vambrace (left; gone with the bisect)
    return 15                                                 # Meshy's braid stub


def components(bm):
    bm.verts.ensure_lookup_table()
    seen = set(); out = []
    for v in bm.verts:
        if v in seen: continue
        st = [v]; seen.add(v); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y)
        out.append(cur)
    return out


def boundary_comps(bm):
    seen = set(); comps = []
    for e in [e for e in bm.edges if e.is_boundary]:
        if e in seen: continue
        st = [e]; seen.add(e); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: seen.add(y); st.append(y)
        comps.append(cur)
    return comps


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh_b = next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith('kira'))
mp = np.array([mesh_b.matrix_world @ v.co for v in mesh_b.data.vertices])
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
o = next(x for x in new if x.type == 'MESH')
M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
for x in new:
    if x is not o: bpy.data.objects.remove(x)
for x in list(bpy.data.objects):
    if x.type == 'MESH' and x is not o: bpy.data.objects.remove(x)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.name = 'Body'; o.data.name = 'Body'; o.data.materials.clear()
me = o.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
# labels on the whole return, Meshy units (gloves: armour faces past the vambrace cuff, x > 0.232 below z 0.075)
lay = bm.faces.layers.int.new('part')
info = []; drop = []
for cur in components(bm):
    q = np.array([v.co for v in cur]); lb = label(q)
    info.append((NAMES[lb], len(cur), q.min(0).round(3).tolist(), q.max(0).round(3).tolist()))
    fs = {f for v in cur for f in v.link_faces}
    if lb == 15 or (lb == 4):
        drop.extend(cur); continue
    for f in fs:
        c = f.calc_center_median()
        f[lay] = 4 if (lb == 1 and abs(c.x) > 0.232 and c.z < 0.075) else lb
bmesh.ops.delete(bm, geom=drop, context='VERTS')
for i in sorted(info, key=lambda x: -x[1]): print('PIECE', i)
co = np.array([v.co for v in bm.verts])
s = np.ptp(mp[:, 2]) / np.ptp(co[:, 2])
t = np.array([-(co[:, 0].min() + co[:, 0].max()) / 2 * s, 0.0, mp[:, 2].min() - co[:, 2].min() * s])
for v in bm.verts:
    v.co = Vector(np.array(v.co) * s + t)
rep['scale'] = float(s)
# each central piece on its own mid-plane (Meshy's pieces sit up to 1 cm off the bbox centre); face, hair and eyes move together by
# the face's front (nose, lips, chin: the frontmost 3 cm), so the eyes stay in their sockets
lay = bm.faces.layers.int['part']
def vpart(v): return v.link_faces[0][lay] if v.link_faces else 0
head = [v for v in bm.verts if vpart(v) in (20, 21, 22)]
fq = np.array([v.co for v in bm.verts if vpart(v) == 20])
fr = fq[(fq[:, 1] < fq[:, 1].min() + 0.03) & (fq[:, 2] > fq[:, 2].min() + 0.03)]
dxh = -(fr[:, 0].min() + fr[:, 0].max()) / 2
print('MIDPLANE head', len(head), round(float(dxh), 4))
for v in head: v.co.x += dxh
for cur in components(bm):
    if vpart(cur[0]) in (20, 21, 22): continue
    q = np.array([x.co for x in cur]); lo, hi = q.min(0), q.max(0)
    if lo[0] < 0 < hi[0] and len(cur) > 100:
        if np.ptp(q[:, 0]) > 0.6: band = (np.abs(q[:, 0]) < 0.2) & (q[:, 2] > 0.1) & (q[:, 2] < 0.5)
        elif hi[2] < 0.3 and lo[2] < -0.3: band = (q[:, 2] > -0.05) & (q[:, 2] < 0.15)
        else: band = np.ones(len(q), bool)
        dx = -(q[band, 0].min() + q[band, 0].max()) / 2
        print('MIDPLANE', len(cur), round(float(dx), 4))
        for x in cur: x.co.x += dx
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 2e-5: v.co.x = 0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# pin holes (short boundary cycles off the mid-plane): fan from the centre
filled = 0
for _ in range(3):
    used = set()
    for e0 in [e for e in bm.edges if e.is_boundary]:
        if e0 in used: continue
        cyc = [e0]; start = e0.verts[0]; cur = e0.verts[1]; ok = False
        while len(cyc) < 10:
            nxt = [e for e in cur.link_edges if e.is_boundary and e not in cyc and e not in used]
            if not nxt: break
            cyc.append(nxt[0]); cur = nxt[0].other_vert(cur)
            if cur is start: ok = True; break
        used.update(cyc)
        if not ok: continue
        vs = [start]; x = start
        for e in cyc[:-1]:
            x = e.other_vert(x); vs.append(x)
        if sum(1 for v in vs if abs(v.co.x) < 1e-4) > 1: continue
        c = sum((v.co for v in vs), Vector()) / len(vs)
        nv = bm.verts.new(c)
        for a_, b_ in zip(vs, vs[1:] + vs[:1]):
            try: bm.faces.new((a_, b_, nv))
            except ValueError: pass
        filled += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
rep['holes'] = filled
lay = bm.faces.layers.int['part']
for _ in range(4):
    for f in bm.faces:
        if f[lay] == 0:
            nb = [g[lay] for e in f.edges for g in e.link_faces if g is not f and g[lay]]
            if nb: f[lay] = nb[0]
bm.to_mesh(me); bm.free()
# reduce per garment, joints protected
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
objs = []
for lb in sorted(set(fp.tolist())):
    x = o.copy(); x.data = me.copy(); sc.collection.objects.link(x)
    bm = bmesh.new(); bm.from_mesh(x.data); bm.faces.ensure_lookup_table()
    lay = bm.faces.layers.int['part']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != lb], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(x.data); bm.free()
    n0 = len(x.data.polygons)
    if RATIO[lb] < 1:
        g = x.vertex_groups.new(name='keep')
        for v in x.data.vertices:
            d = min(((np.array(v.co) - np.array(j)) ** 2).sum() ** 0.5 for j in JOINTS)
            w = float(np.clip(1 - (d - 0.06) / 0.08, 0.0, 1.0))
            if abs(v.co.x) < 1e-5: w = 1.0
            g.add([v.index], w, 'REPLACE')
        dm = x.modifiers.new('D', 'DECIMATE'); dm.ratio = RATIO[lb]; dm.vertex_group = 'keep'; dm.invert_vertex_group = True; dm.vertex_group_factor = 3.0; dm.use_collapse_triangulate = True
        bpy.ops.object.select_all(action='DESELECT'); x.select_set(True); bpy.context.view_layer.objects.active = x
        bpy.ops.object.modifier_apply(modifier='D')
        x.vertex_groups.clear()
    x.data.attributes['part'].data.foreach_set('value', [lb] * len(x.data.polygons))
    if lb in (1, 5, 12, 13):                          # Meshy's sawtooth rims (hem, lames, cuffs, boot tops), relaxed along the rim
        bm = bmesh.new(); bm.from_mesh(x.data)
        for _ in range(3):
            mv = {}
            for v in bm.verts:
                nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb) == 2 and abs(v.co.x) > 1e-4:
                    mv[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
            for v, c in mv.items(): v.co = c
        bm.to_mesh(x.data); bm.free()
    rep.setdefault('reduce', {})[NAMES[lb]] = [n0, len(x.data.polygons)]
    objs.append(x)
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects.remove(o)
for x in objs: x.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
o = objs[0]; o.name = 'Body'; o.data.name = 'Body'; me = o.data
bm = bmesh.new(); bm.from_mesh(me)
for v in bm.verts:
    if abs(v.co.x) < 3e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
filled = 0
for _ in range(2):
    for cur in boundary_comps(bm):
        vs = list({v for e in cur for v in e.verts})
        q = np.array([v.co for v in vs]); ext = np.ptp(q, axis=0)
        if len(cur) <= 6 and np.sort(ext)[1] < 0.003:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=Vector(q.mean(0))); filled += 1
        elif len(cur) <= 20 and ext.max() < 0.04:
            bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur)); filled += 1
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=bm.faces)
rep['seam_filled'] = filled
bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
for _ in range(6):
    for f in bm.faces:
        if f[lay] == 0:
            nb = [g[lay] for e in f.edges for g in e.link_faces if g is not f and g[lay]]
            if nb: f[lay] = nb[0]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# mail skirt split from the armour shell below the belt
bz = [f.calc_center_median().z for f in bm.faces if f[lay] == 9]
BELT_LO = float(np.percentile(bz, 5)) if bz else 0.15
rep['belt_lo'] = round(BELT_LO, 4)
for f in bm.faces:
    c = f.calc_center_median()
    if f[lay] == 1 and abs(c.x) < 0.26 and c.z < BELT_LO + 0.005: f[lay] = 7
# mirror seam: light Laplacian on y, z near x = 0
vp = {v: {f[lay] for f in v.link_faces} for v in bm.verts}
for it in range(3):
    mv = {}
    for v in bm.verts:
        if any(e.is_boundary for e in v.link_edges) and abs(v.co.x) > 1e-5: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        if not nb: continue
        c = sum(nb, Vector()) / len(nb)
        if abs(v.co.x) < 0.012 and vp[v] & {1, 5, 7, 9, 13}:
            mv[v] = Vector((v.co.x, v.co.y * 0.4 + c.y * 0.6, v.co.z * 0.4 + c.z * 0.6))
    for v, c in mv.items(): v.co = c
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
bm = bmesh.new(); bm.from_mesh(me)
rep['boundary'] = sum(1 for e in bm.edges if e.is_boundary); rep['over2'] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
rep['boundary_rings'] = sorted([len(c) for c in boundary_comps(bm)], reverse=True)[:20]
bm.free()
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
rep['parts'] = {int(k): int((fp == k).sum()) for k in np.unique(fp)}
rep['tris'] = len(me.polygons); rep['verts'] = len(me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=0)
print('CLEAN', json.dumps(rep)[:900])
