"""Smart UV Project on the cockatrice mesh (rest pose), then export a neutral, unrigged GLB for the Meshy retexture.
The head and upper neck islands get 2.5x texel density (claude_shared/uv_head_density.py).
Saves work/anim_v1.blend with UVs and texturing/ckt_neutral_upload.glb."""
import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
from uv_head_density import scale_head_islands
mesh = bpy.data.objects['Cockatrice']; rig = bpy.data.objects['Ckt_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
scale_head_islands(mesh, ('Head', 'Neck2'), factor=2.5)  # head, beak, upper neck
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_mainfile()
# neutral copy without armature
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'ckt_neutral_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE')
print('UV islands done; exported')
