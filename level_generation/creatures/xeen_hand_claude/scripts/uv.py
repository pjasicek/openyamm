"""Unwrap the Carnage Hand (TEXTURE_QUALITY_PASS.md section 0): claude_shared/uv_atlas.unwrap with the 2026-11-12
defaults (PartUV charts from the skin-weight part tree, seam pass, sparrow), the lip lids 1.3x denser (seen up close
in the bite). Geometry is final (clean.py, rig.py). Saves work/anim_base.blend (the UV master the clips are keyed on),
work/uv_report.json and the static Meshy upload texturing/hand_upload.glb (rest pose: lids closed, no materials).
Refuses to overwrite an existing layout."""
import bpy, os, sys, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
UPLOAD = os.path.join(HERE, 'texturing', 'hand_upload.glb')
if os.path.exists(UPLOAD):
    raise SystemExit('texturing/hand_upload.glb exists: a paint may belong to this layout')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
mesh = bpy.data.objects['Hand']; rig = bpy.data.objects['Hand_Rig']
rig.data.pose_position = 'REST'
for o in bpy.data.objects: o.select_set(False)
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
nf = len(mesh.data.polygons)
report = uv_atlas.unwrap(mesh, head_groups=('LipUpper', 'LipLower'), head_factor=1.3)
assert len(mesh.data.polygons) == nf and 'part' in mesh.data.attributes
json.dump(report, open(os.path.join(HERE, 'work', 'uv_report.json'), 'w'), indent=1, default=str)
print('UV_REPORT', {k: report.get(k) for k in ('charts_used', 'packer_used', 'fallbacks', 'utilization', 'use')})
rig.data.pose_position = 'POSE'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
up = mesh.copy(); up.data = mesh.data.copy(); up.name = 'HandUpload'
bpy.context.scene.collection.objects.link(up)
up.modifiers.clear(); up.parent = None; up.matrix_world = mesh.matrix_world.copy()
up.data.materials.clear()
for o in bpy.data.objects: o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UPLOAD tris', len(up.data.polygons))
