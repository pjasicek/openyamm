import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round2_surface_probe.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round2_head_uv.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round2_textures.py')],check=True)
runpy.run_path(str(P/'scripts/round2_head_preview.py'),run_name='__main__')
