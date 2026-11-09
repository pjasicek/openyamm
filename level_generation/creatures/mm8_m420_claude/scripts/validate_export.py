from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for n in ['settle_final.py','export_final_lods.py','deformation_gates.py']:runpy.run_path(str(P/n),run_name='__main__')
