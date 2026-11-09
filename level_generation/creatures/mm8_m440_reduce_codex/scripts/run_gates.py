import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['gates','--',str(p/'export/mm8_m440.glb'),'--config',str(p/'candidate.gates.json'),'--out',str(p/'review/gates')]
runpy.run_path(str(p.parent/'claude_shared/gates/run_gates.py'),run_name='__main__')
