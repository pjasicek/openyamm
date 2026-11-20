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
upload=P/'texturing/unicorn_neutral.glb';returned=P/'meshy/retexture_v1/model_urls_glb.glb'
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
missing_triangles=np.unique(missing//3)
# This return omitted one 0.00975% tail-tip chart; retain it and paint from its neighbouring tail surface.
assert len(missing_triangles)==1 and area[missing_triangles].sum()/area.sum()<.0001
assert np.max(tri[missing_triangles,:,2])<-.46, 'Missing chart is outside the reviewed tail tip'
correspondence={'returned_triangles':len(bp)//3,'upload_triangles':len(ap)//3,'max_uv_error':float(distance.max()),'max_geometry_residual':float(residual),'service_normalisation':transform.tolist(),'missing_uv_corners':len(missing),'missing_area_fraction':float(area[np.unique(missing//3)].sum()/area.sum())}
(P/'work/retexture_correspondence.json').write_text(json.dumps(correspondence,indent=2)+'\n')
data=np.load(P/'work/uv3d.npz')
parts,xyz=rasterise(data,tol=0,values=np.arange(len(data['uv'])))
valid=parts>=0
_,inds=ndimage.distance_transform_edt(~valid,return_indices=True)
def pad(a):return a[tuple(inds)]
S=P/'meshy/retexture_v1'
base=pad(load(S/'texture_urls_0_base_color.png'));normal=pad(load(S/'texture_urls_0_normal.png'))
ao=pad(load(T/'unicorn_ao.png','L'));rough=pad(load(S/'texture_urls_0_roughness.png','L'))
# Preserve the authored surface and repair only negligible service-omitted charts after the area check.
bad=np.isin(parts,np.unique(missing//3))&valid
good=valid&~bad
known=np.array(np.nonzero(good)).T
_,nearest=cKDTree(xyz[good]).query(xyz[bad])
source=tuple(known[nearest].T)
base[bad]=base[source];rough[bad]=rough[source];normal[bad]=(.5,.5,1)
base=pad(base);rough=pad(rough);normal=pad(normal)
# The native tiers share palette 544; one coat/hair ramp set serves all three sizes.
h,s,v=hsv(base);x,y,z=xyz.transpose(2,0,1)
hair=((y>.295)|((y>-.33)&(y<-.085)&(z>.49)))&valid
hard=((z<.038)|((y<-.402)&(z>.565)))&valid
eye=(y<-.33)&(z>.51)&(z<.585)&(np.abs(x)>.015)&(v<.22)&valid
coat=valid&~(hair|hard|eye)
labels=np.select([eye,hard,hair],[6,4,2],default=1).astype(np.uint8)
ao=ndimage.gaussian_filter(ao,1)
base=np.clip(base*(.82+.18*ao[...,None]),30/255,243/255)
weights=[pad(w.astype(float)) for w in (coat,hair)]
weights=[ndimage.gaussian_filter(w,.65) for w in weights]
Image.fromarray(np.uint8(base*255+.5)).save(T/'unicorn_basecolor.png')
Image.fromarray(np.uint8(normal*255+.5)).resize((1024,1024),Image.Resampling.LANCZOS).save(T/'unicorn_normal_1k.png')
rough=np.where(pad(eye),.22,np.where(pad(hard),.48,np.where(pad(hair),.86,.79)))
spec=np.where(pad(eye),.65,np.where(pad(hard),.5,np.where(pad(hair),.12,.18)))*(.5+.5*ao)
mr=np.stack([spec,rough,np.zeros_like(spec)],-1)
Image.fromarray(np.uint8(mr*255+.5)).resize((1024,1024),Image.Resampling.BOX).save(T/'unicorn_metal_rough_1k.png')
Image.fromarray(pad(labels),'L').resize((1024,1024),Image.Resampling.NEAREST).save(T/'unicorn_material_classes.png')
write_mask(weights,T/'unicorn_region_mask.png')
from region_variants import fit_ramps
ramps={'unicorn':[]};report={}
for i,weight in enumerate(weights):
    fitted,error=fit_ramps(base,{'unicorn':base},weight)
    ramps['unicorn'].append(fitted['unicorn']);report[str(i)]=error
(T/'unicorn_ramps.json').write_text(json.dumps({'variants':['unicorn'],'materials':[{'base':'Unicorn_A','prefix':'Unicorn','mask':'unicorn_region_mask.png','ramps':ramps}]},indent=2)+'\n')
(T/'compose_report.json').write_text(json.dumps({'uv_and_geometry_return':correspondence,'regions':['coat','mane and tail'],'palette_ids':[544],'tier_difference':'size only, shared native palette','ramp_fit':report,'material':'MR red specular mask, green roughness, blue zero metallic; separate AO source'},indent=2)+'\n')
print(json.dumps(report,indent=2))
