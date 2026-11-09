import subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(script,*args):
 subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(p/'scripts/shrink_shadow_lods.py',p/'export/mm6_nobl_lods.glb',p/'export/mm6_nobl_lods_shadowfix.glb')
run(p.parent/'claude_shared/region_variants.py',p/'export/mm6_nobl_lods_shadowfix.glb',p/'export/mm6_nobl.glb',p/'textures/nobl_ramps.json','--extra','Swordsman','openyamm_specular=1','--extra','Swordsman','openyamm_specular_mask=true','--extra','Swordsman','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',p/'export/mm6_nobl.glb','--joint','Sword','--body',p/'export/mm6_nobl.glb','--attachment',p/'export/mm6_nobl_sword.glb')
run(repo/'tools/merge_head_material.py',p/'export/mm6_nobl.glb',p/'export/mm6_nobl.glb')
run(p/'scripts/viewer_tiers.py')
run(p/'scripts/update_viewer_manifest.py')
