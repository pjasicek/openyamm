"""Report and render a Meshy return: parts, bounds. Args: glb outdir prefix"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix = argv[:3]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
ms = [o for o in sc.objects if o.type == 'MESH']
print('OBJ', [(o.name, len(o.data.vertices), len(o.data.polygons)) for o in ms])
for o in sc.objects:
    print(o.name, o.type, o.location[:], o.rotation_euler[:], o.scale[:])
pts = []
tot = 0
for o in ms:
    co = np.array([o.matrix_world @ v.co for v in o.data.vertices]); pts.append(co)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen = np.zeros(len(bm.verts), bool); comps = []
    for v in bm.verts:
        if seen[v.index]:
            continue
        st = [v]; seen[v.index] = True; idx = []
        while st:
            x = st.pop(); idx.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if not seen[y.index]:
                    seen[y.index] = True; st.append(y)
        comps.append(idx)
    comps.sort(key=len, reverse=True)
    print('PARTS', len(comps), [len(c) for c in comps[:30]])
    for c in comps[:12]:
        q = co[c]; print('  ', len(c), np.round(q.min(0), 3), np.round(q.max(0), 3))
    be = [e for e in bm.edges if e.is_boundary]
    print('BOUNDARY edges', len(be), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2))
pts = np.concatenate(pts)
c = Vector((pts.min(0) + pts.max(0)) / 2); size = float((pts.max(0) - pts.min(0)).max())
print('BOUNDS', pts.min(0), pts.max(0))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_backface_culling = False
sh.show_cavity = True; sh.cavity_type = 'WORLD'
sc.render.resolution_x = 800; sc.render.resolution_y = 1100
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = size * 1.45; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'q34': (-1, -1.25, .35), 'front': (0, -1, .02), 'left': (1, 0, .02), 'back': (0, 1, .02), 'right': (-1, 0, .02)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{n}.png'); bpy.ops.render.render(write_still=True)
