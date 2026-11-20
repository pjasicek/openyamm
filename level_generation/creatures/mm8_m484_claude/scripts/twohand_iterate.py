from pathlib import Path
import runpy
P=Path(__file__).resolve().parents[1]
for n in ['twohand_source.py','fit_twohand.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
