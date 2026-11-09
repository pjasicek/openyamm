import runpy,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent
subprocess.run(['/usr/bin/python3',str(p/'compose_textures.py')],check=True)
for name in ['export_model.py','audit_final.py','finish_runtime.py']:runpy.run_path(str(p/name),run_name='__main__')
