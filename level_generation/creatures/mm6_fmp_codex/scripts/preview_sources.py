import sys, runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for view in ('front','left'):
    sys.argv=['rpg_preview.py','--','anim_library/humanoid_set/Relax.glb',str(p/'review'/('g1_relax_'+view)),view,'4','RelaxIdle','RelaxWalkForward','RelaxWalkFemale2','RelaxWalkFemale3','RelaxRunForward','RelaxLaydownLayDown']
    runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
