import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['run_gates.py','--',str(p/'export/mm8_m412.glb'),'--config',str(p/'gates.json'),'--out',str(p/'review/gates_contacts')]
runpy.run_path(str(p.parent/'claude_shared/gates/run_gates.py'),run_name='__main__')
