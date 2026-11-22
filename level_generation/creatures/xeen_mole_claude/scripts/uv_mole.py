"""Triangulate and unwrap the mole (TEXTURE_QUALITY_PASS.md section 0): claude_shared/uv_atlas.unwrap with the
2026-11-12 defaults (PartUV charts, seam pass, sparrow), head and snout 1.6x denser (the face is what the party
sees). No reduction: 7.8k triangles with most of them in the claws. Saves work/anim_base.blend (the UV master the
clips are keyed on), work/uv_report.json and the static Meshy upload texturing/mole_upload.glb (rest pose).
Refuses to overwrite an existing layout."""
import bpy, os, sys, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
if os.path.exists(os.path.join(HERE, 'texturing', 'mole_upload.glb')):
    raise SystemExit('texturing/mole_upload.glb exists: a paint may belong to this layout')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
mesh = bpy.data.objects['Mole']; rig = bpy.data.objects['Mole_Rig']
rig.data.pose_position = 'REST'
for o in bpy.data.objects: o.select_set(False)
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
tri = mesh.modifiers.new('tri', 'TRIANGULATE'); tri.quad_method = 'SHORTEST_DIAGONAL'
bpy.ops.object.modifier_move_to_index(modifier='tri', index=0)
bpy.ops.object.modifier_apply(modifier='tri')
print('TRIS', len(mesh.data.polygons))
report = uv_atlas.unwrap(mesh, head_groups=('Head', 'Snout'), head_factor=1.6)
json.dump(report, open(os.path.join(HERE, 'work', 'uv_report.json'), 'w'), indent=1, default=str)
print('UV_REPORT', {k: report.get(k) for k in ('charts_used', 'packer_used', 'fallbacks', 'utilization', 'atlas')})
rig.data.pose_position = 'POSE'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
up = mesh.copy(); up.data = mesh.data.copy(); up.name = 'MoleUpload'
bpy.context.scene.collection.objects.link(up)
up.modifiers.clear(); up.parent = None; up.matrix_world = mesh.matrix_world.copy()
up.data.materials.clear()
for o in bpy.data.objects: o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'mole_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UPLOAD tris', len(up.data.polygons))
