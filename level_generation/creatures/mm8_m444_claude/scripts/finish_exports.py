"""Finish engine and preview exports after export_runtime.py, prepare_actor_glb.py and export_lods.py."""
from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];r=p.parents[2];e=p/'export'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(p/'scripts/shrink_shadow_lods.py',e/'mm8_m444_lods.glb',e/'mm8_m444_shadowfix.glb')
run(p.parent/'claude_shared/region_variants.py',e/'mm8_m444_shadowfix.glb',e/'mm8_m444.glb',p/'textures/smuggler_ramps.json','--extra','Smuggler','openyamm_specular=1','--extra','Smuggler','openyamm_specular_mask=true','--extra','Smuggler','pbr.metallicFactor=0')
run(r/'tools/split_attachment.py',e/'mm8_m444.glb','--joint','Sword','--body',e/'mm8_m444.glb','--attachment',e/'mm8_m444_sword.glb')
run(r/'tools/merge_head_material.py',e/'mm8_m444.glb',e/'mm8_m444.glb')
run(p/'scripts/viewer_tiers.py')
