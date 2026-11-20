import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
lib=Path('/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set')
for name,clips in [('Unarmed',['UnarmedDeath1']),('2Hand Sword',['2HandSwordDeath1']),('Armed-Shield',['ShieldDeath1']),('Armed',['ArmedIdleAlert1'])]:
 sys.argv=['rpg_preview.py','--',str(lib/(name+'.glb')),str(p/'review'/('source_'+name.replace(' ','_'))),'three_quarter','6']+clips
 runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
