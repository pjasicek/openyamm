"""Per-face region labels of the source body (work/source.blend), dump order (loop triangles):
0 rest (tunic, arms, legs, mantle), 1 head component A, 2 head component B (the two head-set pieces), 3 left hand,
4 right hand, 5 cloak (Cloak_* chain bones dominant), 6 small separate pieces (<= 150 faces).
-> work/regions.npy, work/comp.npy (connected component per face); prints counts. Also renders a coloured
rest-pose front/back/side sheet to review/regions.png."""
import os, bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
assert len(me.loop_triangles) == len(me.polygons)
names = {g.index: g.name for g in o.vertex_groups}
def lab(n):
    if n.startswith('LeftHand'): return 3
    if n.startswith('RightHand'): return 4
    if n.startswith('Cloak_'): return 5
    return 0
vl = np.zeros((len(me.vertices), 6))
for v in me.vertices:
    for g in v.groups: vl[v.index, lab(names[g.group])] += g.weight
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.faces), int); c = 0
for f in bm.faces:
    if comp[f.index] >= 0: continue
    st = [f]; comp[f.index] = c
    while st:
        x = st.pop()
        for e in x.edges:
            for y in e.link_faces:
                if comp[y.index] < 0: comp[y.index] = c; st.append(y)
    c += 1
uv = me.uv_layers.active.data
fu = np.array([np.mean([uv[l].uv[0] for l in p.loop_indices]) for p in me.polygons])
headc = sorted({int(k) for k in np.unique(comp) if fu[comp == k].mean() > .5}, key=lambda k: -(comp == k).sum())
fl = np.array([np.argmax(sum(vl[i] for i in p.vertices)) for p in me.polygons])
sizes = np.bincount(comp)
fl[sizes[comp] <= 150] = 6
for i, k in enumerate(headc):
    fl[comp == k] = 1 + i
np.save(os.path.join(HERE, 'work', 'regions.npy'), fl); np.save(os.path.join(HERE, 'work', 'comp.npy'), comp)
print('REGIONS', {k: int((fl == k).sum()) for k in range(7)}, 'head comps', headc)
# coloured render
cols = [(.6, .6, .6, 1), (1, .8, .6, 1), (.5, .3, .1, 1), (.2, .4, 1, 1), (1, .2, .2, 1), (.2, .8, .3, 1), (1, 1, 0, 1)]
attr = me.color_attributes.new('reg', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    for l in p.loop_indices: attr.data[l].color = cols[fl[p.index]]
for m in o.modifiers: m.show_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'VERTEX'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x, sc.render.resolution_y = 500, 700
for a in [x for x in bpy.data.objects if x.type == 'ARMATURE']: a.animation_data_clear() if a.animation_data else None
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.75
import math
Image = None
imgs = []
for name, yaw in (('front', 0), ('back', math.pi), ('side', math.pi / 2)):
    d = 4; cam.location = (d * math.sin(yaw) * 0, 0, 0)
    cam.location = (-d * math.sin(yaw), -d * math.cos(yaw), .8); cam.rotation_euler = (math.pi / 2, 0, -yaw)
    sc.render.filepath = os.path.join(HERE, 'work', f'reg_{name}.png'); bpy.ops.render.render(write_still=True)



