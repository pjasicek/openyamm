"""Write native-size bindings, review tiers and deterministic isolated game capture tours."""
import copy
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import yaml

P=Path(__file__).resolve().parents[1];REPO=P.parents[2]
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb,write_glb
glb=Glb(P/'export/mm8_wolf.glb');mesh=load_meshes(glb)[0]
clip=next(c for n,c,a,b in glb.clips() if n=='Standing')
co=mesh.posed(glb.pose(clip,np.array([0.]))[0]);height=float(np.ptp(co[:,2]));scale=158/height
assert 220<scale<260
bindings=[]
for tier in 'ABC':
    binding={'descriptor':'Dire Wolf '+tier,'model':'worlds/mm8/models/mm8_wolf.glb','scale':scale,
             'yaw_offset':-1.570796327,'skin':'wolf_'+tier.lower(),
             'animation':{'cast':'Attack','run':'Running','stride_length':.34,'run_stride_length':.48,
               'upper_body_root':'Spine2','look':{'nodes':['Neck1','Head'],'max_yaw_degrees':30,'max_pitch_degrees':20},
               'sockets':{},'events':{'attack_melee':{'impact':.875}}},
             'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack',
                      'hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}}
    binding['scale']*=dict(A=1,B=2.299988/2,C=2.699997/2)[tier]
    bindings.append(binding)
path=REPO/'assets_dev/worlds/mm8/models/actors.yml';text=path.read_text()
existing=[x for x in yaml.safe_load(text)['actors'] if x['descriptor'].startswith('Dire Wolf ')]
if existing:
    assert existing==bindings,'Existing wolf bindings differ; review before replacing them'
else:
    with path.open('a') as stream:
        stream.write('\n# MM8 m512, palette 512: native A/B/C sizes share one wolf skin and rig.\n'+yaml.safe_dump(bindings,sort_keys=False))
(P/'work/scale_calibration.json').write_text(json.dumps({'native_bbox_height':79,'native_scale_a':2,
 'standing_height_model':height,'scale_a':scale,'tier_ratios':[1,2.299988/2,2.699997/2]},indent=2)+'\n')
viewer=P/'review/viewer';src,payload=read_glb(P/'export/wolf_viewer.glb')
manifest=json.loads((viewer/'manifest.json').read_text());manifest['models']=[]
for tier,label,ratio in [('a','Dire Wolf Yearling',1.),('b','Dire Wolf',2.299988/2),('c','Pack Leader',2.699997/2)]:
    d=copy.deepcopy(src);root=len(d['nodes']);scene=d['scenes'][d.get('scene',0)]
    d['nodes'].append({'name':'NativeTierScale','children':scene['nodes'],'scale':[ratio]*3});scene['nodes']=[root]
    f=viewer/f'wolf_{tier}.glb';write_glb(f,d,payload);sha=hashlib.sha256(f.read_bytes()).hexdigest()
    manifest['models'].append({'id':f'wolf_{tier}','label':label,'revision':'mm8_wolf_final_v3',
                              'url':f.name+'?v='+sha[:12],'sha256':sha})
manifest['model_sha256']=manifest['models'][0]['sha256'];manifest['revision']='mm8_wolf_final_v3'
(viewer/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for location,points in [('outdoor',[(-4114,2954,1),(-4157,3149,1),(-4200,3344,1)]),
                        ('indoor',[(1223,-3135,-47),(1223,-2935,-47),(1223,-2735,-47)])]:
    for rendering in ['model','sprite']:
        out=P/'review/ingame'/f'{location}_{rendering}';out.mkdir(parents=True,exist_ok=True)
        steps=[{'wait':1},{'key':'`'},{'wait':.2}]
        for index,(x,y,z) in enumerate(points,85):
            steps.extend([{'text':f'actor spawn {index} 1 {x} {y} {z}'},{'key':'Return'},{'wait':.05}])
        steps.extend([{'key':'`'},{'wait':.15},{'capture':'tiers'},{'wait':.8},{'capture':'approach'},
                      {'wait':1.4},{'capture':'combat'},{'key':'`'},{'wait':.1},
                      {'text':'actor damage last 1'},{'key':'Return'},{'key':'`'},
                      {'wait':.2},{'capture':'hit'},{'wait':1},
                      {'key':'`'},{'wait':.1},{'text':'actor kill 1200'},{'key':'Return'},{'key':'`'},
                      {'wait':.25},{'capture':'death'},{'wait':1},{'capture':'corpses'}])
        (out/'tour.yml').write_text(yaml.safe_dump({'output_dir':'/tmp/mm8-wolf-runtime/'+out.name,'exit':True,'steps':steps},sort_keys=False))
print('Native scale',scale,'; bindings and four capture tours written')
