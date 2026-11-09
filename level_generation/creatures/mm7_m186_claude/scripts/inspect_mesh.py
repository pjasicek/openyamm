"""Import the Meshy return, report size/triangles/connected pieces and render four labelled clay views with a 5 cm
grid (top, front, side, quarter) to review/geometry_*.png. Args: <glb relative to project> <out tag>."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
src, tag = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(P, src))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices])
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
seen = np.zeros(len(bm.verts), bool); parts = []
for v in bm.verts:
    if seen[v.index]:
        continue
    stack = [v]; seen[v.index] = True; ids = []
    while stack:
        a = stack.pop(); ids.append(a.index)
        for e in a.link_edges:
            b = e.other_vert(a)
            if not seen[b.index]:
                seen[b.index] = True; stack.append(b)
    parts.append(ids)
parts.sort(key=len, reverse=True)
tris = sum(len(f.verts) - 2 for f in bm.faces)
info = {'vertices': len(co), 'triangles': tris, 'bbox_min': co.min(0).round(4).tolist(), 'bbox_max': co.max(0).round(4).tolist(),
        'parts': [{'verts': len(p), 'min': co[p].min(0).round(3).tolist(), 'max': co[p].max(0).round(3).tolist()} for p in parts[:40]],
        'part_count': len(parts)}
os.makedirs(os.path.join(P, 'review'), exist_ok=True)
json.dump(info, open(os.path.join(P, f'review/geometry_{tag}.json'), 'w'), indent=1)
print('INFO', json.dumps({k: info[k] for k in ('vertices', 'triangles', 'bbox_min', 'bbox_max', 'part_count')}))
lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2; span = float((hi - lo).max())
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True; sh.color_type = 'SINGLE'; sh.single_color = (0.78, 0.72, 0.64)
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
# grid lines as thin boxes
gbm = bmesh.new()
step = 0.05
for x in np.arange(np.floor(lo[0] / step) * step, hi[0] + step, step):
    bmesh.ops.create_cube(gbm, size=1, matrix=Matrix.Translation((x, c[1], lo[2] - 0.002)) @ Matrix.Diagonal((0.0015, hi[1] - lo[1] + 0.1, 0.0015, 1)))
for y in np.arange(np.floor(lo[1] / step) * step, hi[1] + step, step):
    bmesh.ops.create_cube(gbm, size=1, matrix=Matrix.Translation((c[0], y, lo[2] - 0.002)) @ Matrix.Diagonal((hi[0] - lo[0] + 0.1, 0.0015, 0.0015, 1)))
gm = bpy.data.meshes.new('grid'); gbm.to_mesh(gm); g = bpy.data.objects.new('grid', gm); sc.collection.objects.link(g)
views = {'top': (Vector((0, 0, 1)), Vector((0, 1, 0))), 'front': (Vector((0, -1, 0)), Vector((0, 0, 1))),
         'side': (Vector((-1, 0, 0)), Vector((0, 0, 1))), 'quarter': (Vector((-0.7, -0.7, 0.45)).normalized(), Vector((0, 0, 1)))}
for name, (d, up) in views.items():
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = span * 1.1
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
    z = d; x = up.cross(z).normalized(); y = z.cross(x)
    cam.matrix_world = Matrix.Translation(Vector(c) + d * 3) @ Matrix((x, y, z)).transposed().to_4x4()
    sc.camera = cam; sc.render.filepath = os.path.join(P, f'review/geometry_{tag}_{name}.png')
    bpy.ops.render.render(write_still=True)
print('RENDERED')
