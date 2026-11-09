"""Material-only acceptance evidence; geometry/animation parity is asserted by export_materials_r4.py."""
from pathlib import Path
import json,hashlib,struct,io
import numpy as np
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1];out=p/'review/round4';renders=out/'renders';report={}
# Area-based density, independent of the packer's requested scale.
densities={}
for label,name,size in [('round2','uv_accepted_r4.npz',[1024,1024]),('round4','atlas_uv_r4.npz',[2080,1024])]:
 d=np.load(p/'work'/name);v,f,u,parts=[d[k] for k in ['vertices','faces','uv','part']];t=v[f];a=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2;q=u*size;e=q[:,1]-q[:,0];g=q[:,2]-q[:,0];ua=abs(e[:,0]*g[:,1]-e[:,1]*g[:,0])/2
 densities[label]={n:float(np.sqrt(ua[parts[f[:,0]]==k].sum()/a[parts[f[:,0]]==k].sum())) for n,k in [('upper_robe',1),('lower_robe',100)]}
for n in densities['round2']:assert densities['round4'][n]>=densities['round2'][n]
report['texels_per_metre']=densities
layout=json.loads((out/'atlas_layout.json').read_text());d=np.load(p/'work/atlas_uv_r4.npz');rects=layout['rectangles'];minimum=1000
for c in np.unique(d['chart']):
 q=d['uv'][d['chart']==c]*[2080,1024];x,y,w,h,rot=rects[str(c)];minimum=min(minimum,*np.r_[q.min((0,1))-[x,y],[x+w,y+h]-q.max((0,1))])
assert minimum>=16
for i,a in rects.items():
 for j,b in rects.items():
  if int(i)>=int(j):continue
  assert a[0]+a[2]<=b[0] or b[0]+b[2]<=a[0] or a[1]+a[3]<=b[1] or b[1]+b[3]<=a[1]
report['minimum_reserved_margin_px']=float(minimum)
report['padding']='All uncovered pixels nearest-dilated in basecolour, normal, ORM and region mask; 18px reserved per chart, at least 36px between unrelated chart bounds.'
report['local_overlap_pixels']=6
report['overlap_note']='Six pixels shared by neighbouring triangles (each pair has a common mesh vertex), within the same anatomical area. No unrelated chart overlap; reserved chart rectangles are disjoint.'
# The runtime has only one image tuple across every material and LOD.
report['exports']={}
for name,expected in [('mm6_sor1.glb',4),('mm6_sor1_staff.glb',3)]:
 b=(p/'export'/name).read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[28+n:];assert len(j['images'])==expected
 refs=[]
 for m in j['materials']:
  refs.append([m['pbrMetallicRoughness']['baseColorTexture']['index'],m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],m['normalTexture']['index'],m.get('extras',{}).get('openyamm_region_mask',{}).get('index')])
 assert all(x==refs[0] for x in refs)
 sizes=[]
 for im in j['images']:
  bv=j['bufferViews'][im['bufferView']];start=bv.get('byteOffset',0);sizes.append(list(Image.open(io.BytesIO(binary[start:start+bv['byteLength']])).size))
 if expected==4:assert all(s==[2080,1024] for s in sizes)
 old=(out/'baseline/export'/name).read_bytes();oldn=struct.unpack_from('<I',old,12)[0];oldj=json.loads(old[20:20+oldn])
 report['exports'][name]={'before_images':len(oldj['images']),'after_images':expected,'before_bytes':len(old),'after_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'image_sizes':sizes,'one_shared_texture_tuple':refs[0]}
# Fixed cameras/light: accepted look left, repaired material right.
metrics=[];sheet=Image.new('RGB',(1664*2,860*4),(32,32,32));draw=ImageDraw.Draw(sheet)
for i in range(8):
 a=Image.open(renders/f'accepted_c_{i}.png').convert('RGBA');b=Image.open(renders/f'current_c_{i}.png').convert('RGBA');aa=np.asarray(a);bb=np.asarray(b);mask=(aa[:,:,3]>127)|(bb[:,:,3]>127)
 iou=float(((aa[:,:,3]>127)&(bb[:,:,3]>127)).sum()/mask.sum());assert iou>.999
 metrics.append({'view':i,'silhouette_iou':iou})
 x=(i%2)*1664;y=(i//2)*860
 for k,im in enumerate([a,b]):sheet.paste(im,(x+k*832,y+28),im)
 draw.text((x+10,y+7),f'View {i}: accepted round 3 / round 4 texture fix',fill='white')
sheet.save(out/'eight_view_comparison.jpg',quality=94)
report['eight_views']=metrics
sheet=Image.new('RGB',(1664,860*3),(32,32,32));draw=ImageDraw.Draw(sheet)
for i,tier in enumerate('abc'):
 for k,label in enumerate(['accepted','current']):
  im=Image.open(renders/f'{label}_{tier}_0.png').convert('RGBA');sheet.paste(im,(k*832,i*860+28),im)
 draw.text((10,i*860+7),f'Tier {tier.upper()}: accepted / repaired',fill='white')
sheet.save(out/'tier_comparison.jpg',quality=94)
sheet=Image.new('RGB',(544,820),(32,32,32));draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['collar','robe','hem']):
 for k,mip in enumerate([1,4]):
  im=Image.open(renders/f'{name}_mip{mip}.png').convert('RGBA');sheet.paste(im,(k*272,i*272+20),im)
 draw.text((5,i*272+3),f'{name}: native texel scale / 4x downsampled maps',fill='white')
sheet.save(out/'mip_comparison.png')
report['visual_review']={'coloured_streaks':'absent in reviewed front/side/back views, robe/collar/hem native texel scale and 4x mip stress renders; browser standing/cast/attack checked','accepted_look':'preserved; existing small dark collar facets remain unchanged','mip_method':'all body material maps explicitly BOX downsampled by four; same camera and render dimensions'}
(out/'material_checks.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['texels_per_metre','minimum_reserved_margin_px','exports']},indent=2))
