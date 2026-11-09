"""Keep one body asset; coupled clips enable its separately skinned cable node."""
import copy,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P.parent/'claude_shared/floor'),str(P.parent/'lod_repair_claude/scripts')]
from glb_pose import Glb
from splice_lods import tuck_shadow,compact
from build_actor_lods import write_glb
src=P/'work/bulwark_final_lods.glb';g=Glb(src);d=g.json
for node in d['nodes']:
    if 'mesh' not in node:continue
    base=d['meshes'][node['mesh']]
    for level,mi in enumerate(base.get('extras',{}).get('openyamm_shadow_lods',[])):
        if level:tuck_shadow(d,g.bin,d['meshes'][mi],base,level)
ci=next(i for i,n in enumerate(d['nodes']) if n.get('name')=='Bulwark_Cables')
d['nodes'][ci]['scale']=[0,0,0]
originals=list(d['animations'])
for clip in originals:
    duration=max(float(g.accessor(s['input'])[-1,0]) for s in clip['samplers'])
    coupled=copy.deepcopy(clip);coupled['name']='Coupled_'+clip['name'];d['animations'].append(coupled)
    for action,visible in ((clip,0),(coupled,1)):
        times=g.append_accessor(np.array([[0],[duration]],np.float32),'SCALAR')
        values=g.append_accessor(np.full((2,3),visible,np.float32),'VEC3')
        action['channels'].append({'sampler':len(action['samplers']),'target':{'node':ci,'path':'scale'}})
        action['samplers'].append({'input':times,'output':values,'interpolation':'STEP'})
assert len(d['animations'])==20
packed=compact(d,g.bin);write_glb(P/'work/hes_bulwark_states.glb',d,packed)
print('State clips: 10 mobile with cables hidden; 10 coupled with cable flex and grounded plugs')
