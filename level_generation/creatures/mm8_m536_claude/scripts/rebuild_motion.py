import runpy
from pathlib import Path
p=Path(__file__).parent
for name in ['animate_body.py','refresh_animation.py','build_effects.py','assembly_gates.py']:runpy.run_path(str(p/name),run_name='__main__')
