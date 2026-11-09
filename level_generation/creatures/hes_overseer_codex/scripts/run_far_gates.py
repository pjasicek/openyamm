import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
shared=P.parent/'claude_shared/gates/run_gates.py'
sys.argv=[str(shared),str(P/'review/lods/hes_overseer/lod3.glb'),'--config',str(P/'gates_far_final.json'),'--out',str(P/'review/gates_far_final')]
runpy.run_path(str(shared),run_name='__main__')
