from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['bake_maps.py','sync_motion.py']:
 runpy.run_path(str(p/n),run_name='__main__')
