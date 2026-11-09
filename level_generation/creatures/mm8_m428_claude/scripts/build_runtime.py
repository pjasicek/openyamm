"""Runtime GLB from the textured LOD0 export (adapted from mm8_m424_claude/scripts/{build_lods,finish_runtime}.py):
prepare_actor_glb (normal-map convention) -> build_actor_lods (4 influences, defaults 0.5/0.18/0.06) ->
shrink_shadow_lods -> region_variants (three tiers sharing every image, dress ramps, specular mask, metallic 0) ->
merge_head_material (2080x1024 body|head atlas, one draw). No attachment split: the body carries no dagger mesh;
actors.yml attaches the installed male dagger to the Dagger bone. Writes export/mm8_m428.glb. Run with plain python3."""
import subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; R = P.parents[2]; E = P / 'export'; S = P / 'scripts'
def run(*a):
    print('RUN', ' '.join(str(x) for x in a)); subprocess.run([str(x) for x in a], check=True, cwd=R)
run(sys.executable, R / 'tools/prepare_actor_glb.py', E / 'mm8_m428_lod0.glb', E / 'mm8_m428_runtime_lod0.glb')
run('/snap/bin/blender', '--background', '--factory-startup', '--disable-autoexec', '--threads', '4',
    '--python-exit-code', '1', '--python', S / 'build_lods.py')
run(sys.executable, S / 'shrink_shadow_lods.py', E / 'mm8_m428_lods.glb', E / 'mm8_m428_lods_shadowfix.glb')
run(sys.executable, P.parent / 'claude_shared/region_variants.py', E / 'mm8_m428_lods_shadowfix.glb', E / 'mm8_m428.glb',
    P / 'textures/m428_ramps.json', '--extra', 'M428', 'openyamm_specular=1', '--extra', 'M428',
    'openyamm_specular_mask=true', '--extra', 'M428', 'pbr.metallicFactor=0')
run(sys.executable, R / 'tools/merge_head_material.py', E / 'mm8_m428.glb', E / 'mm8_m428.glb')
