from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['finish_motion.py','apply_textures.py']:runpy.run_path(str(p/name),run_name='__main__')
