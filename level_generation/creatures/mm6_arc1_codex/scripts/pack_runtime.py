import subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';R=P.parents[2]
commands=[
 [sys.executable,str(P/'scripts/shrink_shadow_lods.py'),str(E/'mm6_arc1_lods.glb'),str(E/'mm6_arc1_lods_shadowfix.glb')],
 [sys.executable,str(P.parent/'claude_shared/region_variants.py'),str(E/'mm6_arc1_lods_shadowfix.glb'),str(E/'mm6_arc1.glb'),str(P/'textures/arc1_ramps.json'),'--extra','Archer','openyamm_specular=1','--extra','Archer','openyamm_specular_mask=true','--extra','Archer','pbr.metallicFactor=0','--extra','Bow','openyamm_specular=1','--extra','Bow','openyamm_specular_mask=true','--extra','Bow','pbr.metallicFactor=0'],
 [sys.executable,str(R/'tools/split_attachment.py'),str(E/'mm6_arc1.glb'),'--joint','Bow','--body',str(E/'mm6_arc1.glb'),'--attachment',str(E/'mm6_arc1_bow.glb')],
 [sys.executable,str(R/'tools/split_attachment.py'),str(E/'mm6_arc1.glb'),'--joint','Arrow','--body',str(E/'mm6_arc1.glb'),'--attachment',str(E/'mm6_arc1_arrow.glb')],
 [sys.executable,str(R/'tools/merge_head_material.py'),str(E/'mm6_arc1.glb'),str(E/'mm6_arc1.glb')],
 [sys.executable,str(P/'scripts/viewer_tiers.py')],
 [sys.executable,str(P/'scripts/viewer_manifest.py')]]
for cmd in commands:subprocess.run(cmd,check=True)
