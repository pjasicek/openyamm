from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
lib=p.parents[2]/'anim_library/humanoid_set'
roles={'Standing':('Armed','ArmedIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR3'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed','ArmedKnockdown1')}
sys.argv=[str(p/'scripts/rom_extract.py'),'--']+[f'{r}={lib/(s+".glb")}:{c}' for r,(s,c) in roles.items()]
runpy.run_path(sys.argv[0],run_name='__main__')
