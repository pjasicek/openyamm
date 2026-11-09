"""Prepare the standard shared viewer and stage bindings. Viewer-only copies bake ramps for three.js."""
import copy,hashlib,json,sys,shutil
from pathlib import Path
import numpy as np
import yaml
P=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='scripts' else Path.cwd()/'level_generation/creatures/hes_drudge_codex'
ROOT=P.parents[2]
sys.path[:0]=[str(P/'scripts'),str(ROOT/'tools'),str(ROOT/'level_generation/creatures/claude_shared/floor')]
from build_drudges import baked
from glb_pose import Glb,Model
from merge_head_material import write_glb,add_image,compact,accessor_array,append_accessor
BOUND={'standing':'Demon_Standing','walking':'Drudge_Walking','attack_melee':'Demon_Attack',
 'hit':'Demon_Hit','dying':'Drudge_Death','dead':'Drudge_Dead','fidget':'Demon_Fidget'}
TIERS=[('a','Drudge A',10000,1,0,[]),('b','Drudge Brute',10001,1.15,1,['shoulder']),
 ('c','Drudge Hulk',10002,1.3,2,['shoulder','slabs']),('hatchling','Hatchling',10003,.8,0,[]),
 ('thrix','Thrix',10263,1,None,['scarf'])]
parts={p['file'].removeprefix('hes_drudge_').removesuffix('.glb'):p for p in json.loads((P/'export/attachments.json').read_text())}
measured=json.loads((P/'review/gates_final.json').read_text())['clips']
walk=round(float(np.mean([measured['Drudge_Walking'][s+'_stride_m'] for s in 'LR'])),4)
run=round(float(np.mean([measured['Drudge_Running'][s+'_stride_m'] for s in 'LR'])),4)
bindings=[]
for tier,label,row,scale,variant,additions in TIERS:
    binding={'descriptor':label,'model':'worlds/hesper/models/'+('hes_thrix.glb' if tier=='thrix' else 'hes_drudge.glb'),
      'scale':104.8623316*scale,'yaw_offset':-1.570796327,
      'animation':{'run':'Drudge_Running','stride_length':walk,'run_stride_length':run,'upper_body_root':'B_Spine',
        'look':{'nodes':['B_Neck','B_Head'],'max_yaw_degrees':30,'max_pitch_degrees':15},
        'events':{'attack_melee':{'impact':.5}}},'clips':BOUND.copy()}
    if variant is not None:binding['skin']='hsd_'+['a','b','c'][variant]
    if additions:binding['attachments']=[{'model':'worlds/hesper/models/'+parts[a]['file'],'node':parts[a]['node']} for a in additions]
    bindings.append(binding)
(P/'integration/actors.yml').write_text('# Stage-only Drudges. Shared body and original clips retained; fitted clips bind walking/running/death.\n'+yaml.safe_dump(bindings,sort_keys=False))
view=P/'review/viewer';view.mkdir(exist_ok=True)
for name in ['index.html','review.js']:
    text=(ROOT/'level_generation/creatures/hes_kreegan_claude/review/viewer'/name).read_text()
    text=text.replace('MM7 Blaster Guy','Hesper Drudges').replace('MM6 Native Archer','Hesper Drudges').replace('openyamm:mm6-natm-claude:notes','openyamm:hes-drudge-codex:notes')
    (view/name).write_text(text)
(view/'feedback').mkdir(exist_ok=True)
if not (view/'feedback/user_feedback.json').exists():(view/'feedback/user_feedback.json').write_text('{"findings": []}\n')
manifest={'revision':'hes_drudge_codex_v1','model':'drudge_a.glb','default_model':'a','default_clip':'Standing',
 'feedback':'feedback/user_feedback.json','models':[],'clips':{}}
RENAME={'Demon_Standing':'Standing','Drudge_Walking':'Walking','Drudge_Running':'Running','Demon_Attack':'Attack',
 'Demon_Hit':'Hit','Drudge_Death':'Death','Drudge_Dead':'Dead','Demon_Fidget':'Fidget'}
