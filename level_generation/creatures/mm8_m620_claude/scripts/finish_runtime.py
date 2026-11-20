from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2];e=p/'export';shared=p.parent/'claude_shared'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(p/'scripts/shrink_shadow_lods.py',e/'mm8_m620_lods.glb',e/'mm8_m620_shadow.glb')
run(shared/'region_variants.py',e/'mm8_m620_shadow.glb',e/'mm8_m620.glb',p/'textures/bedraggled_ramps.json','--extra','Bedraggled','openyamm_specular=1','--extra','Bedraggled','openyamm_specular_mask=true','--extra','Bedraggled','pbr.metallicFactor=1')
run(repo/'tools/merge_head_material.py',e/'mm8_m620.glb',e/'mm8_m620.glb')
run(p/'scripts/fix_lod_winding.py',e/'mm8_m620.glb')
run(repo/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py',e/'mm8_m620.glb')
run(repo/'tools/normal_map_convention.py','--check',e/'mm8_m620.glb')
