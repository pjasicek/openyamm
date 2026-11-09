import subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
run(R/'tools/prepare_actor_glb.py',P/'export/mm8_m632_lod0.glb',P/'export/mm8_m632_prepared.glb')
run(P.parent/'claude_shared/material_classes_to_orm.py',P/'export/mm8_m632_prepared.glb',P/'export/mm8_m632_runtime_lod0.glb',
 '--map',f'Dwarf={P}/textures/m632_body_material_classes.png,{P}/textures/m632_head_material_classes.png',
 '--map',f'Crossbow={P}/textures/m632_crossbow_material_classes.png','--report',P/'review/material_classes.json','--maps-dir',P/'textures/runtime')