def append_part(g,path,joint):
    a=Glb(path);d,b=g.json,g.bin;ad=a.json
    vo,ao,io,to,mo,meo=len(d['bufferViews']),len(d['accessors']),len(d['images']),len(d['textures']),len(d['materials']),len(d['meshes'])
    b.extend(b'\0'*(-len(b)%4));offset=len(b);b.extend(a.bin)
    d['bufferViews'] += [dict(v,byteOffset=v.get('byteOffset',0)+offset) for v in ad['bufferViews']]
    d['accessors'] += [dict(v,bufferView=v['bufferView']+vo) for v in ad['accessors']]
    d['images'] += [dict(v,bufferView=v['bufferView']+vo) for v in ad['images']]
    d['textures'] += [dict(v,source=v['source']+io) for v in ad['textures']]
    for mat in ad['materials']:
        mat=copy.deepcopy(mat)
        for parent,key in [(mat,'normalTexture'),(mat['pbrMetallicRoughness'],'baseColorTexture'),(mat['pbrMetallicRoughness'],'metallicRoughnessTexture')]:
            if key in parent:parent[key]['index']+=to
        d['materials'].append(mat)
    for mesh in ad['meshes']:
        for prim in mesh['primitives']:
            prim['attributes']={k:v+ao for k,v in prim['attributes'].items()};prim['indices']+=ao;prim['material']+=mo
        d['meshes'].append(mesh)
    ni=len(d['nodes']);d['nodes'].append({'name':path.stem,'mesh':meo})
    next(n for n in d['nodes'] if n.get('name')==joint).setdefault('children',[]).append(ni)
for tier,label,row,scale,variant,additions in TIERS:
    g=Glb(P/'export'/('hes_thrix.glb' if tier=='thrix' else 'hes_drudge.glb'));d=g.json
    for mesh in d['meshes']:
        for prim in mesh['primitives']:
            mappings=prim.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[])
            if variant is not None:
                for mapping in mappings:
                    if variant in mapping['variants']:prim['material']=mapping['material']
            prim.pop('extensions',None)
    d.pop('extensions',None);d['extensionsUsed']=[x for x in d.get('extensionsUsed',[]) if x!='KHR_materials_variants']
    for mat in d['materials']:
        if 'openyamm_region_ramps' not in mat.get('extras',{}):continue
        im=baked(d,g.bin,mat);idx=add_image(d,g.bin,im,'Viewer_baked_'+mat['name'],0)
        mat['pbrMetallicRoughness']['baseColorTexture']={'index':idx}
        mat['extras'].pop('openyamm_region_ramps');mat['extras'].pop('openyamm_region_mask')
    for name in additions:append_part(g,P/'export'/parts[name]['file'],parts[name]['node'])
    roots=d['scenes'][d.get('scene',0)]['nodes'];d['nodes'].append({'name':'Tier_scale','scale':[scale]*3,'children':roots})
    d['scenes'][d.get('scene',0)]['nodes']=[len(d['nodes'])-1]
    model=Model(g)
    for animation in d['animations']:
        old=animation['name'];new=RENAME.get(old,old);duration=max(model.clip_times(old));animation['name']=new
        provenance='Bound Drudge clip; '+('Mixamo Standard Run, source-path fit and floor correction.' if new=='Running' else 'shared Kreegan source, local fit where required.')
        if old not in RENAME:provenance='UNBOUND inherited shared clip; see README for measured baseline warnings.'
        manifest['clips'][new]={'label':new,'duration':duration,'mode':'once' if new in ['Attack','Hit','Death'] or any(x in old for x in ['Attack','Death','Hit','Cast']) else 'loop',
          'provenance':provenance,'anchors':[{'time':0,'label':'Start','phase':provenance,'source_images':[]}]}
    g.json,g.bin=compact(d,g.bin);out=view/('drudge_'+tier+'.glb');write_glb(out,g.json,g.bin)
    sha=hashlib.sha256(out.read_bytes()).hexdigest()
    manifest['models'].append({'id':tier,'label':f'{label} ({row}, x{scale:g})','revision':manifest['revision'],'url':out.name+'?v='+sha[:12],'sha256':sha})
# Default bound clips come first, while all inherited clips remain inspectable.
manifest['clips']={k:manifest['clips'][k] for k in list(RENAME.values())+[k for k in manifest['clips'] if k not in RENAME.values()]}
(view/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('VIEWER',len(manifest['models']),'models,',len(manifest['clips']),'clips; strides',walk,run)
