from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ['prepare_texture.py','review_uv.py','bake_ao.py']:runpy.run_path(str(P/name),run_name='__main__')
