import runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
# Reuse protected geometry.
for step in [7,8]:
 (P/'work/round5/config.json').write_text(json.dumps({'step':step,'view_count':8,'gates':True}))
 runpy.run_path(str(P/'scripts/round5_candidate.py'),run_name='__main__')

runpy.run_path(str(P/'scripts/round5_pilot_export.py'),run_name='__main__')
