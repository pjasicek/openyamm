from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2];e=p/'export';shared=p.parent/'claude_shared'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(p/'scripts/shrink_shadow_lods.py',e/'mm8_m476_lods.glb',e/'mm8_m476_shadow.glb')
run(shared/'region_variants.py',e/'mm8_m476_shadow.glb',e/'mm8_m476.glb',p/'textures/troll_ramps.json','--extra','Troll','openyamm_specular=1','--extra','Troll','openyamm_specular_mask=true','--extra','Troll','pbr.metallicFactor=0','--extra','Club','openyamm_specular=1','--extra','Club','openyamm_specular_mask=true','--extra','Club','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',e/'mm8_m476.glb','--joint','Club','--body',e/'mm8_m476.glb','--attachment',e/'mm8_m476_club.glb')
run(repo/'tools/merge_head_material.py',e/'mm8_m476.glb',e/'mm8_m476.glb')
run(p/'scripts/fix_lod_winding.py',e/'mm8_m476.glb')
run(repo/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py',e/'mm8_m476.glb',e/'mm8_m476_club.glb')
run(repo/'tools/normal_map_convention.py','--check',e/'mm8_m476.glb',e/'mm8_m476_club.glb')
