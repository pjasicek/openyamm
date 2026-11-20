"""Finish the repaired runtime export with the shared, inversion-safe near shadow tuck."""
import sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path[:0]=[str(P.parents[2]/'tools'),str(P.parent/'lod_repair_claude/scripts')]
from build_actor_lods import read_glb,write_glb
from splice_lods import tuck_shadow,compact
source=P/'work/lod_repair/export/hes_brood_mother.glb';doc,data=read_glb(source);binary=bytearray(data)
node=next(n for n in doc['nodes'] if n.get('name')=='BroodMother');base=doc['meshes'][node['mesh']]
tuck_shadow(doc,binary,doc['meshes'][base['extras']['openyamm_shadow_lods'][1]],base,1)
write_glb(P/'export/hes_brood_mother.glb',doc,compact(doc,binary))
