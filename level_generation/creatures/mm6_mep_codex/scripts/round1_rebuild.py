import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['round1_finish.py','round1_export.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
for name in ['finalize_runtime.py','viewer_tiers.py','prepare_review.py']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)
runpy.run_path(str(P/'scripts/render_final.py'),run_name='__main__')
