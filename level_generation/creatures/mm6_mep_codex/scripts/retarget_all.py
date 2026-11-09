import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_mep.py')
roles=[('Relax','RelaxIdle','Standing'),('Relax','RelaxWalkForward','Walking'),('Relax','RelaxRunForward','Running'),('Relax','RelaxIdle','Fidget'),('Unarmed','UnarmedGetHitF1','Hit'),('2Hand Staff','StaffAttack1','Attack'),('2Hand Staff','StaffCastLAttack3','Cast')]
run('retarget.py',p/'work/rig_clean.blend',p/'work/retarget_raw.blend',*[f'{root}/anim_library/humanoid_set/{s}.glb:{c}:{n}' for s,c,n in roles])
run('retarget_mixamo.py',p/'work/retarget_raw.blend',p/'work/retarget_raw.blend',f'{root}/anim_library/mixamo/Standing React Death Backward.fbx:Death')
run('grip_from_source.py',root/'anim_library/humanoid_set/2Hand Staff.glb','StaffAttack1:1')
run('rom_extract.py',*[f'{n}={root}/anim_library/humanoid_set/{s}.glb:{c}' for s,c,n in roles])
