import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p)
lib=Path('/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set')
roles={'Standing':('Relax','RelaxIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR1'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed-Shield','ShieldDeath1'),'Fidget':('Relax','RelaxIdle')}
sys.argv=['rom_extract.py','--']+[f'{role}={lib}/{s}.glb:{c}' for role,(s,c) in roles.items()]
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
