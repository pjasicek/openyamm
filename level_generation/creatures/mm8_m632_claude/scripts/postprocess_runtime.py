import subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
run(P/'scripts/clamp_lod_uv.py')
run(P.parent/'claude_shared/region_variants.py',P/'export/mm8_m632_lods.glb',P/'export/mm8_m632_combined.glb',P/'textures/m632_ramps.json')
run(R/'tools/split_attachment.py',P/'export/mm8_m632_combined.glb','--joint','Crossbow','--body',P/'export/mm8_m632.glb','--attachment',P/'export/mm8_m632_crossbow.glb')
run(R/'tools/merge_head_material.py',P/'export/mm8_m632.glb',P/'export/mm8_m632.glb')
