import runpy
from pathlib import Path
p=Path(__file__).parent
for script in ['finish_animations.py','refresh_actions.py','export_ghost.py']:runpy.run_path(str(p/script),run_name='__main__')
