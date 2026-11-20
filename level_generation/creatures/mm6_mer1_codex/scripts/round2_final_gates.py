import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['run_gates.py','--',str(P/'export/mm6_mer1.glb'),'--config',str(P/'gates.json'),'--out',str(P/'review/gates')]
runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='__main__')
