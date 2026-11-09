from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_runtime_lod3.py'))
runpy.run_path(str(p/'round1_collision_curve.py'))
