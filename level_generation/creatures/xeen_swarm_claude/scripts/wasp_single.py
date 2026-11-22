"""One Stinger for the swarm: decimate the 0.45 m Smart Topology wasp to about 1,000 triangles (wings, legs and body
as rigid pieces), triangulate, unwrap with claude_shared/uv_atlas.py (head 1.5x denser) and export the static Meshy
upload texturing/wasp_upload.glb. Vertex groups: Body (everything but the wings), WingFL/WingFR/WingHL/WingHR (front
and hind wings, L = +x). Saves work/wasp_uv.blend and work/wasp_hinges.json (the wing roots). Refuses to overwrite an
existing upload (a paint may belong to it)."""
import bpy, os, sys, json, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
if os.path.exists(os.path.join(HERE, 'texturing', 'wasp_upload.glb')):
    raise SystemExit('texturing/wasp_upload.glb exists')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'wasp_clean.blend'))
m = bpy.data.objects['Wasp']
d = np.load(os.path.join(HERE, 'work', 'wasp_pieces.npz')); lab = d['label']; co = d['co']
WINGS = {'WingFL': 4, 'WingFR': 6, 'WingHL': 3, 'WingHR': 5}
hinges = {}
for name, piece in WINGS.items():
    c = co[lab == piece]
    hinges[name] = c[np.argsort(np.abs(c[:, 0]))[:12]].mean(0).tolist()   # the root: the wing's innermost points
groups = {n: m.vertex_groups.new(name=n) for n in ['Body', 'Head', *WINGS]}
wing_of = {p: n for n, p in WINGS.items()}
for v in m.data.vertices:
    p = int(lab[v.index])
    n = wing_of.get(p, 'Head' if p == 0 else 'Body')
    groups[n].add([v.index], 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = m; m.select_set(True)
t0 = len(m.data.polygons)
dec = m.modifiers.new('dec', 'DECIMATE'); dec.decimate_type = 'COLLAPSE'; dec.ratio = 0.07
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='dec')
tri = m.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier='tri')
print('REDUCED', t0, '->', len(m.data.polygons))
report = uv_atlas.unwrap(m, head_groups=('Head',), head_factor=1.5)
print('UV', report.get('use'), report.get('charts_used'), report.get('packer_used'), report.get('fallbacks'))
json.dump({'hinges': hinges, 'uv': {k: report.get(k) for k in ('use', 'charts_used', 'packer_used', 'fallbacks')}},
          open(os.path.join(HERE, 'work', 'wasp_hinges.json'), 'w'), indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'wasp_uv.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
for o in bpy.data.objects: o.select_set(o == m)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'wasp_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UPLOAD wasp', len(m.data.polygons))
