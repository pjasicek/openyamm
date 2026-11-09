import sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'scripts'),str(P.parents[2]/'tools')]
from merge_head_material import read_glb,write_glb,compact
from normalize_lod_weights import normalize_weights
for file in ['mm6_dwa1_runtime_lod0.glb','mm6_dwa1_lods.glb']:
 path=P/'export'/file;d,b=read_glb(path);normalize_weights(d,b);write_glb(path,*compact(d,b))
