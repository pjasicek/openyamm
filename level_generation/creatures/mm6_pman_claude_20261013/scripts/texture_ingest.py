import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['transfer_textures.py','repair_head_uv.py','bake_ao.py']:runpy.run_path(str(p/name),run_name='__main__')
