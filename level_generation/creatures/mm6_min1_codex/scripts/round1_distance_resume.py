import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_acceleration.py'))
runpy.run_path(str(p/'round1_distance_lods.py'),init_globals={'SKIP_LOD0':True})
