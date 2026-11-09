import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[2]/"lod_repair_claude/scripts/lod_render.py"),run_name="__main__")
