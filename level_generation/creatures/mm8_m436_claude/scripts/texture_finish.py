from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
for n in ['sync_motion.py','export_reduced.py','transfer_textures.py','validate_uv.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
