import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];L=R/'anim_library/humanoid_set';MX=R/'anim_library/mixamo';os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('retarget.py',['work/pilot_raw.blend','work/actions_set.blend',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/Relax.glb:RelaxLaydownLayDown:Death',f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit'])
run('retarget_mixamo.py',['work/actions_set.blend','work/actions_raw.blend',f'{MX}/Standing Idle 03 Examine.fbx:Fidget'])
run('body_weights.py',['work/actions_raw.blend','work/actions_weights.blend'])
run('finger_weights.py',['work/actions_weights.blend','work/actions_fingers.blend'])
