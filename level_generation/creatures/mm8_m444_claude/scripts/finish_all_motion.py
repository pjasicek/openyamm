from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for name in ['fit_motion.py','weight_motion.py','finish_motion.py','check_motion.py']:
 sys.argv=[str(p/'scripts'/name)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
