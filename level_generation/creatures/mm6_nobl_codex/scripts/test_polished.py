import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parent
sys.path.insert(0,str(p))
for n in ['polish_arm_weights.py','preview_compensated.py']:runpy.run_path(str(p/n),run_name='__main__')
