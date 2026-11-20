import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['round2_fit.py','round2_head_uv.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round2_textures.py')],check=True)
for name in ['round2_apply.py','render_final.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
