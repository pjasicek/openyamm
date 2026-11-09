"""Runtime GLB in three steps: (1) `build_runtime.py prepare`: normal convention, export/mm7_m182_lod0.glb ->
mm7_m182_prepared.glb; (2) Blender scripts/build_lods.py: colour + shadow LODs -> mm7_m182_lods.glb; (3)
`build_runtime.py finish`: shadow LODs tucked inside the surface, tier variants m182_a/b/c (shared images, region
ramps) -> export/mm7_m182.glb."""
import subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; E = P / 'export'; REPO = P.parents[2]
sys.path.insert(0, str(REPO / 'tools')); sys.path.insert(0, str(P.parent / 'claude_shared'))
if sys.argv[1] == 'prepare':
    from prepare_actor_glb import prepare
    prepare(E / 'mm7_m182_lod0.glb', E / 'mm7_m182_prepared.glb')
else:
    from region_variants import apply_variants
    subprocess.run([sys.executable, str(P / 'scripts/shrink_shadow_lods.py'), str(E / 'mm7_m182_lods.glb'), str(E / 'mm7_m182_lods_shadow.glb')], check=True)
    apply_variants(E / 'mm7_m182_lods_shadow.glb', E / 'mm7_m182.glb', P / 'textures/dragon_ramps.json',
                   [('Dragon_', 'openyamm_specular', 1.), ('Dragon_', 'openyamm_specular_mask', True)])
