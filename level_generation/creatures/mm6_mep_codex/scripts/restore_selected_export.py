import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for script in ['reexport_animation.py','repair_review_actions.py']:
 runpy.run_path(str(p/'scripts'/script),run_name='__main__')
