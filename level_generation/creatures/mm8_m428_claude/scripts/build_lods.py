"""Blender: tools/build_actor_lods.py on the prepared LOD0 (4 influences, default ratios)."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; R = P.parents[2]
sys.argv = ['build_actor_lods.py', str(P / 'export/mm8_m428_runtime_lod0.glb'), str(P / 'export/mm8_m428_lods.glb'),
            '--mesh-node', 'M428', '--max-influences', '4']
runpy.run_path(str(R / 'tools/build_actor_lods.py'), run_name='__main__')
