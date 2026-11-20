import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['contact_fix.py','--',str(P/'work/gate_repair_helpers.blend'),str(P/'work/master_textured_uv.blend')];runpy.run_path(str(P/'scripts/contact_fix.py'),run_name='__main__')
sys.argv=['export_runtime.py'];runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
