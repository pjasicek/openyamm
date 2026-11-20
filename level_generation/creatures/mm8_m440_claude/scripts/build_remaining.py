from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
lib=root/'anim_library/humanoid_set'
run('retarget.py',p/'work/pilot_grip.blend',p/'work/full_set.blend',f'{lib}/Armed.glb:ArmedGetHitF1:Hit',f'{lib}/Armed.glb:ArmedDeath1:Death',f'{lib}/Armed.glb:ArmedIdleAlert1:Fidget')
run('retarget_mixamo.py',p/'work/full_set.blend',p/'work/full_mixamo.blend',f'{root}/anim_library/mixamo/Standard Run.fbx:Running')
run('foot_level.py',p/'work/full_mixamo.blend',p/'work/full_feet.blend','Hit','Fidget','Death:until=12','Running:const')
run('author_carry.py',p/'work/full_feet.blend',p/'work/full_carried.blend','Hit:.50','Fidget:.15','Running:.25')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Hit,Death,Fidget,Running'
run('twist_bones.py',p/'work/full_carried.blend',p/'work/full_twist.blend')
run('apply_grip.py',p/'work/full_twist.blend',p/'work/full_grip.blend')
