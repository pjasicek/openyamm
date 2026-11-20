import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);L=P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
clips={'Standing':'Idle','Walking':'Walk','Running':'RunForward','Attack':'Attack2','Cast':'Attack2','Hit':'GetHitF1','Death':'Death1','Fidget':'IdleAlert1'}
run('retarget.py',['work/rig_v1.blend','work/rig_v2.blend',*[f'{L}:2HandAxe{clip}:{role}' for role,clip in clips.items()]])
run('twist_bones.py',['work/rig_v2.blend','work/rig_v2t.blend']);run('weights_minotaur.py');run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend'])
