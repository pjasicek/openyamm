"""Import the Smart Topology return, normalise it (abdomen tip at z = 0, facing -Y, centred on x/y, total height
QUEEN_HEIGHT metres) and report components, triangles and bounds. Writes work/step0.blend (object 'Queen') and
review/step0_<view>.png clay turnarounds."""
import bpy, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
# Horn tip to abdomen tip; the scale to game units is set from the native frames in actors.yml.
QUEEN_HEIGHT = 2.4
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.name = 'Queen'
ob.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in ob.data.vertices])
lo, hi = co.min(0), co.max(0)
scale = QUEEN_HEIGHT / (hi[2] - lo[2])
centre = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
ob.data.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(-centre))
ob.data.update()
co = np.array([tuple(v.co) for v in ob.data.vertices])
# Facing: the face (top tenth) should sit at -Y relative to the back; report it rather than guess.
top = co[co[:, 2] > co[:, 2].max() - 0.35]
import bmesh
bm = bmesh.new(); bm.from_mesh(ob.data)
islands = []
seen = set()
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]; comp = []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if w.index not in seen:
                seen.add(w.index); stack.append(w)
    islands.append(comp)
tris = sum(len(f.verts) - 2 for f in bm.faces)
report = {'scale': scale, 'vertices': len(bm.verts), 'triangles': tris, 'components': sorted(map(len, islands), reverse=True)[:12],
          'bounds_min': co.min(0).tolist(), 'bounds_max': co.max(0).tolist(), 'head_mean_y': float(top[:, 1].mean())}
print('LOAD', json.dumps(report))
(P / 'work').mkdir(exist_ok=True)
(P / 'work' / 'step0_report.json').write_text(json.dumps(report, indent=1))
scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(str(P / 'review' / 'step0'), QUEEN_HEIGHT / 2, QUEEN_HEIGHT * 1.1,
                    views=('front', 'left', 'back', 'three_quarter'), resolution=(512, 768))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'step0.blend'))
