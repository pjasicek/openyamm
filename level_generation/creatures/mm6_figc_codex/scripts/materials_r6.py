"""Perceptual steel midpoint; preserve every mesh attribute and unrelated material field."""
import sys,json,copy,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P/'review/round6';E=P/'export'
sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'));sys.path.insert(0,str(P/'scripts'))
from merge_head_material import read_glb,write_glb,image_of,add_image,compact
import package_r4 as pack
L=np.array([.2126,.7152,.0722])
def lin(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def enc(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def mapped(reg,lum):
 t=np.clip((lum-reg['range'][0])/np.diff(reg['range'])[0],0,1)*15;i=np.minimum(t.astype(int),14);return np.array(reg['colors'])[i]*(1-(t-i)[...,None])+np.array(reg['colors'])[i+1]*(t-i)[...,None]
def stats(x):return {'linear_mean':float(x.mean()),'linear_p50_p90_p95':np.percentile(x,[50,90,95]).tolist(),'srgb_mean':float(enc(x).mean()),'srgb_p50_p90_p95':np.percentile(enc(x),[50,90,95]).tolist()}
report={'method':'sRGB midpoint of round-1 and current steel ramps, evaluated at the same base luminance; same curve for all tiers. Base paint/normal/mask/UV unchanged. Shield unchanged.','materials':{}}
for name in ['mm6_figc.glb','mm6_figc_axe.glb']:
 d,b=read_glb(E/name if name=='mm6_figc.glb' else R/'before/export'/name);old,ob=read_glb(P/'review/round2/before/export'/name);reg=d['materials'][0]['extras']['openyamm_region_ramps'][2];bright=old['materials'][0]['extras']['openyamm_region_ramps'][2];new=copy.deepcopy(reg)
 new['colors']=lin((enc(np.array(reg['colors']))+enc(mapped(bright,np.linspace(*reg['range'],16))))/2).tolist()
 mat=d['materials'][0];base=np.array(image_of(d,b,mat['pbrMetallicRoughness']['baseColorTexture']['index'])[0].convert('RGB'))/255;mask=np.array(image_of(d,b,mat['extras']['openyamm_region_mask']['index'])[0].convert('RGBA'))/255;lum=lin(base)@L;core=mask[:,:,2]>.95
 report['materials'][name]={'core_texels':int(core.sum()),'round1':stats(mapped(bright,lum[core])@L),'current':stats(mapped(reg,lum[core])@L),'new':stats(mapped(new,lum[core])@L),'ramp':new}
 mr=np.array(image_of(d,b,mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'])[0].convert('RGB'));weight=mask[:,:,2];mr[:,:,0]=np.rint(mr[:,:,0]*(1-weight)+np.minimum(mr[:,:,0],32)*weight);mr[:,:,1]=np.rint(mr[:,:,1]*(1-weight)+np.maximum(mr[:,:,1],220)*weight)
 ti=add_image(d,b,Image.fromarray(mr),name+'_matte_steel',0)
 for m in d['materials']:
  if 'openyamm_region_ramps' in m.get('extras',{}):m['extras']['openyamm_region_ramps'][2]=copy.deepcopy(new);m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']=ti
 out=P/'textures/round6'/('body' if name=='mm6_figc.glb' else 'axe');out.mkdir(parents=True,exist_ok=True);Image.fromarray(mr).save(out/'metal_rough.png');(out/'steel_ramp.json').write_text(json.dumps(new,indent=2))
 write_glb(E/name,*compact(d,b))
# Use the same native steel selection as the recorded round-2 calibration.
a=np.array(Image.open(P.parent/'mm6_figc/native_variants/figcsta0_212.png').convert('RGB'))/255;mask=np.array(Image.open(P/'review/round2/native_steel_samples.png'))>0;report['native']=stats(lin(a[mask])@L);report['native_samples']=int(mask.sum());(R/'steel_luminance.json').write_text(json.dumps(report,indent=2))
# Same accepted geometry for the three-stage palette comparison, eliminating topology as a confound.
pack.R=R
pack.combine(raw_only=True)
combined,payload=read_glb(R/'combined_unbaked.glb')
for stage in ['round1','current','new']:
 d=copy.deepcopy(combined);b=bytearray(payload)
 if stage!='new':
  for m in d['materials']:
   if m['name'].startswith('FighterChain') and 'openyamm_region_ramps' in m.get('extras',{}):
    # Shield material is the last material: leave the accepted shield alone.
    if m is d['materials'][-1]:continue
    part='mm6_figc_axe.glb' if 'Gear' in m['name'] else 'mm6_figc.glb'
    source=P/'review/round2/before/export'/part if stage=='round1' else R/'before/export'/part
    sd,sb=read_glb(source);m['extras']['openyamm_region_ramps'][2]=copy.deepcopy(sd['materials'][0]['extras']['openyamm_region_ramps'][2])
 pack.bake_tier(d,b,stage);write_glb(R/f'palette_{stage}.glb',*compact(d,b))
for tier in range(3):pack.combine(tier)
shutil.copy2(P/'review/viewer/mm6_figc_a.glb',E/'mm6_figc_portable.glb')
# LOD0 runtime body keeps all tier variants and motion, strips unused LOD meshes.
d,b=read_glb(E/'mm6_figc.glb');d['meshes']=d['meshes'][:1];d['meshes'][0].pop('extras',None);write_glb(E/'mm6_figc_lod0.glb',*compact(d,b))
v=P/'review/viewer/manifest.json';manifest=json.loads(v.read_text());manifest['revision']='mm6_figc_codex_review6'
for m in manifest['models']:
 f=v.parent/f'mm6_{m["id"]}.glb';m['sha256']=hashlib.sha256(f.read_bytes()).hexdigest();m['url']=f.name+'?v='+m['sha256'][:12];m['revision']=manifest['revision']
manifest['clips']['Running'].update(duration=22/30,provenance='Mixamo Standard Run; 1.86 m stride, 12 mm smooth symmetric pelvis bob, foot IK without root snaps, closed loop');manifest['model_sha256']=manifest['models'][0]['sha256'];v.write_text(json.dumps(manifest,indent=2));print(json.dumps(report,indent=2))
