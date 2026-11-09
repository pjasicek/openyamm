from pathlib import Path
import bpy, sys, runpy
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
from sword import add_sword
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5t.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
sword=add_sword(rig)
for o in bpy.data.objects:o.select_set(o in (body,sword))
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
body.data.materials.clear()
mat=bpy.data.materials.new('OgreClay');mat.use_nodes=True
body.data.materials.append(mat)
bpy.context.scene.render.fps=30;bpy.context.scene.render.fps_base=1
rig.animation_data.action=bpy.data.actions['Standing']
rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0]
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
(p/'review/viewer').mkdir(exist_ok=True)
out=p/'review/viewer/mm6_ogr_clay.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_animations=True,
 export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,
 export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,
 export_anim_slide_to_zero=True)
for name in ['g6_sword_mesh.py','blade_edge_gate.py']:
 s=p/'scripts'/name;sys.argv=[str(s),'--',str(out)]
 runpy.run_path(str(s),run_name='__main__')
