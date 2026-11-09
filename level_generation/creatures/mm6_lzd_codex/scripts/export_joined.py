import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/string_join_gate.py'),run_name='__main__',init_globals={'GATE_BLEND':P/'work/rebake/final0_baked.blend'})
runpy.run_path(str(P/'scripts/export_rebaked.py'),run_name='__main__')
