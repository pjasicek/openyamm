from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'round1_silhouette_fit.py'))
runpy.run_path(str(p/'round1_local_smooth.py'))
