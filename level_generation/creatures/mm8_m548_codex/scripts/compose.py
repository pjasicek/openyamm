"""One shared opaque crystal texture set; native tiers differ only in size."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw,ImageFilter
P=Path(__file__).resolve().parents[1];T=P/'textures';source=P/'meshy/body_texture_v1'
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
from normal_map_convention import measure
im=Image.open(source/'texture_urls_0_base_color.png').convert('RGB');a=np.asarray(im,dtype=float)
# Keep the broad facet contrast; tame generated white highlights before game lighting.
a=np.clip(a*.94,25,243).astype('uint8');Image.fromarray(a).save(T/'crystal_basecolor.png')
normal=Image.open(source/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
n=np.array(normal);correlation=measure(n)
if correlation<-.15:n[:,:,1]=255-n[:,:,1]
Image.fromarray(n).save(T/'crystal_normal.png')
print('NORMAL_CONVENTION',correlation,flush=True)
small=np.array(Image.fromarray(a).resize((1024,1024),Image.Resampling.LANCZOS),dtype=float)
eyes=(small[:,:,0]>1.3*small[:,:,2])&(small[:,:,1]>.65*small[:,:,0])&(small[:,:,1]>1.4*small[:,:,2])
rough=np.full((1024,1024),100,dtype='uint8');rough[eyes]=48
orm=np.stack([np.full_like(rough,220),rough,np.zeros_like(rough)],axis=-1);Image.fromarray(orm).save(T/'crystal_orm.png')
classes=np.full((1024,1024),11,dtype='uint8');classes[eyes]=6;Image.fromarray(classes).save(T/'crystal_material_classes.png')
(T/'material_contract.json').write_text(json.dumps({'palette':548,'same_texture_for_all_tiers':True,'class_11':'solid crystal','base_color_size':list(im.size),'normal_size':[1024,1024],'roughness_crystal':100/255,'roughness_eyes':48/255,'metallic':0,'specular_mask':220/255,'body_alpha':'OPAQUE','head_texture':'Shared 2K atlas with protected detailed head; no skin/face texture set is required for the simple crystal facets.'},indent=2))
print('TEXTURES_COMPOSED',flush=True)
