from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=["examine_parts.py","--",str(p/"meshy/smart_topology_v1/model_urls_glb.glb"),"st_v1"]
runpy.run_path(str(p/"scripts/examine_parts.py"),run_name="__main__")
