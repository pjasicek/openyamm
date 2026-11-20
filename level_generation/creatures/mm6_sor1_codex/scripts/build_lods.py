import bpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0,str(p/'scripts'));from build_actor_lods_protected import generate
ratios=json.loads((p/'work/lod_ratios_round2.json').read_text())
generate(p/'export/mm6_sor1_runtime_lod0.glb',p/'export/mm6_sor1_lods.glb','Sorcerer',ratios=ratios)
