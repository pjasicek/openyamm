import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import generate
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P/'export/mm8_m536_runtime_lod0.glb',P/'export/mm8_m536_lods.glb','Body',ratios=(.5,.25,.125),max_influences=4)
