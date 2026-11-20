from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parent
for n in ['author_motion.py','clear_settled_club.py','polish_motion.py','bake_helpers.py','motion_probe.py','sync_motion.py','final_mesh_checks.py']:
 sys.argv=[str(p/n)]
 runpy.run_path(str(p/n),run_name='__main__')
