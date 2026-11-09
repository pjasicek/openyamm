"""Link the authored school LODs and palette ramps; create the shared animation review viewer."""
import copy, hashlib, json, re, sys
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(P.parent/'claude_shared')]
from merge_head_material import read_glb,write_glb,add_image
import region_variants as RV
D,B=read_glb(P/'export/mm8_m636_raw.glb');B=bytearray(B)
assert len(D['skins'])==1 and len(D['skins'][0]['joints'])==61
indices={n['name']:n['mesh'] for n in D['nodes'] if 'mesh' in n};lods=[indices[f'School_LOD{i}'] for i in range(1,4)]
D['meshes'][indices['School']].setdefault('extras',{}).update(openyamm_lods=lods,openyamm_shadow_lods=lods)
for n in D['nodes']:
    if n.get('mesh') in lods:n.pop('mesh');n.pop('skin',None)
assert len(D['materials'])==1
mat=D['materials'][0];mat['name']='FishMaterial';mat.pop('extensions',None)
mat.update(alphaMode='OPAQUE',doubleSided=False,extras={'openyamm_specular':1,'openyamm_specular_mask':True})
pbr=mat['pbrMetallicRoughness'];pbr.update(metallicFactor=0,roughnessFactor=1,baseColorFactor=[1,1,1,1])
sampler=D['textures'][pbr['baseColorTexture']['index']].get('sampler')
pbr['metallicRoughnessTexture']={'index':add_image(D,B,Image.open(P/'textures/fish_orm.png'),'Fish ORM',sampler)}
mat.pop('occlusionTexture',None)
D['extensionsUsed']=[];D.pop('extensionsRequired',None)
D,B=RV._compact(D,B);write_glb(P/'work/mm8_m636_material.glb',D,B)
RV.apply_variants(P/'work/mm8_m636_material.glb',P/'export/mm8_m636.glb',P/'textures/fish_ramps.json')
D,B=read_glb(P/'export/mm8_m636.glb')
V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True);(V/'feedback').mkdir(exist_ok=True)
models=[]
# Browser previews bake the exact engine ramp into the colour image; animation and geometry stay identical.
for i,(name,label) in enumerate([('m636_a','Purple'),('m636_b','Green'),('m636_c','Orange')]):
    d,b=copy.deepcopy(D),bytearray(B);m=copy.deepcopy(d['materials'][i])
    m['pbrMetallicRoughness']['baseColorTexture']={'index':add_image(d,b,Image.open(P/f'review/fish_{name}.png'),name,sampler)}
    m['extras'].pop('openyamm_region_mask');m['extras'].pop('openyamm_region_ramps')
    d['materials']=[m];d.pop('extensions',None);d['extensionsUsed']=[]
    for mesh in d['meshes']:
        for primitive in mesh['primitives']:primitive['material']=0;primitive.pop('extensions',None)
    d,b=RV._compact(d,b);path=V/f'{name}.glb';write_glb(path,d,b)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    models.append({'id':name,'label':f'School of Fish · {label}','revision':'m636-v1','url':f'{name}.glb?v={sha[:12]}','sha256':sha})
template=P.parent/'mm8_m628/review/viewer'
html=(template/'index.html').read_text().replace('MM8 Skeleton Archer','MM8 School of Fish')
html=re.sub(r'<header>.*?</header>','<header><h1>MM8 School of Fish</h1><p>Twelve fish · coordinated swim, phased tails and native death timing · one shared rig and atlas.</p></header>',html)
for before,after in [('Head / neck','Upper fish'),('Arms / wrists','Middle fish'),('Shoulders / wings','Whole school'),('Hands','Lower school'),('Feet','Lowest fish')]:html=html.replace(before,after)
html=html.replace('e.g. Left palm faces backward during the sweep.','e.g. A tail bends too far during the swim.')
(V/'index.html').write_text(html)
js=(template/'review.js').read_text().replace('MM8 Skeleton Archer','MM8 School of Fish').replace('mm8-m628','mm8-m636')
js=re.sub(r'const focuses = .*?;', 'const focuses = {body:[0,1.1,0,4.8],head:[-.25,1.85,-.45,1.8],arms:[.15,1.15,0,2.8],shoulders:[0,1.1,0,4.8],skirt:[0,.65,0,2.8],feet:[0,.3,0,2]};',js)
(V/'review.js').write_text(js)
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text('{"findings":[]}\n')
clips={}
for name,duration,mode,prefix,count in [('Swim',1.875,'loop','w',15),('Death',1.25,'once','d',10),('Dead',1,'loop','x',1)]:
    clips[name]={'label':name,'duration':duration,'mode':mode,'provenance':'Native school silhouette and 125 ms frame timing; newly authored tail, fin, formation and roll motion.',
    'anchors':[{'time':min(i*.125,duration),'label':f'm636{prefix}{chr(97+i)}0','phase':'Native frame',
      'source_images':[f'../../../mm8_m636/aligned_2x/m636{prefix}{chr(97+i)}0.png']} for i in range(count)]}
sha=hashlib.sha256((P/'export/mm8_m636.glb').read_bytes()).hexdigest()
(V/'manifest.json').write_text(json.dumps({'revision':'m636-v1','default_model':'m636_a','default_clip':'Swim','model':'m636_a.glb',
    'model_sha256':models[0]['sha256'],'models':models,'clips':clips,'feedback':'feedback/user_feedback.json','runtime_sha256':sha},indent=2)+'\n')
print('Runtime',sha,'viewer',V)
