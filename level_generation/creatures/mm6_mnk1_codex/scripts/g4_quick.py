import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['g4_weights.py','--',str(p/'work/anim_reduced.blend'),'quick','Standing:0','Walking:8','Attack:22','Cast:15','Death:45','Dead:0']
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
