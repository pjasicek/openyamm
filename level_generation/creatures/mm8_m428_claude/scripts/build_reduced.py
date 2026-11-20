"""Installed runtime = the reduction (../mm8_m428_reduce_claude/, README "Build") applied to this project's current
production export: swap_lod0.py puts the reduced LOD0 geometry (work/cand_export.glb, same skeleton and bind space)
into export/mm8_m428.glb (new clips, materials, variants), then that project's build_lods.py (protected crown and
Death floor points), the production shrink_shadow_lods.py and carry_variants.py write
../mm8_m428_reduce_claude/export/mm8_m428.glb. Run after build_runtime.py, with plain python3."""
import subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; R = P.parents[2]; Q = P.parent / 'mm8_m428_reduce_claude'
def run(*a):
    print('RUN', ' '.join(str(x) for x in a)); subprocess.run([str(x) for x in a], check=True, cwd=R)
run(sys.executable, Q / 'scripts/swap_lod0.py', P / 'export/mm8_m428.glb', Q / 'work/cand_export.glb', Q / 'work/pick_lod0.glb', 'M428')
run('/snap/bin/blender', '--background', '--factory-startup', '--disable-autoexec', '--threads', '4', '--python-exit-code', '1',
    '--python', Q / 'scripts/build_lods.py')
run(sys.executable, P / 'scripts/shrink_shadow_lods.py', Q / 'work/pick_lods.glb', Q / 'export/mm8_m428.glb')
run(sys.executable, Q / 'scripts/carry_variants.py', Q / 'export/mm8_m428.glb')
