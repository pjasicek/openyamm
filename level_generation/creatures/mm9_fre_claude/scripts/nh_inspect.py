"""Pass 7: inspect a Meshy head GLB in Blender: connected pieces (vertices, faces, bbox in Blender axes) and clay views (workbench,
front/left/right/back/3-4/below). Args: <glb> <out prefix>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
obs = [x for x in bpy.data.objects if x.type == 'MESH']
for o in obs:
    bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in obs:
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    P = np.array([v.co[:] for v in me.vertices]); n = len(P); par = np.arange(n)
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1]); par[a] = b
    r = np.array([f(i) for i in range(n)]); u, cnt = np.unique(r, return_counts=True)
    print('OBJ', o.name, 'verts', n, 'faces', len(me.polygons), 'bbox', P.min(0).round(4), P.max(0).round(4))
    for k in np.argsort(-cnt)[:12]:
        q = P[r == u[k]]; print('  PIECE', cnt[k], q.min(0).round(4), q.max(0).round(4), q.mean(0).round(4))
    bm = bmesh.new(); bm.from_mesh(me)
    print('  boundary edges', sum(1 for e in bm.edges if e.is_boundary), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2))
    bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.clear()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True
sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .7); sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (.3, .3, .33)
P = np.vstack([np.array([v.co[:] for v in o.data.vertices]) for o in obs]); ce = Vector(((P.min(0) + P.max(0)) / 2).tolist()); ext = float((P.max(0) - P.min(0)).max())
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = ext * 1.1; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, d in {'front': (0, -1, 0), 'back': (0, 1, 0), 'pX': (1, 0, 0), 'nX': (-1, 0, 0), 'q34': (-1, -1.2, 0.3), 'below': (0, -0.6, -1)}.items():
    d = Vector(d).normalized(); cam.location = ce + d * 10 * ext; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); cd.clip_end = 100 * ext
    sc.render.filepath = f'{OUT}_{nm}.png'; bpy.ops.render.render(write_still=True)
