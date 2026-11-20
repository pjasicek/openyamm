from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/rebuild_motion.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_parity.py'),run_name='__main__')
