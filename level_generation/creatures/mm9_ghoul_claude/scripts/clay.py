"""Clay views of a mesh GLB/blend object for diagnosis. Args: <glb> <outdir> <prefix> [size]. VIEWS env: name=cx,cy,cz,dx,dy,dz,ortho;..."""
import bpy, sys, os, bmesh
from mathutils import Vector
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, pre = argv[:3]; size = int(argv[3]) if len(argv) > 3 else 900
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
ms = [o for o in sc.objects if o.type == 'MESH']
P = []; 
for o in ms:
    M = o.matrix_world
    P += [tuple(M @ v.co) for v in o.data.vertices]
    bm = bmesh.new(); bm.from_mesh(o.data)
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen.add(v.index); cf = 0; cv = []
        while st:
            x = st.pop(); cv.append(x.co.copy())
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        comps.append(cv)
    comps.sort(key=len, reverse=True)
    print('MESH', o.name, 'verts', len(bm.verts), 'tris', sum(len(f.verts) - 2 for f in bm.faces), 'open edges', sum(1 for e in bm.edges if len(e.link_faces) == 1), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2), 'comps', len(comps), [len(c) for c in comps[:12]])
    bm.free()
P = np.array(P); print('BBOX', P.min(0), P.max(0))
mat = bpy.data.materials.new('clay'); mat.use_nodes = True
for o in ms:
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = False if os.environ.get('FLAT') else True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'MATCAP' if False else 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_cavity = True; sh.show_shadows = False; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.32); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = (P.min(0) + P.max(0)) / 2; ext = float((P.max(0) - P.min(0)).max()) * 1.08
views = {'front': (c, (0, -1, 0.05), ext), 'back': (c, (0, 1, 0.05), ext), 'left': (c, (1, 0, 0.05), ext), 'right': (c, (-1, 0, 0.05), ext), 'q34': (c, (-1, -1.2, 0.4), ext)}
for s in os.environ.get('VIEWS', '').split(';'):
    if s:
        n, v = s.split('='); f = [float(x) for x in v.split(',')]
        views[n] = (Vector(f[:3]), f[3:6], f[6])
for n, (ce, d, e) in views.items():
    d = Vector(d).normalized(); ce = Vector(tuple(ce))
    cd.ortho_scale = e; cam.location = ce + d * 10
    cam.rotation_euler = (ce - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}/{pre}_{n}.png'; bpy.ops.render.render(write_still=True)
