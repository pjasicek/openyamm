import runpy,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
subprocess.run(['/usr/bin/python3',str(p/'scripts/pack_runtime.py')],check=True)
notes=(p/'integration/playbook_notes.md').read_text()
subprocess.run(['/usr/bin/python3',str(p/'scripts/prepare_review.py')],check=True)
(p/'integration/playbook_notes.md').write_text(notes)
runpy.run_path(str(p/'scripts/round1_gate_regions.py'),run_name='__main__')
