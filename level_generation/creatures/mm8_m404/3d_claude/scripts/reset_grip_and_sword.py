import bpy,json,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_motion.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
for side in 'RL':
 path=p/('work/grip_pose_'+side+'.json');g=json.load(open(path));g['finger_local']={n:list(r.pose.bones[n].rotation_quaternion) for n in g['finger_local']};g.pop('surface_fit',None);json.dump(g,open(path,'w'),indent=2)
runpy.run_path(str(p/'scripts/make_sword.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/check_fit_pipeline.py'),run_name='__main__')
