"""Grade the new AI texture to dull steel; retain wear and material-specific roughness."""
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,accessor_array
M=P/'meshy/sword_retexture_round1';T=P/'textures/sword_round1';T.mkdir(exist_ok=True);uv=np.load(P/'work/round1/sword_uv.npz');valid=uv['parts']>=0;near=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True);classes=uv['classes'][tuple(near)];metal=classes==9
src,sb=read_glb(P/'work/round1/sword_upload.glb');ret,rb=read_glb(M/'model_urls_glb.glb');a=src['meshes'][0]['primitives'][0];b=ret['meshes'][0]['primitives'][0]
for attr in ['TEXCOORD_0']:
 sa=accessor_array(src,sb,a['attributes'][attr])[accessor_array(src,sb,a['indices']).ravel()];ra=accessor_array(ret,rb,b['attributes'][attr])[accessor_array(ret,rb,b['indices']).ravel()];assert np.array_equal(sa,ra),'Retexture changed uploaded UVs'
def load(name):return np.array(Image.open(M/f'texture_urls_0_{name}.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),float)/255
base=load('base_color');base*=np.where(metal,.82,1.)[...,None];normal=load('normal');rough=load('roughness')[...,0];rough=np.where(metal,np.clip(rough*.75+.20,.45,.72),np.clip(rough,.73,.90));spec=np.where(metal,.65,.035);mr=np.stack([spec,rough,load('metallic')[...,0]],-1)
for name,x in [('basecolor_1k.png',base),('normal_1k.png',normal),('metal_rough_1k.png',mr)]:Image.fromarray(np.uint8(np.clip(x,0,1)*255+.5)).save(T/name)
Image.fromarray(classes).save(T/'material_classes_1k.png');report={'uv_per_corner_identical_to_upload':True,'basecolor_metal_grade':.82,'steel_rgb_median':np.median(base[valid&metal],axis=0).tolist(),'steel_rgb_p95':np.percentile(base[valid&metal],95,axis=0).tolist(),'texture_dimension':1024,'roughness_metal_range':[.45,.72],'roughness_leather_range':[.73,.90],'MR_red':'specular mask: metal .65, leather .035','shared_steel_colour_all_tiers':True};(P/'review/round1/texture_validation.json').write_text(json.dumps(report,indent=2));print(report)
