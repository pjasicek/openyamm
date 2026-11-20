from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ['animate_phoenix.py','reduction_pipeline.py','export_pilot.py']:
 runpy.run_path(str(P/name),run_name='__main__')
