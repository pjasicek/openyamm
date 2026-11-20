import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));L=P.parents[2]/'anim_library/humanoid_set';MX=P.parents[2]/'anim_library/mixamo'
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('retarget.py',['work/rig_v1.blend','work/rig_set.blend',f'{L}/2Hand Bow.glb:2HandBowIdle:Standing',f'{L}/2Hand Bow.glb:2HandBowWalk:Walking',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/2Hand Bow.glb:2HandBowGetHitF1:Hit',f'{L}/2Hand Bow.glb:2HandBowDeath1:Death',f'{L}/2Hand Bow.glb:2HandBowBoost1:Boost'])
run('retarget_mixamo.py',['work/rig_set.blend','work/rig_sources.blend',f'{MX}/Standing Draw Arrow.fbx:Draw:plant',f'{MX}/Standing Aim Recoil.fbx:Release:plant',f'{MX}/Standing Draw Arrow.fbx:DrawFull:turn',f'{MX}/Standing Aim Recoil.fbx:ReleaseFull:turn'])
