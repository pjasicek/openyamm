from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
runpy.run_path(str(p.parents[2]/'tools/test_build_actor_lod_seams.py'),run_name='__main__')
