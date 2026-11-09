"""Transfer rest shading normals only; frozen topology, weights, UVs and poses are untouched."""
import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/ceiling1_0.1.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
with bpy.data.libraries.load(str(P/'work/round2/lod0_selected.blend'),link=False)as(a,b):b.objects=['Body']
src=b.objects[0];bpy.context.scene.collection.objects.link(src);src.modifiers.clear();src.parent=None;src.hide_render=True
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
mod=ob.modifiers.new('AcceptedRestNormals','DATA_TRANSFER');mod.object=src;mod.use_loop_data=True;mod.data_types_loops={'CUSTOM_NORMAL'};mod.loop_mapping='POLYINTERP_NEAREST'
while ob.modifiers[0]!=mod:bpy.ops.object.modifier_move_up(modifier=mod.name)
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(src,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/lod1_normal_transfer.blend'))
os.environ['LCH_EXPORT_BLEND']='work/round2/lod1_normal_transfer.blend';os.environ['LCH_EXPORT_PATH']='work/round2/lod1_geometry.glb';os.environ['LCH_TEXTURE_ROOT']='textures/round2';runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
