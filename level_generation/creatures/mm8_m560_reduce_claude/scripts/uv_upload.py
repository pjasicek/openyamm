"""Fresh UVs for the rebuilt wyvern with the creature's own settings (mm8_m560_claude/scripts/uv_export.py: smart
project 1.15 rad, margin 0.004, head and jaw islands 2.5x denser), then the static Meshy upload.
work/rebuild.blend -> work/uv_master.blend, work/uv3d.npz (per triangle uv, rest xyz, part),
work/uv_metrics.json (uv_layout.py draws the layout and coverage), texturing/wyvern_upload.glb. Usage: blender -b -P uv_upload.py"""
import json, os, sys
import bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
from uv_head_density import scale_head_islands  # noqa: E402
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rebuild.blend'))
mesh = bpy.data.objects['Rebuilt']; rig = bpy.data.objects['Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.004, area_weight=0., scale_to_bounds=False)
scale_head_islands(mesh, ('Head', 'Jaw'), factor=2.5)
bpy.ops.uv.pack_islands(margin=.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
me = mesh.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
part = np.array([a.value for a in me.attributes['part'].data])
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], np.float32)
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], np.float32)
P = np.array([part[t.polygon_index] for t in me.loop_triangles], np.int32)
areas = np.abs(np.cross(U[:, 1] - U[:, 0], U[:, 2] - U[:, 0])) * .5
assert np.isfinite(U).all() and U.min() >= -1e-5 and U.max() <= 1 + 1e-5
assert (areas > 1e-12).all(), f'{int((areas <= 1e-12).sum())} degenerate UV triangles'
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=X, part=P)
head_w = {g.index for g in mesh.vertex_groups if g.name in ('Head', 'Jaw')}
hv = np.array([sum(g.weight for g in v.groups if g.group in head_w) for v in me.vertices])
head = np.array([hv[list(t.vertices)].mean() > .5 for t in me.loop_triangles])
area3 = np.linalg.norm(np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]), axis=1) * .5
dens = lambda m: float(np.sqrt(areas[m].sum() / area3[m].sum()) * 2048)
report = {'triangles': len(U), 'texels_per_m_head': round(dens(head), 1),
          'texels_per_m_rest': round(dens(~head), 1), 'parts': {str(k): int((P == k).sum()) for k in np.unique(P)}}
json.dump(report, open(os.path.join(HERE, 'work', 'uv_metrics.json'), 'w'), indent=1); print('UV', report)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = mesh.matrix_world.copy(); bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'wyvern_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE')
print('UPLOAD written')
