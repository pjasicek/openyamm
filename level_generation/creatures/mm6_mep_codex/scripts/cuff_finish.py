import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];runpy.run_path(str(p/'scripts/open_cuffs.py'),run_name='__main__');os.environ['GATE_BLEND']='work/textured.blend';os.environ['GATE_REPORT']='review/final_dense_gates.json'
for n in ['dense_gates.py','cloth_surface_gate.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
