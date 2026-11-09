import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
lib=Path('/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set')
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('extract_rom.py')
roles={'Standing':('Relax','RelaxIdle'),'Fidget':('Relax','RelaxIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR1'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed-Shield','ShieldDeath1')}
run('retarget.py',[p/'work/rig_v1.blend',p/'work/rig_v2.blend']+[f'{lib}/{s}.glb:{c}:{role}' for role,(s,c) in roles.items()])
run('twist_bones.py',[p/'work/rig_v2.blend',p/'work/rig_v2t.blend'])
