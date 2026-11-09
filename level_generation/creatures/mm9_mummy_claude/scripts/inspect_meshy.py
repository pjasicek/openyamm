"""Clay views + component stats of a Meshy GLB. Args: glb outdir"""
import bpy, sys, os, bmesh
import numpy as np
from mathutils import Vector
glb, out = sys.argv[sys.argv.index('--') + 1:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
ob = [o for o in sc.objects if o.type == 'MESH']
print('OBJ', [(o.name, len(o.data.vertices), len(o.data.polygons)) for o in ob])
o = ob[0]
P = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
print('BOUNDS', P.min(0), P.max(0))
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
print('COMPS', len(comps), [len(c) for c in comps[:20]])
for c in comps[:12]:
    q = P[c]; print(len(c), q.min(0).round(3), q.max(0).round(3))
nm = sum(1 for e in bm.edges if not e.is_manifold); print('NONMANIFOLD', nm); bm.free()
for m in bpy.data.materials: m.use_nodes = False
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'MATCAP'; sh.color_type = 'SINGLE'; sh.single_color = (0.7, 0.68, 0.62)
try: sh.studio_light = 'clay_brown.exr'
except Exception: pass
sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 1000
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.3); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_end = 100
mn, mx = P.min(0), P.max(0); c = Vector(((mn + mx) / 2).tolist()); H = mx[2] - mn[2]
views = {'front': (Vector((0, -1, 0)), c, H * 1.15), 'q': (Vector((-1, -1.2, .4)), c, H * 1.2), 'side': (Vector((1, 0, 0)), c, H * 1.15), 'back': (Vector((0, 1, 0)), c, H * 1.15),
         'head': (Vector((-.5, -1, .1)), Vector((c.x, c.y, mn[2] + H * .9)), H * .25), 'headb': (Vector((.5, 1, .1)), Vector((c.x, c.y, mn[2] + H * .9)), H * .25)}
for n, (d, t, s) in views.items():
    cd.ortho_scale = s; cam.location = t + d.normalized() * 10
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}/{n}.png'; bpy.ops.render.render(write_still=True)
