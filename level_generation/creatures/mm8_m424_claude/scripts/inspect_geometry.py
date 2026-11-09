"""Inspect the downloaded geometry and record the source proportions."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
sys.argv = ['proportions.py', '--', 'source', str(p.parents[2] / 'anim_library/humanoid_set/Relax.glb')]
runpy.run_path(str(p / 'scripts/proportions.py'), run_name='__main__')
sys.argv = ['examine_parts.py', '--', str(p / 'meshy/smart_topology_v1/model_urls_glb.glb'), 'st_v1']
runpy.run_path(str(p / 'scripts/examine_parts.py'), run_name='__main__')
