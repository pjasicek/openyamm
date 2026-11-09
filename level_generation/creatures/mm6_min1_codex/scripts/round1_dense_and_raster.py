from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_curve_dense.py'))
runpy.run_path(str(p/'round1_curve_timing.py'))
runpy.run_path(str(p/'round1_raster_fit.py'))
