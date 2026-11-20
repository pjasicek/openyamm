"""G1 previews on the owned source mannequin, before modelling."""
import sys, runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
root=p.parents[2]
sys.path.insert(0,str(p/'scripts'))
source=root/'anim_library/humanoid_set/2Hand Bow.glb'
clips=['2HandBowIdle','2HandBowWalk','2HandBowAttack1','2HandBowAttack2','2HandBowGetHitF1','2HandBowDeath1']
for view in ['front','left','three_quarter']:
    sys.argv=['rpg_preview.py','--',str(source),str(p/'review/g1'/view),view,'6',*clips]
    runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['source_rest.py','--',str(source)]
runpy.run_path(str(p/'scripts/source_rest.py'),run_name='__main__')
sys.argv=['rom_extract.py','--',*[role+'='+str(source)+':'+clip for role,clip in zip(['Standing','Walking','Attack','AttackAlternative','Hit','Death'],clips)]]
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
