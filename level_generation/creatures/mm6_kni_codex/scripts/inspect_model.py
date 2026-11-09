import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p)
sys.argv=["examine_parts.py","--","meshy/smart_topology_v1/model_urls_glb.glb","st_v1"]
runpy.run_path(str(p/"scripts/examine_parts.py"),run_name="__main__")
