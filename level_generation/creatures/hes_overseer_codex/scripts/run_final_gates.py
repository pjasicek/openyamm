import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
shared=P.parent/'claude_shared/gates/run_gates.py'
sys.argv=[str(shared),str(P/'export/hes_overseer.glb'),'--config',str(P/'gates_final.json'),'--out',str(P/'review/gates_final')]
runpy.run_path(str(shared),run_name='__main__')
