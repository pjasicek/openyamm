"""Existing runtime passes: corrected shadows, tier ramps, rigid prop split, merged head."""
from pathlib import Path
import sys,subprocess,runpy,json,hashlib
P=Path(__file__).resolve().parents[1];E=P/'export';ROOT=P.parents[2]
sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import apply_variants
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m568_lods.glb'),str(E/'mm8_m568_lods_shrunk.glb')]
runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
apply_variants(E/'mm8_m568_lods_shrunk.glb',E/'mm8_m568_combined.glb',P/'textures/m568_ramps.json',[('Salamander','openyamm_specular',1.),('Salamander','openyamm_specular_mask',True)])
def tool(name,*args):subprocess.run([sys.executable,str(ROOT/'tools'/name),*map(str,args)],check=True)
tool('split_attachment.py',E/'mm8_m568_combined.glb','--joint','Polearm','--body',E/'mm8_m568.glb','--attachment',E/'mm8_m568_polearm.glb')
tool('merge_head_material.py',E/'mm8_m568.glb',E/'mm8_m568.glb')
for f in ['mm8_m568.glb','mm8_m568_polearm.glb']:
 subprocess.run([sys.executable,str(ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),str(E/f)],check=True)
print('RUNTIME EXPORTS READY',flush=True)
