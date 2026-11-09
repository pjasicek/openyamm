from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=['run_gates.py',str(p/'export/mm8_m456.glb'),'--config',str(p/'gates.json'),'--out',str(p/'review/gates')]
runpy.run_path(str(p.parent/'claude_shared/gates/run_gates.py'),run_name='__main__')
