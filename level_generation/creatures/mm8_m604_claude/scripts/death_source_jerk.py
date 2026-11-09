from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for file in ['work/texture_master.blend','work/ready_motion.blend','work/ready_final.blend']:
 print('DEATH JERK',file)
 sys.argv=['jerk','--',str(p/file),'Death'];runpy.run_path(str(p/'scripts/jerk_probe.py'),run_name='__main__')
