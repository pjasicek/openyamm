import json,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
contacts=json.loads((P/'review/upperarm_contacts.json').read_text())
assert max(v['depth_m'] for row in contacts.values() for v in row.values())<.002
for name in ['twohand_grip.py','final_measurements.py','export_runtime.py','verify_export.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
for source,role in [('work/gated_master.blend','Attack'),('work/twohand_source.blend','AttackTwoHandSource')]:
 sys.argv=['jerk_probe.py','--',str(P/source),role];runpy.run_path(str(P/'scripts/jerk_probe.py'),run_name='__main__')
