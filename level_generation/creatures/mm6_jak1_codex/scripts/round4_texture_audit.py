import sys,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P/'review/round4';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
report={}
for label,path in [('before',R/'before/export/mm6_jak1_staff.glb'),('after',P/'export/mm6_jak1_staff.glb')]:
 d,b=read_glb(path);q=d['meshes'][0]['primitives'][0];pos=accessor_array(d,b,q['attributes']['POSITION']);uv=accessor_array(d,b,q['attributes']['TEXCOORD_0']);faces=accessor_array(d,b,q['indices']).reshape(-1,3)
 size=np.array([576,1024]if label=='before'else[1024,1024]);xyz=pos[faces];xy=uv[faces]*size
 area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1).sum()/2
 a=xy[:,1]-xy[:,0];c=xy[:,2]-xy[:,0];texarea=np.abs(a[:,0]*c[:,1]-a[:,1]*c[:,0]).sum()/2
 report[label]={'surface_m2':float(area),'surface_texels':float(texarea),'linear_texels_per_m':float(np.sqrt(texarea/area))}
 if label=='before':continue
 parents=list(range(len(faces)))
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 seen={}
 for i,face in enumerate(faces):
  for vertex in face:
   key=tuple(np.round(uv[vertex],7))
   if key in seen:parents[root(i)]=root(seen[key])
   seen[key]=i
 labels=np.array([root(i)for i in range(len(faces))]);cover=np.zeros((1024,1024),np.uint16);occupied=np.zeros_like(cover,bool)
 for island in np.unique(labels):
  mask=Image.new('1',(1024,1024));draw=ImageDraw.Draw(mask)
  for tri in xy[labels==island]:draw.polygon([tuple(x)for x in tri],fill=1)
  a=np.asarray(mask);occupied|=a;cover+=(distance_transform_edt(~a)<=16).astype(np.uint16)
 report['padding']={'islands':len(np.unique(labels)),'border_pixels':float(min(uv.min(),1-uv.max())*1024),'dilation_pixels':16,'overlap_pixels':int((cover>1).sum()),'surface_coverage':float(occupied.mean())}
 normals=np.asarray(Image.open(P/'textures/round4_staff/normal.png').convert('RGB'))
 report['normal']={'occupied_channel_std':normals[occupied].std(0).tolist(),'nonflat_fraction':float((np.linalg.norm(normals[occupied,:2].astype(float)-128,axis=1)>5).mean())}
 assert report['padding']['border_pixels']>=16 and report['padding']['overlap_pixels']==0,report['padding']
(R/'texture_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
