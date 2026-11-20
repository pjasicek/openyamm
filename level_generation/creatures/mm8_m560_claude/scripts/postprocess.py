"""Shared runtime post-processes; no geometry or gameplay changes."""
from pathlib import Path
import subprocess,sys,json
P=Path(__file__).resolve().parents[1];repo=P.parents[2];E=P/'export';C=P.parent/'claude_shared'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(C/'region_variants.py',E/'mm8_m560_lods.glb',E/'mm8_m560_regions.glb',P/'textures/wyvern_ramps.json')
run(C/'material_classes_to_orm.py',E/'mm8_m560_regions.glb',E/'mm8_m560.glb','--classes',P/'textures/wyvern_material_classes.png','--report',P/'review/material_orm.json','--maps-dir',P/'textures/runtime')
run(P/'scripts/viewer_tiers.py')
