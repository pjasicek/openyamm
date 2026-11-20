import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['compare_exported_lods.py','cloth_surface_gate.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
