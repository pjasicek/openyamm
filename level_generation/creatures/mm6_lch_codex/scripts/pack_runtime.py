"""Pack the already-exported LODs and refresh the local tier viewer; never install."""
import subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';repo=P.parents[2]
cmds=[
 [sys.executable,str(P/'scripts/shrink_shadow_lods.py'),str(E/'mm6_lch_lods.glb'),str(E/'mm6_lch_lods_shadowfix.glb')],
 [sys.executable,str(P.parent/'claude_shared/region_variants.py'),str(E/'mm6_lch_lods_shadowfix.glb'),str(E/'mm6_lch.glb'),str(P/'textures/lch_ramps.json'),'--extra','Lich','openyamm_specular=1','--extra','Lich','openyamm_specular_mask=true','--extra','Lich','pbr.metallicFactor=0'],
 [sys.executable,str(repo/'tools/merge_head_material.py'),str(E/'mm6_lch.glb'),str(E/'mm6_lch.glb')],
 [sys.executable,str(P/'scripts/viewer_tiers.py')],
 [sys.executable,str(P/'scripts/update_viewer_manifest.py')]]
for cmd in cmds:subprocess.run(cmd,check=True)
