"""Clean and reduce the Meshy body: scale to MM9's height on MM9's floor, drop its head (the head-only job replaces it) and the one-sided bandolier and its buckle (paint), each group on its own mid-plane, the figure's right half kept and
mirrored. Meshy's garments are open sheets: tunic, sleeves, forearms and bracers are closed and fused into one voxel skin, so that no seam or gap opens between them; skirt, pants, boots, cuffs, belt and plates stay separate pieces.
Parts: 1 skin of the upper body, 4 glove, 5 pants, 6 boots, 7 skirt, 9 belt, 11 cuffs, 12 plates. Args: <meshy glb> <mm9 true glb> <out blend> <report json>"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
MESHY, MM9, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
rep = {}
TRIS = {1: int(os.environ.get('T_SKIN', 2300)), 5: 240, 6: 520, 7: 340, 9: 110, 11: 160, 12: 90}      # right half
DX = {1: 0.0160, 4: 0.0160, 12: 0.0160, 5: 0.0020, 7: 0.0020, 9: 0.0080, 11: 0.0, 6: -0.0050}
WRIST = np.array([-0.372, -0.03, -0.125]); WRIST_D = np.array([-0.012, -0.03, -0.14]); WRIST_D /= np.linalg.norm(WRIST_D)
JOINTS = [(-.235, .012, .27), (-.33, .05, .03), (-.372, -.03, -.125), (-.10, .02, -.10), (-.125, .02, -.285), (-.155, .07, -.50)]
V = float(os.environ.get('VOXEL', 0.0045))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mp = np.array([o_.matrix_world @ v.co for o_ in sc.objects if o_.type == 'MESH' and o_.name.startswith('d_') for v in o_.data.vertices])
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
o.name = 'Raw'; o.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
co = np.array([v.co for v in bm.verts])
s = np.ptp(mp[:, 2]) / np.ptp(co[:, 2]); t = np.array([0.0, 0.0, mp[:, 2].min() - co[:, 2].min() * s])
for v in bm.verts: v.co = Vector(np.array(v.co) * s + t)
rep['scale'] = float(s)
bm.verts.ensure_lookup_table()
seen = set(); pieces = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    pieces.append(cur)
def label(q):
    lo, hi = q.min(0), q.max(0); e = hi - lo; cx = abs(q[:, 0].mean())
    if lo[2] > 0.26 and hi[2] > 0.45: return 0                         # head job
    if hi[2] > 0.36 and lo[2] < 0.0 and e[0] > 0.3: return 1            # tunic
    if lo[2] < -0.6: return 6                                           # boot
    if lo[2] > -0.12 and lo[2] < 0.1 and hi[2] > 0.1 and cx > 0.2: return 1     # sleeve, forearm
    if lo[1] < -0.17 and e[0] < 0.1 and lo[2] > 0.05: return 0          # the bandolier's buckle
    if lo[1] < -0.17 and e[0] > 0.12 and e[2] > 0.2: return 0           # the bandolier
    if lo[2] < -0.2 and cx > 0.27 and hi[2] < 0.02: return 4            # hand with bracer
    if lo[2] < -0.38 and hi[2] > -0.1: return 5                         # pants
    if lo[2] < -0.25 and hi[2] > -0.05 and e[0] > 0.3: return 7         # skirt
    if lo[2] < -0.28 and hi[2] < -0.25: return 11                       # boot cuff
    if lo[2] > -0.12 and hi[2] < 0.02 and e[0] > 0.3: return 9          # belt
    if lo[2] > -0.12 and hi[2] < 0.02 and lo[1] < -0.12: return 9       # belt buckle
    if lo[2] > 0.15: return 12                                          # shoulder plates, trims
    return 0
lay = bm.faces.layers.int.new('part')
info = []
dead = []
for cur in pieces:
    q = np.array([v.co for v in cur]); lb = label(q)
    info.append((lb, len(cur), q.min(0).round(3).tolist(), q.max(0).round(3).tolist()))
    if lb == 0: dead.extend(cur); continue
    for f in {f for v in cur for f in v.link_faces}:
        f[lay] = lb
        if lb == 4 and (np.array(f.calc_center_median()) - WRIST * [np.sign(q[:, 0].mean()) * -1, 1, 1]) @ (WRIST_D * [np.sign(q[:, 0].mean()) * -1, 1, 1]) < 0: f[lay] = 1    # the bracer is skin of the arm; only the glove past the wrist is replaced
bmesh.ops.delete(bm, geom=dead, context='VERTS')
for i in sorted(info, key=lambda x: -x[1]): print('PIECE', i)
for v in bm.verts:
    ps = {f[lay] for f in v.link_faces}
    if ps: v.co.x += DX[max(ps)]
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 2e-5: v.co.x = 0
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = o.data; bm.to_mesh(me); bm.free()
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
print('FACES', {int(k): int((fp == k).sum()) for k in np.unique(fp)})
def extract(lb, name):
    x = o.copy(); x.data = me.copy(); x.name = name; sc.collection.objects.link(x)
    b = bmesh.new(); b.from_mesh(x.data); b.faces.ensure_lookup_table()
    l = b.faces.layers.int['part']
    bmesh.ops.delete(b, geom=[f for f in b.faces if f[l] not in lb], context='FACES')
    bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context='VERTS')
    b.to_mesh(x.data); b.free()
    return x
def select(x):
    for y in bpy.data.objects: y.select_set(y is x)
    bpy.context.view_layer.objects.active = x
def right_half(x, keep_joints=True):
    b = bmesh.new(); b.from_mesh(x.data)
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in b.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    b.to_mesh(x.data); b.free()
def decimate(x, tris, protect=()):
    select(x)
    b = bmesh.new(); b.from_mesh(x.data); bmesh.ops.triangulate(b, faces=b.faces); b.to_mesh(x.data); b.free()
    while len(x.data.polygons) > 60000:
        st = x.modifiers.new('St', 'DECIMATE'); st.ratio = 0.3; st.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='St')
    g = x.vertex_groups.new(name='keep')
    for v in x.data.vertices:
        d = min((np.linalg.norm(np.array(v.co) - np.array(j)) for j in protect), default=1.0)
        w = float(np.clip(1 - (d - 0.05) / 0.07, 0, 1)) * 0.8
        g.add([v.index], 1.0 if abs(v.co.x) < 1e-5 else w, 'REPLACE')
    d = x.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, tris / max(len(x.data.polygons), 1)); d.use_collapse_triangulate = True
    d.vertex_group = 'keep'; d.invert_vertex_group = True; d.vertex_group_factor = 3.0
    bpy.ops.object.modifier_apply(modifier='D'); x.vertex_groups.clear()
def mirror(x):
    b = bmesh.new(); b.from_mesh(x.data)
    for v in b.verts:
        if abs(v.co.x) < 3e-4: v.co.x = 0
    bmesh.ops.mirror(b, geom=b.verts[:] + b.edges[:] + b.faces[:], axis='X', merge_dist=3e-4)
    bmesh.ops.triangulate(b, faces=[f for f in b.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    b.to_mesh(x.data); b.free()
def setpart(x, lb):
    if 'part' not in x.data.attributes: x.data.attributes.new('part', 'INT', 'FACE')
    x.data.attributes['part'].data.foreach_set('value', [lb] * len(x.data.polygons))
# --- the upper body: every shell closed, then one voxel skin
s_ = extract((1,), 'Skin')
b = bmesh.new(); b.from_mesh(s_.data)
bmesh.ops.holes_fill(b, edges=[e for e in b.edges if e.is_boundary], sides=0)
bmesh.ops.triangulate(b, faces=[f for f in b.faces if len(f.verts) > 3])
print('SKIN boundary left', sum(1 for e in b.edges if e.is_boundary), 'faces', len(b.faces))
bmesh.ops.recalc_face_normals(b, faces=b.faces)
b.to_mesh(s_.data); b.free()
select(s_)
rm = s_.modifiers.new('R', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = V; rm.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='R')
b = bmesh.new(); b.from_mesh(s_.data); b.verts.ensure_lookup_table()
seen = set(); comps = []
for v in b.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    comps.append(cur)
comps.sort(key=len, reverse=True)
print('SKIN voxel comps', [len(c) for c in comps[:8]])
for c in comps[1:]: bmesh.ops.delete(b, geom=c, context='VERTS')
b.to_mesh(s_.data); b.free()
sm = s_.modifiers.new('S', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 3
bpy.ops.object.modifier_apply(modifier='S')
right_half(s_); decimate(s_, TRIS[1], JOINTS); mirror(s_); setpart(s_, 1)
objs = [s_]
for lb, nm in ((5, 'Pants'), (6, 'Boots'), (7, 'SkirtP'), (9, 'Belt'), (11, 'Cuffs'), (12, 'Plates')):
    x = extract((lb,), nm)
    right_half(x); n0 = len(x.data.polygons)
    decimate(x, TRIS[lb], JOINTS if lb in (5, 6) else ()); mirror(x); setpart(x, lb)
    rep.setdefault('reduce', {})[nm] = [n0, len(x.data.polygons)]
    if lb in (7, 9, 11, 12):                                         # Meshy's sawtooth rims, relaxed along the rim
        b = bmesh.new(); b.from_mesh(x.data)
        for _ in range(3):
            mv = {}
            for v in b.verts:
                nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb) == 2 and abs(v.co.x) > 1e-4: mv[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
            for v, c in mv.items(): v.co = c
        b.to_mesh(x.data); b.free()
    objs.append(x)
x = extract((4,), 'Glove'); setpart(x, 4); objs.append(x)                         # replaced by the grafted hands; here only for the frame
bpy.data.objects.remove(o)
select(objs[0])
for x in objs: x.select_set(True)
bpy.ops.object.join()
o = objs[0]; o.name = 'Body'; o.data.name = 'Body'; me = o.data
for p in me.polygons: p.use_smooth = True
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
rep['parts'] = {int(k): int((fp == k).sum()) for k in np.unique(fp)}
b = bmesh.new(); b.from_mesh(me)
rep['boundary'] = sum(1 for e in b.edges if e.is_boundary); rep['over2'] = sum(1 for e in b.edges if len(e.link_faces) > 2)
b.free()
rep['tris'] = len(me.polygons); rep['verts'] = len(me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=0)
print('CLEAN', json.dumps(rep)[:900])
