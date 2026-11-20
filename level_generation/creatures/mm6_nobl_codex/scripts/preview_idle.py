import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
sys.argv=['rpg_preview.py','--','/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set/Relax.glb',str(p/'review/source_relax'),'three_quarter','4','RelaxIdle']
runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['hand_xray.py','--',str(p/'work/rig_v1.blend'),'R',str(p/'review/hand_fit')]
runpy.run_path(str(p/'scripts/hand_xray.py'),run_name='__main__')
