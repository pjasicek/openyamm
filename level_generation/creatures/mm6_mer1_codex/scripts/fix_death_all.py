import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['fix_death_leg.py','fix_death_surface.py','check_final_cloth.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
