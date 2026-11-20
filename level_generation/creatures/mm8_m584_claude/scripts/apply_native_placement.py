from pathlib import Path
import runpy,json
P=Path(__file__).resolve().parents[1]
for name in ['hover_height.py','inspect_animation.py','contacts.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
report=json.loads((P/'work/contacts_final.json').read_text())
assert not any(c['contacts'] for c in report.values()),report
runpy.run_path(str(P/'scripts/export_textured.py'),run_name='__main__')
