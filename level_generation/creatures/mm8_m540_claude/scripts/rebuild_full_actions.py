from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for s in ['author_full_actions.py','fit_full_cloth.py','fit_garment_finish.py','finish_full_floor.py','check_full_actions.py']:runpy.run_path(str(p/s),run_name='__main__')
