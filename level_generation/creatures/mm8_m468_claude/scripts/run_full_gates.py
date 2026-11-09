import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['gates','--',str(p/'export/m468_full.glb'),'--config',str(p/'gates.json'),'--out',str(p/'review/full_gates')]
runpy.run_path(str(p.parents[2]/'level_generation/creatures/claude_shared/gates/run_gates.py'),run_name='__main__')
