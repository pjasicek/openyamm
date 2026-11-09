from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['fit_body.py','robe_rig.py']:runpy.run_path(str(p/n),run_name='__main__')
