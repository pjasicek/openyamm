import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round1_export_pose.py'))
runpy.run_path(str(P/'scripts/render_final.py'))
