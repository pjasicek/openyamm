from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_curve_refine.py'))
runpy.run_path(str(p/'round1_curve_timing.py'))
runpy.run_path(str(p/'round1_inflate_lod.py'))
