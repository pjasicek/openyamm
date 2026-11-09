from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('retarget.py',p/'work/rig_v1.blend',p/'work/motion_rpg.blend',str(repo/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedGetHitF1:Hit',str(repo/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedDeath1:Death')
run('retarget_mixamo.py',p/'work/motion_rpg.blend',p/'work/motion_v1.blend',str(repo/'anim_library/mixamo/Standard Idle.fbx')+':Standing',str(repo/'anim_library/mixamo/Standard Walk.fbx')+':Walking',str(repo/'anim_library/mixamo/_discarded/Neck Stretching.fbx')+':Fidget')
run('retarget.py',p/'work/motion_v1.blend',p/'work/motion_planted.blend',str(repo/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedGetHitF1:Hit:plant')
run('twist_bones.py',p/'work/motion_planted.blend',p/'work/motion_twist.blend')
run('finger_weights.py',p/'work/motion_twist.blend',p/'work/weighted_v1.blend')
