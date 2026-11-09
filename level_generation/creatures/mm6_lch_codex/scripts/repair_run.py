import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for s in ["finish_clips.py","gate_reduce.py","gates_upload_run.py"]:runpy.run_path(str(P/"scripts"/s),run_name="__main__")
