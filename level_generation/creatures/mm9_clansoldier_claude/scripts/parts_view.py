"""Meshy parts in false colours + sections through the middle (x=0 plane cut, y=0 plane cut). Args: <glb> <out prefix>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
col = bm.loops.layers.color.new('c')
seen = set(); parts = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); ids = []
    while st:
        x = st.pop(); ids.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    parts.append(ids)
parts.sort(key=len, reverse=True)
rng = np.random.RandomState(3)
pal = [(1, .2, .2), (.2, .9, .2), (.2, .4, 1), (1, 1, .2), (1, .2, 1), (.2, 1, 1), (1, .6, .2), (.6, .3, 1), (.5, 1, .5), (1, .6, .7)] + [tuple(rng.rand(3)) for _ in range(20)]
for k, ids in enumerate(parts):
    c = pal[k]
    for v in ids:
        for l in v.link_loops: l[col] = (*c, 1)
bm.to_mesh(o.data); bm.free()
for p in o.data.polygons: p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False
sc.render.resolution_x = 700; sc.render.resolution_y = 800
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.2, 0.22)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.ortho_scale = 1.1
for n, d in (('front', (0, -1, 0)), ('back', (0, 1, 0)), ('left', (1, 0, 0))):
    d = Vector(d).normalized(); cam.location = d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
# sections: boolean by clip planes through camera
sc.display.shading.show_backface_culling = False
cd.ortho_scale = 0.75
for n, d, clip, cen in (('secx', (1, 0, 0), 0.0, (0, 0, -0.05)), ('secx2', (1, 0, 0), 0.09, (0.09, 0, -0.05)), ('secy', (0, -1, 0), 0.0, (0, 0, -0.05))):
    d = Vector(d).normalized(); cam.location = Vector(cen) + d * (2 - 0.0)
    cd.clip_start = 2.0 - 0.0; cd.clip_end = 5
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
