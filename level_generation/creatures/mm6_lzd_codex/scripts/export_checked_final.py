import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.argv=['gate','--',str(P/'work/rebake/final0_baked.blend')];runpy.run_path(str(P/'scripts/round3_gates.py'),run_name='__main__');assert json.loads((P/'review/round3_motion_gate.json').read_text())['passed'];runpy.run_path(str(P/'scripts/export_rebaked.py'),run_name='__main__')
