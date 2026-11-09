"""Finalize the GLB and configure the existing shared evaluator's neck/floor probes."""
import json, sys, runpy
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb, write_glb, accessor_array
file=P/'export/mm6_natm.glb'; doc,buf=read_glb(file); removed=[]
for animation in doc['animations']:
    keep=[]
    for channel in animation['channels']:
        target=channel['target']; node=doc['nodes'][target['node']]; path=target['path']
        if node.get('name') in ['B_Neck','B_Head'] and path in ['translation','scale']:
            values=accessor_array(doc,buf,animation['samplers'][channel['sampler']]['output'])
            expected=node.get(path,[1,1,1] if path=='scale' else [0,0,0])
            assert np.max(abs(values-np.array(expected)))<1e-5, (animation['name'],node['name'],path)
            removed.append([animation['name'],node['name'],path])
        else:keep.append(channel)
    animation['channels']=keep
write_glb(file,doc,buf)
(P/'review/round3_removed_constant_channels.json').write_text(json.dumps(removed,indent=2))
source=(P/'scripts/review1_finalize.py').read_text().replace('round1','round3')
exec(compile(source,str(P/'scripts/review1_finalize.py'),'exec'))
config=json.loads((P/'gates.json').read_text())
config['forward']=[0,-1,0]
config['regions']['neck']={'weights':['B_Neck','B_Head'], 'weight_min':.015,
                          'bounds':[[-.13,-.3,1.375],[.13,.10,1.54]]}
(P/'gates.json').write_text(json.dumps(config,indent=2)+'\n')
neck=json.loads(json.dumps(config))
for side in 'LR':neck['regions']['arm_'+side]='neck'
neck['thresholds']['arm_stretch_p99']=1.5;neck['thresholds']['arm_stretch_max']=2.0
neck['clips']={'rest':[],'walk':[],'run':[],'attack':['Attack']}
neck['sole_band_m']=4
for side in 'LR':neck['regions']['foot_'+side]={'bounds':[[-10,-10,-10],[10,10,10]]}
for prop in neck['props']:prop['file']='../'+prop['file']
(P/'review/round3_neck.gates.json').write_text(json.dumps(neck,indent=2)+'\n')
# Unknown top-level fields are rejected by the shared runner; keep the requested extension separate.
request={'status':'UNVERIFIED by shared runner: unsupported configuration fields',
 'head_forward':{'clips':['Attack','Cast'],'node':'B_Head','forward':[0,-1,0],
                 'maximum_yaw_deg':20,'maximum_pitch_deg':20,'interval':'entire clip'},
 'cast_palm_forward':{'clip':'Cast','side':'L','release_s':23/48,'maximum_angle_deg':30},
 'neck_channels':{'nodes':['B_Neck','B_Head'],'translation_channels':0,'scale_channels':0},
 'neck_stretch':'Measured with the unmodified shared runner using its configurable arm edge selectors; see round3_neck.gates.json.'}
(P/'integration/shared_gate_request.json').write_text(json.dumps(request,indent=2)+'\n')
