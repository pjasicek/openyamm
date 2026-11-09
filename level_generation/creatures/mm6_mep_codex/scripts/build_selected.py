import json,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/fit_contact_lods.py'),run_name='__main__')
rows=json.loads((p/'review/reduction/contact_selected_curve.json').read_text());assert all(r['pass'] for r in rows)
for kind in ['dense','physical']:
 d=json.loads((p/f'review/reduction/contact_selected_body_3_{kind}.json').read_text());assert all(v for row in d.values() for k,v in row.items() if k.endswith('pass'))
c=json.loads((p/'review/reduction/contact_selected_body_3_cloth.json').read_text())['clips'];assert all(row['pass'] for row in c.values())
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
