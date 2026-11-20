from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ("author_clips.py","finish_clay.py","check_twist.py"):
 runpy.run_path(str(p/"scripts"/name),run_name="__main__")
