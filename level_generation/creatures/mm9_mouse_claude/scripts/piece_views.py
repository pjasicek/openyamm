"""Render a GLB/blend mesh with every connected component in its own colour, zoomed on a box.
Args: <glb> <out png prefix> <cx,cy,cz> <ortho> [views]"""
import bpy, bmesh, sys, os, colorsys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, out, c, ortho = argv[0], argv[1], Vector([float(x) for x in argv[2].split(',')]), float(argv[3])
views = argv[4].split(',') if len(argv) > 4 else ['front', 'left', 'q34', 'bottom']
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    lay = bm.loops.layers.color.new('comp')
    seen = set(); k = 0
    for f in bm.faces:
        if f.index in seen:
            continue
        st = [f]; seen.add(f.index); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen:
                        seen.add(y.index); st.append(y)
        col = colorsys.hsv_to_rgb((k * 0.618) % 1, 0.7 if k else 0.0, 0.9)
        for x in comp:
            for l in x.loops:
                l[lay] = (*col, 1)
        k += 1
    bm.to_mesh(o.data)
    print('COMPONENTS', o.name, k)
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 512
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'right': (-1, 0, 0.05), 'q34': (-1, -1.25, 0.55),
     'top': (0, 0.0001, 1), 'bottom': (0, 0.0001, -1), 'back': (0, 1, 0.05)}
for v in views:
    d = Vector(D[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'
    bpy.ops.render.render(write_still=True)
