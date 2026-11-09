from pathlib import Path
import sys,subprocess,runpy
P=Path(__file__).resolve().parents[1];E=P/'export';ROOT=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import apply_variants
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m516_lods.glb'),str(E/'mm8_m516_lods_shrunk.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
apply_variants(E/'mm8_m516_lods_shrunk.glb',E/'mm8_m516.glb',P/'textures/m516_ramps.json',[('ThunderLizard','openyamm_specular',1.),('ThunderLizard','openyamm_specular_mask',True)])
subprocess.run([sys.executable,str(ROOT/'tools/merge_head_material.py'),str(E/'mm8_m516.glb'),str(E/'mm8_m516.glb')],check=True)
subprocess.run([sys.executable,str(ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),str(E/'mm8_m516.glb')],check=True)
