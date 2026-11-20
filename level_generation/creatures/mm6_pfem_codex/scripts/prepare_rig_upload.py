import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'step1_clean.py'),run_name='__main__')
runpy.run_path(str(p/'fit_face.py'),run_name='__main__')
