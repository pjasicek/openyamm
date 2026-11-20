import subprocess,runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name in ['translate_head_maps.py','compose_textures.py']:subprocess.run(['python3',str(p/'scripts'/name)],check=True)
for name in ['validate_uv.py','preview_textures.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
