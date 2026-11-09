"""Load a GLB (or a .blend's 'Body'), print loose parts, triangle count and bounds, and render a clay turnaround
(front, left, back, right, three-quarter) to <out prefix>_<view>.png plus a joined sheet <out prefix>.png.
Args: -- <glb|blend> <out prefix> [height m: normalise, soles at 0, centred]"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
height = float(a[2]) if len(a) > 2 else None
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or o.name != 'Body':
            if o.type == 'ARMATURE':
                continue
    ob = bpy.data.objects['Body']
    if ob.parent:
        ob.modifiers.clear()
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in bpy.data.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
if height:
    s = height / (co[:, 2].max() - co[:, 2].min())
    ob.scale = (s, s, s)
    ob.location = (-(co[:, 0].max() + co[:, 0].min()) / 2 * s, -(co[:, 1].max() + co[:, 1].min()) / 2 * s,
                   -co[:, 2].min() * s)
    bpy.ops.object.transform_apply(location=True, scale=True)
    co = np.array([tuple(v.co) for v in ob.data.vertices])
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
# loose parts by connectivity
seen = np.zeros(len(bm.verts), bool); parts = []
for v in bm.verts:
    if seen[v.index]:
        continue
    stack = [v]; seen[v.index] = True; comp = []
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if not seen[y.index]:
                seen[y.index] = True; stack.append(y)
    parts.append(comp)
parts.sort(key=len, reverse=True)
nb = sum(1 for e in bm.edges if e.is_boundary)
print('INSPECT verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'parts', len(parts),
      'boundary edges', nb)
print('INSPECT bounds', np.round(co.min(0), 3), np.round(co.max(0), 3))
for i, p in enumerate(parts[:25]):
    c = co[p]
    print(f'INSPECT part {i}: {len(p)} verts centre {np.round(c.mean(0), 3)} size {np.round(c.max(0) - c.min(0), 3)}')
bm.free()
scene = bpy.context.scene
common.workbench_clay(scene)
lo, hi = co.min(0), co.max(0)
H = (hi[2] - lo[2]) * 1.1
ob.data.materials.clear()
files = common.render_views(out, (lo[2] + hi[2]) / 2, H, views=('front', 'left', 'back', 'right', 'three_quarter'),
                            resolution=(512, 640))
try:
    from PIL import Image
except ImportError:
    Image = None
if Image:
    ims = [Image.open(f) for f in files]
    S = Image.new('RGB', (sum(i.width for i in ims), ims[0].height))
    x = 0
    for i in ims:
        S.paste(i, (x, 0)); x += i.width
    S.save(out + '.png')
