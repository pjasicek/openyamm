from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=repo,check=True)
run(p/'scripts/shrink_shadow_lods.py',p/'export/mm8_m604_lods.glb',p/'export/mm8_m604_shadow.glb')
run(repo/'level_generation/creatures/claude_shared/region_variants.py',p/'export/mm8_m604_shadow.glb',p/'export/mm8_m604.glb',p/'textures/m604_ramps.json','--extra','EtherKnight','openyamm_specular=1','--extra','EtherKnight','openyamm_specular_mask=true','--extra','EtherKnight','pbr.metallicFactor=0','--extra','Sword','openyamm_specular=1','--extra','Sword','openyamm_specular_mask=true','--extra','Sword','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',p/'export/mm8_m604.glb','--joint','Sword','--body',p/'export/mm8_m604.glb','--attachment',p/'export/mm8_m604_sword.glb')
run(repo/'tools/merge_head_material.py',p/'export/mm8_m604.glb',p/'export/mm8_m604.glb')
