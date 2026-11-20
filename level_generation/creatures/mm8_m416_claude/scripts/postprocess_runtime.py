from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=repo,check=True)
run(p/'scripts/shrink_shadow_lods.py',p/'export/mm8_m416_lods.glb',p/'export/mm8_m416_shadow.glb')
run(repo/'level_generation/creatures/claude_shared/region_variants.py',p/'export/mm8_m416_shadow.glb',p/'export/mm8_m416.glb',p/'textures/m416_ramps.json','--extra','PirateCrossbowwoman','openyamm_specular=1','--extra','PirateCrossbowwoman','openyamm_specular_mask=true','--extra','PirateCrossbowwoman','pbr.metallicFactor=0','--extra','Crossbow','openyamm_specular=1','--extra','Crossbow','openyamm_specular_mask=true','--extra','Crossbow','pbr.metallicFactor=0','--extra','Quiver','openyamm_specular=1','--extra','Quiver','openyamm_specular_mask=true','--extra','Quiver','pbr.metallicFactor=0','--extra','BowString','openyamm_specular=1','--extra','BowString','openyamm_specular_mask=true','--extra','BowString','pbr.metallicFactor=0')
import shutil
shutil.copy2(p/'export/mm8_m416.glb',p/'export/mm8_m416_portable.glb')
run(repo/'tools/merge_head_material.py',p/'export/mm8_m416_portable.glb',p/'export/mm8_m416_portable.glb')
for joint,stem in [('Crossbow','crossbow'),('Bolt','bolt'),('Quiver','quiver'),('StringL','string_l'),('StringR','string_r')]:
 run(repo/'tools/split_attachment.py',p/'export/mm8_m416.glb','--joint',joint,'--body',p/'export/mm8_m416.glb','--attachment',p/f'export/mm8_m416_{stem}.glb')
run(repo/'tools/merge_head_material.py',p/'export/mm8_m416.glb',p/'export/mm8_m416.glb')
