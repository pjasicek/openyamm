from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/clip_timing.py'),run_name='__main__')
sys.argv=['g6_contacts.py','--',str(p/'work/timed_v1.blend'),'Standing','Walking','Hit','Fidget','Death']
runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
