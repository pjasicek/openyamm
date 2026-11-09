import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));C.reset();r=bpy.data.objects['Rig'];bpy.ops.object.select_all(action='DESELECT')
 for n in ['Body','SpearMesh','BucklerMesh']:bpy.data.objects[n].select_set(True)
 body=bpy.data.objects['Body'];bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Natm'
 for ob in bpy.data.objects:ob.select_set(ob in [r,body])
 bpy.context.view_layer.objects.active=r
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_natm_raw_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
