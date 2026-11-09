from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ['polish_motion.py','bake_helpers.py','motion_quality.py']:
 runpy.run_path(str(p/script),run_name='__main__')
