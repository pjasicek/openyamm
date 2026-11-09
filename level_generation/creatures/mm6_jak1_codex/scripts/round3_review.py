import runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent
runpy.run_path(str(S/'round3_panel_gate.py'),run_name='__main__')
runpy.run_path(str(S/'render_final.py'),run_name='__main__')
