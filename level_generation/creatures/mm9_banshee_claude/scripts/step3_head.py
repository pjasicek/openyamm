"""The head: Meshy's head-only model (references_head2) cleaned and placed on MM9's head. Parts: shell, two eyeballs, tongue, about 28 separate teeth. The shell is mirror-symmetric (x > 0 kept), the hair cap is drawn in towards MM9's narrower skull
(cap ridge at the hairline and the shelf at the nape smoothed: the spikes cover it), the neck cut on a slanted plane behind the jaw and lofted to the torso's neck ring. Reduced, scaled, placed.
Writes object Head with attribute hpart (0 shell, 1 eyes, 2 tongue, 3 upper teeth, 4 lower teeth, 5 neck). Args: <glb> <upper blend> <out blend>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
GLB, UPPER, OUT = sys.argv[sys.argv.index('--') + 1:]
S, T = 0.358, np.array([0, -0.244, 0.581])
TRIS_SHELL = 2800


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


bpy.ops.wm.open_mainfile(filepath=UPPER)
up = bpy.data.objects['Upper']
old = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
new = [o for o in bpy.data.objects if o not in old]
h = next(o for o in new if o.type == 'MESH')
m = h.matrix_world.copy(); h.parent = None; h.matrix_world = m
for o in new:
    if o is not h:
        bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.select_set(o == h)
bpy.context.view_layer.objects.active = h
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = h.data
for u in list(me.uv_layers):
    me.uv_layers.remove(u)
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int.new('hpart'); bm.verts.ensure_lookup_table()
seen = {}; parts = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = 1; cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = 1; st.append(y)
    parts.append(cur)
parts.sort(key=len, reverse=True)
print('PARTS', [len(p) for p in parts])
shell = parts[0]
pieces = {}
eyes = []; tongue = None; up_t = []; lo_t = []
for p in parts[1:]:
    c = np.mean([v.co[:] for v in p], axis=0)
    if len(p) > 500:
        eyes.append(p)
    elif len(p) > 200:
        tongue = p
    elif c[2] > -0.19:
        up_t.append(p)
    else:
        lo_t.append(p)
print('EYES', len(eyes), 'upper teeth', len(up_t), 'lower teeth', len(lo_t))
# eyes: keep the +x eye and mirror it; drop the -x one
for p in eyes:
    if np.mean([v.co.x for v in p]) < 0:
        bmesh.ops.delete(bm, geom=p, context='VERTS')
sv = [v for v in shell]
# ---------- shell deformation in Meshy units
sets = dict(shell=set(sv))
co = np.array([v.co[:] for v in sv])
y, z = co[:, 1], co[:, 2]
# cap = above the brow, behind the face
cap = ss(0.02, 0.2, z + 0.55 * (y + 0.1)) * ss(-0.32, -0.12, y + 0.4 * (0.2 - z))
fx = 1 - 0.2 * cap
fy = 1 - 0.13 * cap * (y > 0)
for v, c, a, b in zip(sv, co, fx, fy):
    v.co = Vector((c[0] * a, c[1] * b, c[2] * (1 - 0.05 * max(0.0, c[2]) * 2)))
# smooth the cap and the nape (hairline ridge, shelf at the back)
mask = [v for v, c in zip(sv, cap) if c > 0.25]
nape = [v for v in sv if v.co.y > 0.05 and -0.3 < v.co.z < 0.2]
for _ in range(14):
    bmesh.ops.smooth_vert(bm, verts=list(set(mask) | set(nape)), factor=0.6, use_axis_x=True, use_axis_y=True, use_axis_z=True)
# neck cut: slanted plane behind the jaw
# world plane through the throat (y -0.25, z 0.474) and the nape (y -0.154, z 0.563)
P_w = np.array([0, -0.2, 0.52]); N_w = np.array([0, 0.68, -0.73])
cut_co, cut_no = Vector(((P_w - T) / S).tolist()), Vector(N_w.tolist())
geom = [v for v in sv if v.is_valid and v.co.y > -0.08]
gm = list({f for v in geom for f in v.link_faces}) + list({e for v in geom for e in v.link_edges}) + geom
r = bmesh.ops.bisect_plane(bm, geom=gm, plane_co=cut_co, plane_no=cut_no, clear_outer=True, clear_inner=False, dist=1e-5)
bm.verts.ensure_lookup_table()
# mirror the shell's +x half
shell_now = None
seen = {}; comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = 1; cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y_ = e.other_vert(x)
            if y_.index not in seen:
                seen[y_.index] = 1; st.append(y_)
    comps.append(cur)
comps.sort(key=len, reverse=True)
sh = comps[0]
print('COMPS', [len(c) for c in comps[:5]])
# tag parts by a layer before mirror
for c in comps[1:]:
    pc = np.mean([v.co[:] for v in c], axis=0)
    tag = 1 if len(c) > 500 else (2 if len(c) > 200 else (3 if pc[2] > -0.19 else 4))
    for v in c:
        v[lay] = tag
gm = list({f for v in sh for f in v.link_faces}) + list({e for v in sh for e in v.link_edges}) + sh
bmesh.ops.bisect_plane(bm, geom=gm, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=False, clear_inner=True, dist=1e-5)
bm.verts.ensure_lookup_table()
keep_mirror = [v for v in bm.verts if v[lay] == 0 or v[lay] == 1]
for v in keep_mirror:
    if abs(v.co.x) < 1e-3 and v[lay] == 0:
        v.co.x = 0
gm = list({f for v in keep_mirror for f in v.link_faces}) + list({e for v in keep_mirror for e in v.link_edges}) + keep_mirror
bmesh.ops.mirror(bm, geom=gm, matrix=Matrix.Identity(4), merge_dist=2e-4, axis='X')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for v in bm.verts:
    v.co = Vector((np.array(v.co[:]) * S + T).tolist())
print('HEAD', len(bm.verts), len(bm.faces), 'boundary', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(me); bm.free()
me.update()
h.name = 'HeadRaw'; me.name = 'HeadRaw'
# reduce each part on its own: faces per part
def split_decimate():
    idx = np.zeros(len(me.vertices), np.int32); me.attributes['hpart'].data.foreach_get('value', idx)
    out = {}
    for tag, ratio in ((0, None), (1, 0.08), (2, 0.25), (3, 0.26), (4, 0.26)):
        o = h.copy(); o.data = me.copy(); bpy.context.scene.collection.objects.link(o)
        bm = bmesh.new(); bm.from_mesh(o.data)
        lay = bm.verts.layers.int.get('hpart')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != tag], context='VERTS')
        bm.to_mesh(o.data); bm.free(); o.data.update()
        n = len(o.data.polygons)
        r = TRIS_SHELL / n if tag == 0 else ratio
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.context.view_layer.objects.active = o
        mod = o.modifiers.new('d', 'DECIMATE'); mod.ratio = min(r, 1.0); mod.use_symmetry = tag in (0, 1); mod.symmetry_axis = 'X'
        bpy.ops.object.modifier_apply(modifier='d')
        print('PART', tag, n, '->', len(o.data.polygons))
        out[tag] = o
    return out


parts_o = split_decimate()
bpy.data.objects.remove(h)
for x in bpy.data.objects:
    x.select_set(x in parts_o.values())
bpy.context.view_layer.objects.active = parts_o[0]
bpy.ops.object.join()
head = parts_o[0]; head.name = 'Head'; head.data.name = 'Head'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SAVED', len(head.data.polygons))
