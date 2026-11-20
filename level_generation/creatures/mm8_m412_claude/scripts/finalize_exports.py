"""Build the runtime palette materials and separate prop from the LOD export."""
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1];E=P/'export';repo=P.parents[2]
def run(*a):subprocess.run(['python3',*map(str,a)],check=True)
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m412_lods.glb',E/'mm8_m412.glb',P/'textures/pirate_ramps.json','--extra','Pirate','openyamm_specular=1','--extra','Pirate','openyamm_specular_mask=true','--extra','Pirate','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',E/'mm8_m412.glb','--joint','Sword','--body',E/'mm8_m412.glb','--attachment',E/'mm8_m412_cutlass.glb')
run(repo/'tools/merge_head_material.py',E/'mm8_m412.glb',E/'mm8_m412.glb')
