from pathlib import Path
import subprocess,sys
P=Path(__file__).resolve().parents[1];E=P/'export';repo=P.parents[2]
def run(*a):subprocess.run(['python3',*map(str,a)],check=True)
run(P/'scripts/shrink_shadow_lods.py',E/'mm8_m576_lods_raw.glb',E/'mm8_m576_lods.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m576_lods.glb',E/'mm8_m576.glb',P/'textures/triton_ramps.json','--extra','Triton','openyamm_specular=1','--extra','Triton','openyamm_specular_mask=true','--extra','Triton','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',E/'mm8_m576.glb','--joint','Trident','--body',E/'mm8_m576.glb','--attachment',E/'mm8_m576_trident.glb')
# A power-of-two atlas preserves both the 2K body and 1K head through the desktop cooker.
sys.path.insert(0,str(repo/'tools'));import merge_head_material
merge_head_material.GUTTER=1024
sys.argv=['merge_head_material.py',str(E/'mm8_m576.glb'),str(E/'mm8_m576.glb')]
merge_head_material.main()
