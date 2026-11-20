import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['rom_extract.py','--','Standing=anim_library/humanoid_set/Relax.glb:RelaxIdle','Walking=anim_library/humanoid_set/Relax.glb:RelaxWalkForward','Run=anim_library/humanoid_set/Relax.glb:RelaxRunForward','Death=anim_library/humanoid_set/Relax.glb:RelaxLaydownLayDown']
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
sys.argv=['rpg_preview.py','--','anim_library/humanoid_set/Relax.glb',str(p/'review/g1_selected_three_quarter'),'three_quarter','5','RelaxIdle','RelaxWalkForward','RelaxRunForward','RelaxLaydownLayDown']
runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
