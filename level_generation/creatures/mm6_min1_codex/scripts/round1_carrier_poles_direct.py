from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_carrier_poles.py'))
runpy.run_path(str(p/'round1_coarse_direct.py'))
