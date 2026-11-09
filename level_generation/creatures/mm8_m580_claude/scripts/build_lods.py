from pathlib import Path
import sys
sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import generate
P=Path(__file__).resolve().parents[1]
generate(P/'export/mm8_m580_runtime_lod0.glb',P/'export/mm8_m580_lods.glb','Turtle',max_influences=4)
