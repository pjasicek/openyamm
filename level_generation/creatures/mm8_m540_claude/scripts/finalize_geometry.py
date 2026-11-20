from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for s in ['finish_full_floor.py','reduce_and_upload.py','check_reduced_actions.py']:runpy.run_path(str(p/s),run_name='__main__')
