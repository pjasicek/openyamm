"""Split the m234 Smart Topology return (work/st_v1_parts.blend, normalised to 2.0 m overall incl. the raised wing tips,
facing -Y) into body / wings / tail. P00 is one shell holding the body, both wing arms with their struts, and the tail;
P01/P02 are the two membrane sheets, P06 the tail's spade tip, P03/P04 the eyes and P05, P07..P22 the teeth;
P09, P23..P29 are stray slivers (< 60 triangles, beside the left wing root and the right wing tip) and are deleted.
- WINGS (on P00): grown from each wing tip through candidates: behind the back surface (y > back(z) + BACK_GAP) above
  WING_Z0, or laterally beyond ARM_X above WING_Z1 (the hands stop inside ARM_X). P01/P02 join the wings.
- TAIL: Dijkstra geodesic distance on P00 from the vertices nearest the spade (P06); bands of BAND m; the tail is every
  band from the tip until the band's spread (max distance from its centroid) exceeds TAIL_SPREAD (the band has
  reached the buttocks). P06 joins the tail.
Writes 'part' (0 body, 1 left wing, 2 right wing, 3 tail) and 'piece' point attributes, the objects 'Body' (body pieces),
'Wings' (both wings) and 'Tail', each with 'orig_co'; the split edges are duplicated (wings_join.py merges them back).
Renders review/split_<view>.png. Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, heapq
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
BACK_GAP, WING_Z0, ARM_X, WING_Z1 = E('BACK_GAP', 0.03), E('WING_Z0', 1.2), E('ARM_X', 0.66), E('WING_Z1', 0.95)
BAND, TAIL_SPREAD = E('BAND', 0.02), E('TAIL_SPREAD', 0.075)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
DROP = {9, 23, 24, 25, 26, 27, 28, 29}
P = {int(o.name[1:]): o for o in bpy.data.objects if o.type == 'MESH'}
for k in [k for k in P if k in DROP]:
    bpy.data.objects.remove(P.pop(k), do_unlink=True)
for k, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [k] * len(o.data.vertices))
    o.data.materials.clear()
main = P[0]; me = main.data
co = np.array([tuple(main.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
adj = [[] for _ in range(nv)]
for e in me.edges:
    a, b = e.vertices; L = float(np.linalg.norm(co[a] - co[b]))
    adj[a].append((b, L)); adj[b].append((a, L))
# back surface: per height the largest y of the torso centre column (|x| < 0.06)
zs = np.arange(0.9, 1.75, 0.025); back = []
for z in zs:
    s = co[(np.abs(co[:, 2] - z) < 0.0125) & (np.abs(co[:, 0]) < 0.06)]
    back.append(s[:, 1].max() if len(s) else 0.0)
back_y = np.interp(co[:, 2], zs, np.array(back))
cand = ((co[:, 1] > back_y + BACK_GAP) & (co[:, 2] > WING_Z0)) | ((np.abs(co[:, 0]) > ARM_X) & (co[:, 2] > WING_Z1))
part = np.zeros(nv, np.int32)
for side, sg in ((1, 1.0), (2, -1.0)):
    seed = int(np.argmax(co[:, 0] * sg))
    st = [seed]; part[seed] = side
    while st:
        a = st.pop()
        for b, _ in adj[a]:
            if cand[b] and part[b] == 0 and co[b, 0] * sg > -0.02:
                part[b] = side; st.append(b)
# tail by geodesic bands from the spade
sp = np.array([tuple(P[6].matrix_world @ v.co) for v in P[6].data.vertices]).mean(0)
d = np.full(nv, np.inf); seeds = np.argsort(np.linalg.norm(co - sp, axis=1))[:6]
h = []
for s_ in seeds:
    d[s_] = 0.0; heapq.heappush(h, (0.0, int(s_)))
while h:
    dd, a = heapq.heappop(h)
    if dd > d[a] or dd > 2.5:
        continue
    for b, L in adj[a]:
        if dd + L < d[b]:
            d[b] = dd + L; heapq.heappush(h, (dd + L, b))
tail_len = 0.0
for k in range(0, 200):
    m = (d >= k * BAND) & (d < (k + 1) * BAND) & (part == 0)
    if m.sum() < 3:
        continue
    c = co[m].mean(0); spread = float(np.linalg.norm(co[m] - c, axis=1).max())
    if spread > TAIL_SPREAD:
        tail_len = k * BAND; break
part[(d < tail_len) & (part == 0)] = 3
me.attributes.new('part', 'INT', 'POINT').data.foreach_set('value', part.tolist())
print('SPLIT P00 verts', nv, 'left wing', int((part == 1).sum()), 'right wing', int((part == 2).sum()),
      'tail', int((part == 3).sum()), 'tail length m', round(tail_len, 3))
for k, o in P.items():
    if k == 0:
        continue
    pc = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    val = (1 if pc[:, 0].mean() > 0 else 2) if k in (1, 2) else (3 if k == 6 else 0)
    o.data.attributes.new('part', 'INT', 'POINT').data.foreach_set('value', [val] * len(o.data.vertices))
# join everything, then separate by part (faces whose vertices are all of one part; mixed faces stay with the body)
for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = main
bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
oc = np.array([tuple(v.co) for v in ob.data.vertices])
ob.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', oc.ravel())
pa = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['part'].data.foreach_get('value', pa)
names = {0: 'Body', 1: 'Wings', 3: 'Tail'}
groups = {0: [], 1: [], 3: []}
for f in ob.data.polygons:
    vals = {int(pa[v]) for v in f.vertices}
    g = 0 if vals & {0} else (1 if vals <= {1, 2} else 3 if vals == {3} else 0)
    groups[g].append(f.index)
for g in (1, 3):
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for i in groups[g]:
        ob.data.polygons[i].select = True
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    new = [o for o in bpy.context.selected_objects if o is not ob][-1]
    new.name = new.data.name = names[g]
    # re-index the remaining body faces for the next separation
    pa = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['part'].data.foreach_get('value', pa)
    groups = {0: [], 1: [], 3: []}
    for f in ob.data.polygons:
        vals = {int(pa[v]) for v in f.vertices}
        gg = 0 if vals & {0} else (1 if vals <= {1, 2} else 3 if vals == {3} else 0)
        groups[gg].append(f.index)
    for o in bpy.data.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
ob.name = ob.data.name = 'Body'
for o in bpy.data.objects:
    if o.type == 'MESH':
        bm = bmesh.new(); bm.from_mesh(o.data)
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS'); bm.to_mesh(o.data); bm.free()
        print('SPLIT', o.name, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), 'verts', len(o.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
# review renders: body grey, wings green, tail orange
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'OBJECT'
for o, c in ((bpy.data.objects['Body'], (0.7, 0.7, 0.7, 1)), (bpy.data.objects['Wings'], (0.2, 0.8, 0.2, 1)),
             (bpy.data.objects['Tail'], (1.0, 0.5, 0.1, 1))):
    o.color = c
sc.render.resolution_x, sc.render.resolution_y = 900, 700
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.0
for name, dv in (('front', (0, 1, 0)), ('back', (0, -1, 0)), ('side', (-1, 0, 0)), ('top', (0, 0.01, -1))):
    dv = Vector(dv).normalized(); cam.location = Vector((0, 0, 1.0)) - dv * 6
    cam.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', f'split_{name}.png'); bpy.ops.render.render(write_still=True)
