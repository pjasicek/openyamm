import sys, runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for view in ('front','left','three_quarter'):
    sys.argv=['rpg_preview.py','--',str(Path('anim_library/humanoid_set/Relax.glb').resolve()),str(p/'review/g1'/view),view,'5','RelaxIdle','RelaxWalkFemale2','RelaxWalkFemale3','RelaxWalkForward','RelaxLaydownLayDown']
    runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
