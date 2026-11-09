import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for script in ['round4_author.py','round4_repair.py','round4_textures.py','round4_export_lods.py']:
 runpy.run_path(str(P/'scripts'/script),run_name='__main__')
