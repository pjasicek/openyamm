import runpy, sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name,clips in [('Armed',['ArmedIdle','ArmedWalk','ArmedRunForward','ArmedIdleAlert1','ArmedGetHitF1']),('Unarmed',['UnarmedDeath1'])]:
    sys.argv=['preview_maces.py','--',f'anim_library/humanoid_set/{name}.glb',str(p/'review/motion'/name),'three_quarter','5',*clips]
    runpy.run_path(str(p/'scripts/preview_maces.py'),run_name='__main__')
