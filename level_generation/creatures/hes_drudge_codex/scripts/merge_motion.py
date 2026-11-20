"""Append fitted clips without re-exporting any shared body geometry, rig, or inherited animation."""
import copy,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'level_generation/creatures/claude_shared/floor')]
from glb_pose import Glb
from merge_head_material import accessor_array,append_accessor,write_glb
source=Glb(P/'work/motion.glb')
for stem in ['drudge','thrix']:
    target=Glb(P/'work'/f'{stem}_before_lod.glb')
    names={n.get('name'):i for i,n in enumerate(target.json['nodes'])}
    for animation in source.json['animations']:
        assert animation['name'].startswith('Drudge_')
        new=copy.deepcopy(animation)
        for ch in new['channels']:
            name=source.json['nodes'][ch['target']['node']]['name'];assert name in names
            old=source.json['nodes'][ch['target']['node']];own=target.json['nodes'][names[name]]
            for key,default in [('translation',[0,0,0]),('scale',[1,1,1])]:
                assert np.allclose(old.get(key,default),own.get(key,default),atol=2e-5),(name,key)
            q=np.array(old.get('rotation',[0,0,0,1]));r=np.array(own.get('rotation',[0,0,0,1]));assert abs(q@r)>1-1e-5,name
            ch['target']['node']=names[name]
        for sampler in new['samplers']:
            for key in ['input','output']:
                i=sampler[key];a=source.json['accessors'][i]
                sampler[key]=append_accessor(target.json,target.bin,accessor_array(source.json,source.bin,i),a,34962)
        target.json['animations'].append(new)
    write_glb(P/'work'/f'{stem}_animated.glb',target.json,target.bin)
    print(stem,[a['name'] for a in target.json['animations']])
