from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/check_head_look.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
