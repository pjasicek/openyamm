from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for view in ['front','left','three_quarter']:
 sys.argv=['set_preview.py','--',str(p.parents[2]/'anim_library/humanoid_set/Armed.glb'),str(p/'review/source_motion/Fidget'/view),view,'9','ArmedIdleAlert1']
 runpy.run_path(str(p/'scripts/set_preview.py'),run_name='__main__')
