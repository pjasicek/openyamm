from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['author_motion.py','clear_settled_club.py','polish_motion.py','bake_helpers.py','motion_quality.py','gate_motion.py']:
 runpy.run_path(str(p/n),run_name='__main__')
