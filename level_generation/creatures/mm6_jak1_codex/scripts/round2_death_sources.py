import bpy,sys,runpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(P/'scripts'))
sys.argv=['retarget','--',str(P/'work/round2_sources.blend'),str(P/'work/round2_sources.blend'),f'{ROOT}/anim_library/humanoid_set/2Hand Staff.glb:StaffDeath1:StaffFall']
runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
sys.argv=['mixamo','--',str(P/'work/round2_sources.blend'),str(P/'work/round2_sources.blend'),f'{ROOT}/anim_library/mixamo/Standing Death Forward 02.fbx:DeathForward']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G={s:json.loads((P/f'work/grip_pose{su}.json').read_text()) for s,su in [('R',''),('L','_left')]}
a=bpy.data.actions['Staff2'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in [0,5,10,15,20,30]:
 sc.frame_set(f);M={s:rig.matrix_world@rig.pose.bones[f'B_{s}_Hand'].matrix for s in 'LR'};A={s:(M[s].to_3x3()@Vector(G[s]['handle_axis_hand_local'])).normalized() for s in 'LR'};axis=(M['L']@Vector(G['L']['handle_centre_hand_local'])-M['R']@Vector(G['R']['handle_centre_hand_local'])).normalized();print('LIBRARY THUMBS',f,A['L'].dot(A['R']),A['R'].dot(axis),A['L'].dot(axis),flush=True)
import common,numpy as np
common.workbench_clay(sc)
for clip in ['StaffFall','DeathForward']:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i,f in enumerate(np.linspace(*a.frame_range,5)):
  sc.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/round2/sources/{clip}_{i}'),.8,3.5,views=('left','front'),resolution=(320,400))
