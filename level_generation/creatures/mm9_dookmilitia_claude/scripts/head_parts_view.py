"""Clay views of chosen loose parts of the head job. Args: <glb> <out prefix> <part list comma>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
keep = [int(x) for x in a[2].split(',')]
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
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
dl = [v for i, p in enumerate(parts) if i not in keep for v in p]
bmesh.ops.delete(bm, geom=dl, context='VERTS'); bm.to_mesh(o.data); bm.free()
for p in o.data.polygons: p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True
sc.render.resolution_x = 600; sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 1.1; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in (('front', (0, -1, 0)), ('right', (-1, 0, 0)), ('back', (0, 1, 0))):
    d = Vector(d).normalized(); cam.location = d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
