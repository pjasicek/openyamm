"""Step 1 examination of a returned mesh: topology health, triangle budget by region, hidden geometry, close-ups.
Args: glb tag. Normalises to 1.578 m height (soles at z=0, facing -Y) and writes review/<tag>_*.png + work/<tag>_exam.json."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
src, tag = args[0], args[1]
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
for o in bpy.data.objects: o.select_set(o == obj)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in obj.data.vertices])
s = 1.578 / (co[:, 2].max() - co[:, 2].min())
for v in obj.data.vertices:
    v.co = Vector(((v.co.x - (co[:, 0].max() + co[:, 0].min()) / 2) * s, (v.co.y - (co[:, 1].max() + co[:, 1].min()) / 2) * s,
                   (v.co.z - co[:, 2].min()) * s))
obj.data.update()
for p in obj.data.polygons: p.use_smooth = True
bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
report = {'verts': len(bm.verts), 'tris': sum(len(f.verts) - 2 for f in bm.faces)}
report['non_manifold_edges'] = sum(1 for e in bm.edges if not e.is_manifold)
report['boundary_edges'] = sum(1 for e in bm.edges if e.is_boundary)
report['wire_edges'] = sum(1 for e in bm.edges if e.is_wire)
report['degenerate_faces'] = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
report['loose_verts'] = sum(1 for v in bm.verts if not v.link_faces)
# connected components
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; seen.add(v.index); comp = []
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); stack.append(y)
    comps.append(comp)
cc = np.array([tuple(v.co) for v in bm.verts])
report['components'] = [{'verts': len(c), 'z': [round(float(cc[c][:, 2].min()), 3), round(float(cc[c][:, 2].max()), 3)]}
                        for c in sorted(comps, key=len, reverse=True)[:12]]
# triangle budget by region (face centres)
fc = np.array([tuple(f.calc_center_median()) for f in bm.faces]); ft = np.array([len(f.verts) - 2 for f in bm.faces])
regions = {'head_neck z>1.33': fc[:, 2] > 1.33,
           'hands |x|>0.30 z<1.0': (np.abs(fc[:, 0]) > 0.30) & (fc[:, 2] < 1.0),
           'arms+sleeves |x|>0.16 z>=1.0 or |x| in(0.22,0.30)': ((np.abs(fc[:, 0]) > 0.16) & (fc[:, 2] >= 1.0) & (fc[:, 2] <= 1.33)),
           'torso 0.95<z<=1.33 |x|<=0.16': (fc[:, 2] > 0.95) & (fc[:, 2] <= 1.33) & (np.abs(fc[:, 0]) <= 0.16),
           'skirt 0.15<z<=0.95 |x|<=0.30': (fc[:, 2] > 0.15) & (fc[:, 2] <= 0.95) & (np.abs(fc[:, 0]) <= 0.30),
           'feet/ankles z<=0.15': fc[:, 2] <= 0.15}
report['tris_by_region'] = {k: int(ft[m].sum()) for k, m in regions.items()}
# hidden geometry: faces whose outward ray is blocked within the skirt volume (legs inside skirt etc.)
tree = BVHTree.FromBMesh(bm)
hidden = 0; hidden_z = []
for f in bm.faces:
    c = f.calc_center_median(); n = f.normal
    hit = tree.ray_cast(c + n * 1e-4, n, 2.0)
    if hit[0] is not None and 0.15 < c.z < 0.95 and abs(c.x) < 0.3:
        # count if the blocking surface is the skirt and this face is inside it
        hidden += 1; hidden_z.append(c.z)
report['inner_faces_under_skirt_estimate'] = hidden
bm.free()
json.dump(report, open(os.path.join(common.WORK, f'{tag}_exam.json'), 'w'), indent=1)
print('EXAM', json.dumps(report))
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.show_cavity = True
obj.show_wire = True
scene.display.shading.wireframe_color_type = 'THEME' if hasattr(scene.display.shading, 'wireframe_color_type') else None
def shots(name, cz, hh, views, target, res=(500, 500)):
    common.render_views(os.path.join(common.REVIEW, f'{tag}_{name}'), cz, hh, views=views, resolution=res, target=target)
mesh_co = np.array([tuple(v.co) for v in obj.data.vertices])
rh = mesh_co[(mesh_co[:, 0] < -0.25) & (mesh_co[:, 2] < 1.0)]
shots('hand', float(rh[:, 2].mean()), 0.24, ('front', 'right'), (float(rh[:, 0].mean()), float(rh[:, 1].mean())))
shots('face', 1.46, 0.30, ('front', 'left', 'three_quarter'), (0, 0))
shots('feet', 0.08, 0.35, ('front', 'left'), (0, 0))
shots('braid', 1.35, 0.45, ('back', 'left'), (0, 0))
# wireframe overlay full body (topology density)
bpy.context.scene.render.use_freestyle = False
shots('wire', 0.8, 1.7, ('front', 'back'), (0, 0), res=(800, 800))
# look up under the skirt
cam_data = bpy.data.cameras.new('under'); cam = bpy.data.objects.new('under', cam_data); scene.collection.objects.link(cam)
cam.location = (0.9, -0.9, 0.05); cam.rotation_euler = (math.radians(95), 0, math.radians(45)); cam_data.lens = 28
scene.camera = cam; scene.render.resolution_x = scene.render.resolution_y = 600
scene.render.filepath = os.path.join(common.REVIEW, f'{tag}_under.png'); bpy.ops.render.render(write_still=True)
cut = obj.modifiers.new('cut', 'BOOLEAN')
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.5 - 0.0, 0.8)); box = bpy.context.active_object; box.scale = (2, 1, 2); box.hide_render = True
cut.object = box; cut.operation = 'DIFFERENCE'; cut.solver = 'EXACT'
shots('section', 0.8, 1.7, ('front',), (0, 0), res=(700, 700))
