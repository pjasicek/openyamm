from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/ground_motion.py'),run_name='__main__')
s=p/'scripts/robe_sim.py';sys.argv=[str(s),'--',str(p/'work/motion_grounded.blend'),str(p/'work/motion_robed.blend')]
runpy.run_path(str(s),run_name='__main__')
