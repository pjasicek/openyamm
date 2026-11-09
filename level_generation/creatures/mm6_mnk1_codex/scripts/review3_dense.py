import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ['GATE_BLEND']='work/animation_finish.blend'
runpy.run_path(str(p/'scripts/gates_dense.py'),run_name='__main__')
