from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_carrier_smooth.py'))
runpy.run_path(str(p/'round1_coarse_lod.py'))
