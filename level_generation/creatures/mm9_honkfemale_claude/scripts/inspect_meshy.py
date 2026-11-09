"""Parts of a Meshy GLB and clay views. Args: <glb> <out prefix>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
ms = [o for o in bpy.data.objects if o.type == 'MESH']
print('INSPECT meshes', len(ms))
for o in ms:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    M = o.matrix_world
    co = np.array([tuple(M @ v.co) for v in bm.verts])
    comp = -np.ones(len(bm.verts), int); cid = 0
    for v in bm.verts:
        if comp[v.index] >= 0: continue
        st = [v]; comp[v.index] = cid
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
        cid += 1
    print('INSPECT', o.name, 'verts', len(bm.verts), 'tris', sum(len(f.verts) - 2 for f in bm.faces), 'parts', cid, 'bbox', co.min(0).round(3).tolist(), co.max(0).round(3).tolist(),
          'boundary edges', sum(1 for e in bm.edges if e.is_boundary))
    for k in sorted(range(cid), key=lambda k: -(comp == k).sum())[:40]:
        m = comp == k
        print('  part', k, int(m.sum()), co[m].min(0).round(3).tolist(), co[m].max(0).round(3).tolist())
    bm.free()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .75, .75); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
pts = np.concatenate([[tuple(o.matrix_world @ v.co) for v in o.data.vertices] for o in ms])
c = Vector(((pts.min(0) + pts.max(0)) / 2).tolist()); ext = float(np.ptp(pts, 0).max())
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ext * 1.05; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'front': (0, -1, 0), 'q34': (-1, -1.2, .4), 'side': (1, 0, 0), 'back': (0, 1, 0), 'below': (0, -.3, -1)}.items():
    d = Vector(d).normalized(); cam.location = c + d * ext * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
