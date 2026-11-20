from pathlib import Path
import runpy,sys,os
os.environ["CHECK_CLIPS"]="Running"
p=Path(__file__).resolve().parents[1]
for name in ['fit_motion.py','weight_motion.py','finish_motion.py','refresh_uv_actions.py','g6_smuggler.py']:
 sys.argv=[str(p/'scripts'/name)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
