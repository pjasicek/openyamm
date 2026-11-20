"""Meshy return: objects, triangles, bounds, connected components; solid renders (front, left, q34, top).
Args: glb outdir prefix"""
import bpy, bmesh, sys, os, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix = argv
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
rep = {}
pts = []
for o in sc.objects:
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        st = [v]; seen.add(v.index); c = []
        while st:
            x = st.pop(); c.append(x.co.copy())
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
        comps.append(c)
    comps.sort(key=len, reverse=True)
    pts += [v.co.copy() for v in bm.verts]
    rep[o.name] = {'verts': len(bm.verts), 'tris': sum(len(f.verts) - 2 for f in bm.faces),
                   'components': [(len(c), [round(min(p[i] for p in c), 3) for i in range(3)],
                                   [round(max(p[i] for p in c), 3) for i in range(3)]) for c in comps[:12]],
                   'n_components': len(comps)}
mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
rep['bounds'] = [mn, mx]
print('MESHY ' + json.dumps(rep))
c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)]); size = max(mx[i] - mn[i] for i in range(3)) * 1.1
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 512
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = size; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'front': (0, -1, 0), 'left': (1, 0, 0), 'q34': (-1, -1.25, 0.55), 'top': (0, 0.0001, 1)}.items():
    d = Vector(d).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
