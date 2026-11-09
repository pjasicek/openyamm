from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from prepare_actor_glb import prepare
from merge_head_material import read_glb,write_glb
out=P/'export/mm8_centaur_prepared.glb';prepare(P/'export/mm8_centaur_lod0.glb',out)
d,b=read_glb(out)
for m in d['materials']:m.pop('occlusionTexture',None)
arrow=next(i for i,n in enumerate(d['nodes'])if n.get('name')=='Arrow')
for a in d['animations']:
    for c in a['channels']:
        if c['target']['node']==arrow and c['target']['path']=='scale':a['samplers'][c['sampler']]['interpolation']='STEP'
write_glb(out,d,b)
