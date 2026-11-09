"""Build the four colour levels and shared shadow chain without changing level-zero animation."""
from pathlib import Path
import sys,subprocess
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
import build_actor_lods as L
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
L.generate(P/'export/mm8_m592_runtime_lod0.glb',P/'export/mm8_m592_lods.glb','PlaneGuardian',ratios=(.5,.25,.125),max_influences=4)
def run(*a):subprocess.run([str(x) for x in a],check=True)
run('python3',P.parent/'claude_shared/region_variants.py',P/'export/mm8_m592_lods.glb',P/'export/mm8_m592.glb',P/'textures/m592_ramps.json','--extra','PlaneGuardian','openyamm_specular=1','--extra','PlaneGuardian','openyamm_specular_mask=true','--extra','PlaneGuardian','pbr.metallicFactor=0')
run('python3','tools/merge_head_material.py',P/'export/mm8_m592.glb',P/'export/mm8_m592.glb')
run('python3',P/'scripts/shrink_shadow_lods.py',P/'export/mm8_m592.glb',P/'export/mm8_m592.glb')
run('python3',P/'scripts/fix_lod_winding.py',P/'export/mm8_m592.glb')
