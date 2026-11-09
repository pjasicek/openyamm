from pathlib import Path
import runpy,json
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/contacts.py'),run_name='__main__')
report=json.loads((P/'work/contacts_final.json').read_text())
assert not any(c['contacts'] for c in report.values()),report
runpy.run_path(str(P/'scripts/review_motion.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_uploads.py'),run_name='__main__')
