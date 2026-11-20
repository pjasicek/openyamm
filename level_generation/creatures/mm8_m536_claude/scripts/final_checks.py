import runpy
from pathlib import Path
P=Path(__file__).parent
for n in ['final_gates.py','pack_editable.py']:runpy.run_path(str(P/n),run_name='__main__')
