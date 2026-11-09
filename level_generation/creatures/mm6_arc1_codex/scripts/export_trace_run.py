import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_clips.blend'));rig=bpy.data.objects['Rig']
for o in bpy.data.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/source_motion.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_yup=True,export_reset_pose_bones=True)
L=P.parents[2]/'anim_library/humanoid_set/2Hand Bow.glb';refs=[f'{role}={L}:{clip}'for role,clip in [('Standing','2HandBowIdle'),('Walking','2HandBowWalk'),('Hit','2HandBowGetHitF1'),('Death','2HandBowDeath1'),('Fidget','2HandBowBoost1')]]
refs += [f'Attack_Draw={P}/work/source_motion.glb:Draw',f'Attack_Release={P}/work/source_motion.glb:Release']
sys.argv=['trace_export.py','--',str(P/'export/mm6_arc1_lod0.glb'),*refs];runpy.run_path(str(P/'scripts/trace_export.py'),run_name='__main__')
sys.argv=['rom_extract.py','--',*refs];runpy.run_path(str(P/'scripts/rom_extract.py'),run_name='__main__')
