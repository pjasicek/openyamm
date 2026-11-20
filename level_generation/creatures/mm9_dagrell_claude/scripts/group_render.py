"""Render the aligned Meshy pieces coloured by their nearest-MM9-bone group (posed Stand space), plus the biggest
pieces in their own colours. Args: <align blend> <outdir>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
act = bpy.data.actions['Stand']; arm.animation_data_create(); arm.animation_data.action = act
try:
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(0); bpy.context.view_layer.update()
ob = bpy.data.objects['Meshy']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = np.full(len(bm.verts), -1); comps = []
for v in bm.verts:
    if seen[v.index] >= 0: continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0: seen[y.index] = len(comps); st.append(y)
    comps.append(c)
order = sorted(range(len(comps)), key=lambda k: -len(comps[k]))
pal = [(1, .2, .2), (.2, 1, .2), (.2, .4, 1), (1, 1, .2), (1, .2, 1), (.2, 1, 1), (1, .6, .1), (.6, .3, 1)]
col = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'POINT')
for r, k in enumerate(order):
    c = pal[r] if r < len(pal) else (.75, .75, .75)
    for i in comps[k]:
        col.data[i].color = (*c, 1)
    if r < 8:
        P = np.array([tuple(me.vertices[i].co) for i in comps[k]])
        print('BIG', r, len(comps[k]), pal[r], [round(x, 2) for x in P.min(0)], [round(x, 2) for x in P.max(0)])
me.color_attributes.active_color = col
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not ob:
        o.hide_render = True
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 640
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 2.8; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 0.75))
os.makedirs(argv[1], exist_ok=True)
for v, dv in {'right': (-1, 0, 0), 'front': (0, -1, 0), 'top': (0, 0.0001, 1)}.items():
    dv = Vector(dv).normalized(); cam.location = c + dv * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'g_{v}.png'); bpy.ops.render.render(write_still=True)
