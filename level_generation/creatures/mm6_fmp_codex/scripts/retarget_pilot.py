import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/weights_fmp.py'),run_name='__main__')
sys.argv=['retarget.py','--',str(p/'work/rig_weighted.blend'),str(p/'work/motion_base.blend'),*[f'anim_library/humanoid_set/Relax.glb:{clip}:{role}' for role,clip in [('Standing','RelaxIdle'),('Walking','RelaxWalkForward'),('Run','RelaxRunForward'),('Death','RelaxLaydownLayDown')]]]
runpy.run_path(str(p/'scripts/retarget.py'),run_name='__main__')
for view in ('front','left'):
 sys.argv=['clip_sheet.py','--',str(p/'work/motion_base.blend'),str(p/'review'/('pilot_'+view)),view,'5','Standing','Walking','Run','Death']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
