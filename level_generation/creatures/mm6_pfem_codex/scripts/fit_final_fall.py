import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in ('review_body_clips.py','build_skirt.py','death_skirt_envelope.py','audit_skirt.py'):
 runpy.run_path(str(p/'scripts'/n),run_name='__main__')
