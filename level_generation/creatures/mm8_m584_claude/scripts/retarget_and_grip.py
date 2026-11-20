from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1];R=P.parents[2]
def step(name,*args):
 script=P/'scripts'/name;sys.argv=[str(script),'--',*map(str,args)];runpy.run_path(str(script),run_name='__main__')
step('weights_raven.py')
base=R/'anim_library/humanoid_set'
step('retarget.py',P/'work/rig_owned.blend',P/'work/source_motion.blend',
 str(base/'2Hand Axe.glb')+':2HandAxeAttack1:SourceAttack',
 str(base/'2Hand Spear.glb')+':2HandSpearIdle:SourceIdle',
 str(base/'2Hand Spear.glb')+':2HandSpearGetHitF1:SourceHit',
 str(base/'2Hand Spear.glb')+':2HandSpearDeath1:SourceDeath')
for side in ('R','L'):
 step('grip_from_source.py',base/'2Hand Axe.glb',side,'2HandAxeAttack1:15')
 step('grip_solve.py',P/'work/source_motion.blend','SourceAttack',15,side)
