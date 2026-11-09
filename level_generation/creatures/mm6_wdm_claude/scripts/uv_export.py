"""Export the rest-pose demon mesh (no rig, no materials) as texturing/wdm_neutral_upload.glb for the Meshy retexture.
Meshy makes its own UV layout (enable_original_uv: false); transfer_uv.py copies it back onto the rigged mesh.
(A Blender Smart UV Project gave ~1,000 tiny islands and Meshy's paint broke into per-island blobs; a seam-based
unwrap crushed the head, hands and feet.) Run on work/rig_v1.blend."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Demon']; rig = bpy.data.objects['Demon_Rig']
for b in rig.pose.bones:
    b.matrix_basis.identity()
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'wdm_neutral_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE')
print('EXPORTED neutral')
