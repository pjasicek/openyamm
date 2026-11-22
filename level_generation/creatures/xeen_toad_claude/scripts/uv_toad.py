"""Reduce, triangulate and unwrap the toad (TEXTURE_QUALITY_PASS.md section 0): collapse decimation after weighting
with the head, hands and toes protected (weights and groups kept), triangulate, claude_shared/uv_atlas.unwrap with the
2026-11-12 defaults (PartUV charts, seam pass, sparrow), head and throat 1.6x denser. The tongue gets a cylindrical
unwrap on its own material. Saves work/anim_base.blend (the UV master the clips are keyed on), work/uv_report.json and
the static Meshy upload texturing/toad_upload.glb (body only, rest pose). Refuses to overwrite an existing layout."""
import bpy, os, sys, json, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
if os.path.exists(os.path.join(HERE, 'texturing', 'toad_upload.glb')):
    raise SystemExit('texturing/toad_upload.glb exists: a paint may belong to this layout')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
mesh = bpy.data.objects['Toad']; rig = bpy.data.objects['Toad_Rig']; tongue = bpy.data.objects['Tongue']
rig.data.pose_position = 'REST'
for o in bpy.data.objects: o.select_set(False)
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
# protection group: head, hands, toes keep their density
prot = mesh.vertex_groups.new(name='Protect')
names = {g.index: g.name for g in mesh.vertex_groups}
for v in mesh.data.vertices:
    w = sum(g.weight for g in v.groups if names[g.group].startswith(('Head', 'Throat', 'Hand', 'Toes')))
    if w > 0:
        prot.add([v.index], min(1.0, w), 'REPLACE')
tris0 = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
dec = mesh.modifiers.new('dec', 'DECIMATE'); dec.decimate_type = 'COLLAPSE'; dec.ratio = 0.62
dec.vertex_group = 'Protect'; dec.invert_vertex_group = True; dec.vertex_group_factor = 0.8
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
bpy.ops.object.modifier_apply(modifier='dec')
mesh.vertex_groups.remove(mesh.vertex_groups['Protect'])
tri = mesh.modifiers.new('tri', 'TRIANGULATE'); tri.quad_method = 'SHORTEST_DIAGONAL'
bpy.ops.object.modifier_move_to_index(modifier='tri', index=0)
bpy.ops.object.modifier_apply(modifier='tri')
print('REDUCED tris', tris0, '->', len(mesh.data.polygons))
report = uv_atlas.unwrap(mesh, head_groups=('Head', 'Throat'), head_factor=1.6)
json.dump(report, open(os.path.join(HERE, 'work', 'uv_report.json'), 'w'), indent=1, default=str)
print('UV_REPORT', {k: report.get(k) for k in ('charts_used', 'packer_used', 'fallbacks', 'utilization', 'atlas')})
# tongue: cylinder unwrap (u around, v along)
me = tongue.data
layer = me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
ys = [v.co.y for v in me.vertices]; y0, y1 = min(ys), max(ys)
for p in me.polygons:
    for li in p.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        a = (math.atan2(v.z - 0.59, v.x) / (2 * math.pi)) % 1.0
        layer.data[li].uv = (a, (v.y - y0) / (y1 - y0))
rig.data.pose_position = 'POSE'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
# static upload: body only, bind pose, no materials
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
up = mesh.copy(); up.data = mesh.data.copy(); up.name = 'ToadUpload'
bpy.context.scene.collection.objects.link(up)
up.modifiers.clear(); up.parent = None; up.matrix_world = mesh.matrix_world.copy()
up.data.materials.clear()
for o in bpy.data.objects: o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'toad_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UPLOAD tris', len(up.data.polygons))
