import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];S=R/'anim_library/humanoid_set/2Hand Bow.glb'
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
clips={'Standing':'2HandBowIdle','Walking':'2HandBowWalk','Running':'2HandBowRunForward','Attack':'2HandBowAttack1','Hit':'2HandBowGetHitF1','Death':'2HandBowDeath1'}
run('retarget.py',P/'work/rig_v1.blend',P/'work/rig_v2.blend',*[str(S)+':'+c+':'+n for n,c in clips.items()])
run('twist_bones.py',P/'work/rig_v2.blend',P/'work/rig_v3.blend')
run('finger_weights.py',P/'work/rig_v3.blend',P/'work/rig_v4.blend')
run('grip_from_source.py',S,'2HandBowIdle:0','2HandBowAttack1:14')
run('grip_solve.py',P/'work/rig_v4.blend','Standing','0')
