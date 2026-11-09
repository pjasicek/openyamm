from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for n in ['transfer_textures.py','diagnose_uv.py','repair_uv.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
