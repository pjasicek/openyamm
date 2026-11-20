"""Assemble the shared runtime material, shadow and attachment contracts."""
from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(script,*args):subprocess.run([sys.executable,str(script),*[str(v) for v in args]],check=True)
e=p/'export'
run(p/'scripts/fit_lod_soles.py',e/'mm8_m520_lods.glb',e/'mm8_m520_lods_fitted.glb')
run(p/'scripts/shrink_shadow_lods.py',e/'mm8_m520_lods_fitted.glb',e/'mm8_m520_lods_shadowfix.glb')
run(p.parent/'claude_shared/region_variants.py',e/'mm8_m520_lods_shadowfix.glb',e/'mm8_m520.glb',p/'textures/m520_ramps.json',
    '--extra','Cyclops','openyamm_specular=1','--extra','Cyclops','openyamm_specular_mask=true',
    '--extra','Boulder','openyamm_specular=1','--extra','Boulder','openyamm_specular_mask=true')
run(repo/'tools/split_attachment.py',e/'mm8_m520.glb','--joint','Boulder','--body',e/'mm8_m520.glb','--attachment',e/'mm8_m520_boulder.glb')
run(repo/'tools/merge_head_material.py',e/'mm8_m520.glb',e/'mm8_m520.glb')
run(p/'scripts/viewer_tiers.py')
