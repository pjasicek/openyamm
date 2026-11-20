"""Retarget selected local sources at their original speed; fit pilot skin and grip."""
import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent/'work';ROOT=P.parents[3]
def run(n,*args):
    sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/n),run_name='__main__')
run('weights_fix.py',W/'rig_v1.blend',W/'rig_weighted.blend')
run('finger_weights.py',W/'rig_weighted.blend',W/'rig_fingers.blend')
run('retarget.py',W/'rig_fingers.blend',W/'sources_set.blend',str(ROOT/'anim_library/humanoid_set/Armed.glb')+':ArmedIdle:GripRef',str(ROOT/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedGetHitF1:Hit')
run('retarget_mixamo.py',W/'sources_set.blend',W/'sources.blend',*[str(ROOT/'anim_library/mixamo'/fn)+':'+act for fn,act in [('Standard Idle.fbx','Standing'),('Walk.fbx','Walking'),('Standard Run.fbx','Running'),('Standing React Death Backward.fbx','Death'),('Sword And Shield Power Up.fbx','Fidget:plant'),('Stabbing (2).fbx','Stab2:turn')]])
run('foot_level.py',W/'sources.blend',W/'sources_level.blend','Standing','Walking:const','Hit','Fidget','Death:until=24')
run('grip_from_source.py',ROOT/'anim_library/humanoid_set/Armed.glb','ArmedIdle:0')
os.environ['GRIP_RENDER']=str(P.parent/'review/grip_left')
run('grip_solve.py',W/'sources_level.blend','GripRef',0)
