from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=repo,check=True)
run(p/'scripts/shrink_shadow_lods.py',p/'export/mm8_ratman_lods.glb',p/'export/mm8_ratman_shadow.glb')
run(repo/'level_generation/creatures/claude_shared/region_variants.py',p/'export/mm8_ratman_shadow.glb',p/'export/mm8_ratman.glb',p/'textures/ratman_ramps.json','--extra','Ratman','openyamm_specular=1','--extra','Ratman','openyamm_specular_mask=true','--extra','Ratman','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',p/'export/mm8_ratman.glb','--joint','Sword','--body',p/'export/mm8_ratman.glb','--attachment',p/'export/mm8_ratman_sword.glb')
run(repo/'tools/merge_head_material.py',p/'export/mm8_ratman.glb',p/'export/mm8_ratman.glb')
