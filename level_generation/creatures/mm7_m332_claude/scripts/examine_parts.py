"""Exam of the Smart Topology return: normalise (height env H, default 1.7 m, soles z=0, faces -Y), split loose parts, report each part
(verts/tris/bounds/boundary edges/non-manifold) and render each part coloured. Args: glb tag."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, tag = sys.argv[sys.argv.index('--') + 1:]
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in bpy.data.objects: o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in obj.data.vertices])
H = float(os.environ.get('H', '1.7'))
s = H / (co[:, 2].max() - co[:, 2].min())
obj.scale = (s, s, s)
obj.location = (-(co[:, 0].max() + co[:, 0].min()) / 2 * s, -(co[:, 1].max() + co[:, 1].min()) / 2 * s, -co[:, 2].min() * s)
bpy.ops.object.transform_apply(location=True, scale=True)
obj.data.materials.clear()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
rep = []
cols = [(0.9,0.3,0.3,1),(0.3,0.8,0.3,1),(0.3,0.5,0.95,1),(0.95,0.8,0.2,1),(0.8,0.3,0.9,1),(0.2,0.85,0.85,1),(0.95,0.55,0.2,1),(0.6,0.6,0.6,1)]
for i, o in enumerate(sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: -len(o.data.vertices))):
    c = np.array([tuple(v.co) for v in o.data.vertices])
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = {'name': f'P{i:02d}', 'verts': len(c), 'tris': sum(len(p.vertices) - 2 for p in o.data.polygons),
         'lo': [round(float(x), 3) for x in c.min(0)], 'hi': [round(float(x), 3) for x in c.max(0)],
         'mean': [round(float(x), 3) for x in c.mean(0)],
         'boundary': sum(1 for e in bm.edges if e.is_boundary), 'nonmanifold': sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)}
    bm.free(); rep.append(r); o.name = r['name']
    m = bpy.data.materials.new(r['name']); m.diffuse_color = cols[i % len(cols)]; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    print('PART', json.dumps(r))
json.dump(rep, open(os.path.join(common.WORK, f'{tag}_parts.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, f'{tag}_parts.blend'))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
for o in bpy.data.objects:
    if o.type == 'MESH': o.show_wire = True
common.render_views(os.path.join(common.REVIEW, f'{tag}_parts'), 0.47 * H, H, views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900))
common.render_views(os.path.join(common.REVIEW, f'{tag}_head'), 0.84 * H, 0.21 * H, views=('front', 'left'), resolution=(500, 500))
