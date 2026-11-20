from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
lib=root/'anim_library/humanoid_set'
run('retarget.py',p/'work/pilot_fitted.blend',p/'work/full_set.blend',f'{lib}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{lib}/Unarmed.glb:UnarmedIdleAlert1:Fidget',f'{lib}/Unarmed.glb:UnarmedCastDualAttack2:Cast',f'{lib}/Armed.glb:ArmedDeath1:Death')
run('retarget_mixamo.py',p/'work/full_set.blend',p/'work/full_raw.blend',f'{root}/anim_library/mixamo/Standard Run.fbx:Running')
run('adapt_remaining.py')
run('align_full_hinges.py')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Hit,Death,Dead,Fidget,Cast,Running'
run('twist_bones.py',p/'work/full_fitted.blend',p/'work/full_fitted.blend')
for view in ['front','left','three_quarter']:run('clip_sheet.py',p/'work/full_fitted.blend',p/f'review/full_{view}',view,9,'Hit','Fidget','Cast','Death','Running')
run('export_full.py')
run('run_full_gates.py')
