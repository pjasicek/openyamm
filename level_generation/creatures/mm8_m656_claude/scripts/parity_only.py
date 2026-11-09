import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).parent/'export_parity.py'),run_name='__main__')
