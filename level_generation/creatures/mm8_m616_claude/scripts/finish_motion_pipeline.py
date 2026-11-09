import runpy
from pathlib import Path
p=Path(__file__).parent
for n in ['animate_bone_dragon.py','prepare_texture.py']:runpy.run_path(str(p/n),run_name='__main__')
