"""Import and inspect the recorded Smart Topology return in an isolated scene."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
source = p / 'meshy/smart_topology_v1/model_urls_glb.glb'
assert source.is_file()
script = p / 'scripts/examine_parts.py'
sys.argv = [str(script), '--', str(source), 'st_v1']
runpy.run_path(str(script), run_name='__main__')
