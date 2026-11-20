import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/ground_feet.py'),run_name='__main__')
sys.argv=['g4_weights.py','--',str(p/'work/pilots_twist.blend'),'death_locate','Death:45']
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
