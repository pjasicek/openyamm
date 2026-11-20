"""Smart UV Project on the spider (rest pose; after mm6_rat_claude/scripts/uv_export.py), then a neutral unrigged GLB
for the Meshy retexture (enable_original_uv: true). Cephalothorax and fang islands get 2x texel density (mm6_spi1) (claude_shared/uv_head_density.py).
Args: -- <in blend> <out blend>   (writes texturing/m402_upload.glb)"""
import bpy, os, sys
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
mesh = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
rig.animation_data_create(); rig.animation_data.action = None
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
scale_head_islands(mesh, ('Thorax', 'Fang_L', 'Fang_R'), factor=2.0)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None; dup.vertex_groups.clear()
for at in [a.name for a in dup.data.attributes if a.name in ('piece', 'orig_co')]:
    dup.data.attributes.remove(dup.data.attributes[at])
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'm402_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UVEXPORT islands packed; exported texturing/m402_upload.glb')
