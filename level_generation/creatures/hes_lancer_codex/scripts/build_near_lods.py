"""Keep the prepared LOD0 and animation bytes; use the repository's colour/shadow LOD builder."""
from pathlib import Path
import runpy
import sys
import bpy

P = Path(__file__).resolve().parents[1]
builder = P.parents[2] / 'tools/build_actor_lods.py'
names = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['hes_lancer','hes_lancer_twin']
for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sys.argv = [str(builder), '--', str(P / f'work/{name}_runtime_lod0.glb'),
                str(P / f'work/{name}_lods.glb'), '--mesh-node', 'Lancer', '--max-influences', '4']
    runpy.run_path(str(builder), run_name='__main__')

import os
sys.stdout.flush();os._exit(0)
