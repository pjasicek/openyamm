import runpy,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'bake_ao.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(p/'compose_textures.py')],check=True)
runpy.run_path(str(p/'export_model.py'),run_name='__main__')
