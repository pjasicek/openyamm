from pathlib import Path
import sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import generate
generate(p/'export/mm6_ogr_runtime_lod0.glb',p/'export/mm6_ogr_lods.glb','Ogre')
