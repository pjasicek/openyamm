import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/finish_master.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/search_reduction.py'),run_name='__main__')
