"""Keep the selected head and native ramps, and compose independent 1K stone body/wing maps."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';W=P/'work/parts_v5';SIZE=1024
assert (W/'texture_correspondence.json').is_file()
sys.path[:0]=[str(P.parent/'claude_shared'),str(Path('tools').resolve())]
import tier_textures as tier
from normal_map_convention import measure
spec=importlib.util.spec_from_file_location('raster',P.parent/'mm6_gob_claude/scripts/compose_textures_v2.py');raster=importlib.util.module_from_spec(spec);spec.loader.exec_module(raster);raster.SIZE=SIZE
def load(path,mode='RGB'):return np.array(Image.open(path).convert(mode).resize((SIZE,SIZE),Image.Resampling.LANCZOS),np.float32)/255
def save(a,path):Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8)).save(path)
config=json.loads((T/'gar_ramps.json').read_text());ramps=config['materials'][0]['ramps'];report={}
head=load(T/'head_basecolor.png');headregion=np.array(Image.open(T/'head_regions.png'))[:,:,0]>.9*255
target_gray=float(np.median((head@tier.LUMA)[headregion]))
for part in ['body','wings']:
 src=P/f'meshy/{part}_texture_v5';data=np.load(W/(part+'_uv3d.npz'));regions,xyz=raster.rasterise(data,tol=0);valid=regions>=0
 interior=ndimage.binary_erosion(valid,iterations=1);_,ind=ndimage.distance_transform_edt(~interior,return_indices=True)
 def pad(a):return a[tuple(ind)]
 raw=load(src/'texture_urls_0_base_color.png');gray=raw@tier.LUMA
 # Match neutral stone brightness at the part boundaries without flattening the generated detail.
 shift=target_gray-float(np.median(gray[interior]));base=np.repeat(np.clip(pad(gray)+shift,0,1)[...,None],3,axis=2)
 mask=np.zeros((SIZE,SIZE,4));mask[:,:,0]=1;save(mask,T/f'{part}_regions.png');save(base,T/f'{part}_basecolor.png')
 detail=load(src/'texture_urls_0_normal.png')*2-1;correlation=measure(np.array(Image.open(src/'texture_urls_0_normal.png').convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS)))
 flip=correlation<-.1
 if flip:detail[...,1]*=-1
 detail=pad(detail);detail[...,:2]*=.55;detail/=np.maximum(np.linalg.norm(detail,axis=-1,keepdims=True),1e-8);save(detail*.5+.5,T/f'{part}_normal.png')
 rough=np.clip(pad(load(src/'texture_urls_0_roughness.png','L')),.78,.97)
 save(np.stack([np.full_like(rough,.045),rough,np.zeros_like(rough)],-1),T/f'{part}_metal_rough.png')
 Image.fromarray(np.full((SIZE,SIZE),3 if part=='wings' else 1,np.uint8)).save(T/f'{part}_classes.png')
 for variant in ramps:save(tier.apply(base,mask,ramps[variant]),T/f'{part}_{variant}.png')
 entry={'base':'Gargoyle'+part.title(),'prefix':'Gargoyle'+part.title(),'mask':f'{part}_regions.png','ramps':ramps}
 config['materials']=[m for m in config['materials'] if m['base']!=entry['base']]+[entry]
 report[part]={'resolution':SIZE,'occupied_texels':int(valid.sum()),'source':part+'_texture_v5','normal_green_flipped':bool(flip),'normal_correlation':correlation,'brightness_shift':shift}
 assert np.isfinite(base).all() and np.isfinite(detail).all()
(T/'gar_ramps.json').write_text(json.dumps(config,indent=2));(W/'composition.json').write_text(json.dumps(report,indent=2));print('PART_TEXTURES',report)
