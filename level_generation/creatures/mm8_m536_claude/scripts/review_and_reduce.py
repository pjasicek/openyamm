import runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/review_assembly.py'),run_name='__main__')
for step in range(1,4):
 (P/'review/reduction/next_step.json').write_text(json.dumps({'step':step}))
 runpy.run_path(str(P/'scripts/reduce_step.py'),run_name='__main__')
