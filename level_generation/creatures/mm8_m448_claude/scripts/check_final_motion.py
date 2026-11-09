from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
acts=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
os.environ['STEP']='0.5'
for script in ('sole_probe.py','jerk_probe.py','g6_ratman.py'):
    sys.argv=[script,'--',str(p/'work/rig_reduced.blend')]+acts
    runpy.run_path(str(p/'scripts'/script),run_name='__main__')
runpy.run_path(str(p/'scripts/review_final_motion.py'),run_name='__main__')
