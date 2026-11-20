from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];root=p.parents[2];sys.path.insert(0,str(p/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
lib=root/'anim_library/humanoid_set'
run('retarget.py',p/'work/pilot_fitted.blend',p/'work/full_set.blend',f'{lib}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{lib}/Relax.glb:RelaxYes:Fidget',f'{lib}/Unarmed.glb:UnarmedDeath1:Death')
run('retarget_mixamo.py',p/'work/full_set.blend',p/'work/full_raw.blend',f'{root}/anim_library/mixamo/Running (5).fbx:Running')
run('adapt_remaining.py')
os.environ['RUN_STRIDE']='1.2'
run('run_fit.py',p/'work/full_fitted.blend',p/'work/full_fitted.blend')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Hit,Death,Dead,Fidget,Running'
run('twist_bones.py',p/'work/full_fitted.blend',p/'work/full_fitted.blend')
for view in ['front','left']:run('clip_sheet.py',p/'work/full_fitted.blend',p/f'review/full_{view}',view,7,'Hit','Fidget','Death','Running')
run('export_full.py')
run('run_full_gates.py')
