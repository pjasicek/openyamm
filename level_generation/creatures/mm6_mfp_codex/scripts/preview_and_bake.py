import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['preview_death_mixamo.py','bake_textures.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
