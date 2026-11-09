import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/pilot_gates.py'),run_name='__main__')
sys.argv=['jerk_probe.py','--',str(P/'work/motion_mixamo.blend'),'Walking','Running','Death']
print('SOURCE MOTION COMPARISON',flush=True)
runpy.run_path(str(P/'scripts/jerk_probe.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/hand_review.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/contacts.py'),run_name='__main__')
