"""Native palette regions over the retained UVs; one shared PBR set for all three tiers."""
from pathlib import Path
import json,sys,struct
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];REPO=P.parents[2];T=P/'textures'
sys.path.insert(0,str(P.parent/'mm6_gob_claude/scripts'))
from compose_textures_v2 import rasterise,hsv,load
sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import read_glb,srgb_to_linear,write_mask,luminance

def accessor(doc,binary,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
 dt={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
 return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*n),np.dtype(dt).itemsize))
def corners(path,key):
 d,b=read_glb(path);q=d['meshes'][0]['primitives'][0]
 return accessor(d,b,q['attributes'][key])[accessor(d,b,q['indices']).ravel()]
from scipy.spatial import cKDTree
upload=P/'texturing/gorgon_neutral.glb';returned=P/'meshy/retexture_v1/model_urls_glb.glb'
ap,au=corners(upload,'POSITION'),corners(upload,'TEXCOORD_0')
bp,bu=corners(returned,'POSITION'),corners(returned,'TEXCOORD_0')
distance,match=cKDTree(au).query(bu)
assert distance.max()<1e-6,'Retexture changed UVs'
transform=np.linalg.lstsq(np.c_[ap[match],np.ones(len(match))],bp,rcond=None)[0]
residual=np.max(abs(np.c_[ap[match],np.ones(len(match))]@transform-bp))
assert residual<.00025,'Retexture changed local shape'
assert np.max(abs(transform[:3]-np.eye(3)*np.mean(np.diag(transform[:3]))))<1e-5
back_distance,_=cKDTree(bu).query(au)
missing=np.where(back_distance>1e-6)[0]
tri=ap.reshape(-1,3,3)
area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
assert len(missing)==0 or area[np.unique(missing//3)].sum()/area.sum()<5e-5,'Missing visible textured surfaces'
correspondence={'returned_triangles':len(bp)//3,'upload_triangles':len(ap)//3,'max_uv_error':float(distance.max()),'max_geometry_residual':float(residual),'service_normalisation':transform.tolist(),'missing_uv_corners':len(missing),'missing_area_fraction':float(area[np.unique(missing//3)].sum()/area.sum())}
(P/'work/retexture_correspondence.json').write_text(json.dumps(correspondence,indent=2)+'\n')
data=np.load(P/'work/uv3d.npz')
parts,xyz=rasterise(data,tol=0,values=np.arange(len(data['uv'])))
valid=parts>=0
_,inds=ndimage.distance_transform_edt(~valid,return_indices=True)
def pad(a):return a[tuple(inds)]
S=P/'meshy/retexture_v1'
base=pad(load(S/'texture_urls_0_base_color.png'));normal=pad(load(S/'texture_urls_0_normal.png'))
ao=pad(load(T/'gorgon_ao.png','L'));rough=pad(load(S/'texture_urls_0_roughness.png','L'))
# The service removed four zero-area triangles and one 0.003% surface chart. Repair that tiny chart locally.
bad=np.isin(parts,np.unique(missing//3))&valid
good=valid&~bad
known=np.array(np.nonzero(good)).T
_,nearest=cKDTree(xyz[good]).query(xyz[bad])
source=tuple(known[nearest].T)
base[bad]=base[source];rough[bad]=rough[source];normal[bad]=(.5,.5,1)
base=pad(base);rough=pad(rough);normal=pad(normal)
h,s,v=hsv(base);x,y,z=xyz.transpose(2,0,1)
# The returned paint distinguishes copper ridge, olive plates and pale horn/hoof surfaces.
eye=(h<18)&(s>.58)&(v>.30)&(y<-.30)&(z>.19)&(z<.33)
bone=(s<.30)&(v>.25)&((z<.06)|((y<-.20)&(z>.29)))&~eye
copper=(h<53)&(s>.34)&~bone&~eye
plate=~(bone|copper|eye)
labels=np.select([eye,bone,copper],[6,4,9],default=9).astype(np.uint8)
weights=[pad(w.astype(float)) for w in (plate,copper,bone,eye)]
weights=[ndimage.gaussian_filter(w,.65) for w in weights]
assert np.max(abs(sum(weights)-1))<1e-5
# Mild AO strengthens real panel junctions without painting out sculptural relief.
base=np.clip(base*(.78+.22*ao[...,None]),0,1)
Image.fromarray(np.uint8(base*255+.5)).save(T/'gorgon_basecolor.png')
Image.fromarray(np.uint8(normal*255+.5)).resize((1024,1024),Image.Resampling.LANCZOS).save(T/'gorgon_normal_1k.png')
metal=np.where(pad(bone|eye),0,.72)
rough=np.where(pad(eye),.2,np.where(pad(bone),.56,np.clip(rough,.48,.78)))
spec=np.where(pad(bone),.30,np.where(pad(eye),.65,.65))*(.45+.55*ao)
mr=np.stack([spec,rough,metal],-1)
Image.fromarray(np.uint8(mr*255+.5)).resize((1024,1024),Image.Resampling.BOX).save(T/'gorgon_metal_rough_1k.png')
Image.fromarray(pad(labels),'L').save(T/'gorgon_material_classes.png')
write_mask(weights,T/'gorgon_region_mask.png')
pal=[np.frombuffer((REPO/f'assets_dev/worlds/mm8/textures/Pal{i}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for i in (565,566,567)]
ids=np.asarray(Image.open(REPO/'assets_dev/engine/sprites/m564Sa2.bmp'))
counts=np.bincount(ids.ravel(),minlength=256);counts[0]=0
h,s,v=hsv(pal[0]);bonepal=(s<.28)&(v>.35);eyepal=(h<20)&(v>.20)
copperpal=(h<55)&~bonepal&~eyepal;platepal=~(bonepal|eyepal|copperpal)
ramps={k:[] for k in ('gorgon_a','gorgon_b','gorgon_c')};report={}
for region,(mask,sel) in enumerate(zip(weights,(platepal,copperpal,bonepal,eyepal))):
 core=(mask>.9)&valid
 assert core.sum()>50,(region,int(core.sum()))
 lo,hi=np.percentile(luminance(base)[core],[1,99]);hi=max(hi,lo+.001)
 selected=np.where(sel&(counts>0))[0]
 assert len(selected)>1,(region,selected)
 # Resample each tier independently by its own native luminance, never by A-to-B colour ratios.
 for tier,p in zip(ramps,pal):
  colors=np.clip(p[selected]*1.4,0,1);lum=luminance(colors);order=np.argsort(lum)
  u=np.linspace(float(lum.min()),float(lum.max()),16)
  target=np.stack([np.interp(u,lum[order],colors[order,c]) for c in range(3)],-1)
  ramps[tier].append({'range':[float(lo),float(hi)],'colors':srgb_to_linear(target).tolist()})
 report[str(region)]={'native_indices':selected.tolist(),'texels':int(core.sum()),'base_luminance_range':[float(lo),float(hi)]}
(T/'gorgon_ramps.json').write_text(json.dumps({'variants':list(ramps),'materials':[{'base':'Gorgon_A','prefix':'Gorgon','mask':'gorgon_region_mask.png','ramps':ramps}]},indent=2)+'\n')
(T/'compose_report.json').write_text(json.dumps({'uv_and_geometry_return':correspondence,'regions':['armour plates','copper ridge and muzzle','horns and hooves','eyes'],'palette_ids':[565,566,567],'native_albedo_gain':1.4,'native_regions':report,'material':'oxidised metal armour .72 metallic; horns and eyes dielectric; current runtime MR red carries specular mask, separate AO retained'},indent=2)+'\n')
print(json.dumps(report,indent=2))
