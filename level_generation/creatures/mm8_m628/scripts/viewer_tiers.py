"""Bake native ramps only into browser-review copies; installed tiers retain one shared texture set."""
import sys,json,hashlib,copy
import numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,image_of,add_image,compact
V=P/'review/viewer';base,raw=read_glb(P/'export/mm8_m628.glb')
def lin(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def srgb(c):return np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
models=[]
for vi,(name,label)in enumerate(zip(['m628_a','m628_b','m628_c'],['Bowman — green','Hunter — blue-purple','Archer — red'])):
    d=copy.deepcopy(base);b=bytearray(raw);used=set()
    for mesh in d['meshes']:
        for p in mesh['primitives']:
            for mapping in p.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):
                if vi in mapping['variants']:p['material']=mapping['material']
            p.get('extensions',{}).pop('KHR_materials_variants',None);used.add(p['material'])
    for i in used:
        m=d['materials'][i];extra=m.get('extras',{})
        if 'openyamm_region_mask'not in extra:continue
        index=m['pbrMetallicRoughness']['baseColorTexture']['index'];im,_=image_of(d,b,index);rgb=np.asarray(im.convert('RGB'),float)/255
        mask,_=image_of(d,b,extra['openyamm_region_mask']['index']);mask=np.asarray(mask.convert('RGBA'),float)/255
        color=lin(rgb);lum=color@np.array([.2126,.7152,.0722]);out=color.copy()
        for channel,reg in enumerate(extra['openyamm_region_ramps']):
            lo,hi=reg['range'];colors=np.array(reg['colors']);x=np.clip((lum-lo)/(hi-lo),0,1)*15;j=np.minimum(x.astype(int),14);f=(x-j)[...,None]
            ramp=colors[j]*(1-f)+colors[j+1]*f;w=mask[...,channel,None];out=out*(1-w)+ramp*w
        pixels=Image.fromarray((np.clip(srgb(out),0,1)*255+.5).astype(np.uint8))
        sampler=d['textures'][index].get('sampler');new=add_image(d,b,pixels,name+'_atlas',sampler)
        m['pbrMetallicRoughness']['baseColorTexture']['index']=new
        extra.pop('openyamm_region_mask');extra.pop('openyamm_region_ramps')
    d.get('extensions',{}).pop('KHR_materials_variants',None)
    for key in ['extensionsUsed','extensionsRequired']:
        if key in d:d[key]=[x for x in d[key]if x!='KHR_materials_variants']
    path=V/(name+'.glb');write_glb(path,*compact(d,b));sha=hashlib.sha256(path.read_bytes()).hexdigest()
    models.append({'id':name,'label':label,'revision':'m628-textured-v3','url':path.name+'?v='+sha[:12],'sha256':sha})
m=json.loads((V/'manifest.json').read_text());m.update(revision='m628-textured-v3',default_model='m628_a',model='m628_a.glb',models=models,model_sha256=models[0]['sha256'])
(V/'manifest.json').write_text(json.dumps(m,indent=2));print('VIEWER',[(x['id'],x['sha256'][:12])for x in models])
