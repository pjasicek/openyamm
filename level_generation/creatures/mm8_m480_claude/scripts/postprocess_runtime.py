from pathlib import Path
import subprocess,sys,shutil
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=repo,check=True)
run(p/'scripts/shrink_shadow_lods.py',p/'export/mm8_m480_lods.glb',p/'export/mm8_m480_shadow.glb')
run(repo/'level_generation/creatures/claude_shared/region_variants.py',p/'export/mm8_m480_shadow.glb',p/'export/mm8_m480.glb',p/'textures/m480_ramps.json','--extra','Troll','openyamm_specular=1','--extra','Troll','openyamm_specular_mask=true','--extra','Troll','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',p/'export/mm8_m480.glb','--joint','Club','--body',p/'export/mm8_m480.glb','--attachment',p/'export/mm8_m480_club.glb')
run(repo/'tools/merge_head_material.py',p/'export/mm8_m480.glb',p/'export/mm8_m480.glb')
