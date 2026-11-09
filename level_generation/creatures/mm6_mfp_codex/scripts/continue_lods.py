import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for script in ['stride_fit.py','update_selected_motion.py','reduction_search_soft.py']:runpy.run_path(str(P/script),run_name='__main__')
