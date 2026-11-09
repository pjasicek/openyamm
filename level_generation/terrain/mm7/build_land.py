"""Recover MM7 material coverage and original contact treatment; connect scalar edge profiles."""
import collections,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,distance_transform_edt
from common import *
from inventory import GROUPS
spec=importlib.util.spec_from_file_location('native_recovery',T/'mm6_remaining/transitions/build.py')
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
edge=recovery.edge;line=recovery.line;connect=recovery.connect

def classify(a,side):
 e=edge(a,side)
 # Four-way corners identify land boundaries; roads can also cross at the centre.
 bits=''.join(str(int(np.mean(e[lo:hi])>.5)) for lo,hi in [(8,40),(224,288),(472,504)])
 return bits

def road_contact(a):
 solid=a>.5
 if not solid.any() or solid.all():return np.ones_like(a)
 # A narrow shadow beds the stones into earth, without blurring the material.
 distance=distance_transform_edt(solid)+distance_transform_edt(~solid)-1
 return 1-(.20*(1-a)+.10*a)*np.exp(-(distance/6)**2)

def main():
 inv=json.loads((P/'inventory.json').read_text());native_d=read(P/'references/7dirttyl.png');dirt=read(M/'materials/dirt.png')
 mats={g:read(M/'materials'/f'{g}.png') for g in ('grass','sand','snow','swamp','waste','roads')}
 natives={g:read(P/'references'/(GROUPS[g][0]+'.png')) for g in mats if g!='roads'}
 fields={};measurements=collections.defaultdict(list)
 for r in inv['tiles']:
  if r['kind'] not in ('transition','shore'):continue
  n,g=r['name'],r['family'];o=read(P/'references'/f'{n}.png')
  if g=='shore':
   solid=~((o[:,:,0]>240)&(o[:,:,1]<10)&(o[:,:,2]>240))
   a=np.clip(up(solid.astype(float)),0,1)
   # Native palette carries a desaturated ochre/grey wet fringe. Transfer a smooth
   # per-channel multiplicative field, keeping the accepted dirt untouched inland.
   ratio=o/np.maximum(native_d,1);ratio[~solid]=1
   bank=solid & (np.max(abs(o-native_d),2)>4)
   for c in range(3):ratio[:,:,c]=np.where(bank,ratio[:,:,c],1)
   ratio=np.clip(ratio,.45,1.35)
   s=np.stack([up(gaussian_filter(ratio[:,:,c],.6)) for c in range(3)],2)
   error=0.
  elif g=='roads':
   restored=np.load(P/'roads_v4/fields'/f'{n}.npz')
   a=restored['coverage'].astype(float);s=restored['shade'].astype(float);error=0.
  else:
   a,s,error=recovery.recover(o,native_d,natives[g])
   bulk=gaussian_filter(a,8)>.5;inside=distance_transform_edt(bulk);outside=distance_transform_edt(~bulk)
   fi=np.clip((48-inside)/24,0,1);fo=np.clip((48-outside)/24,0,1)
   a=np.where(bulk,1-(1-a)*fi,a*fo);s=1+(s-1)*fi*fo
  topo={side:(classify(a,side) if g=='roads' else classify(a,side)[::2]) for side in 'NSEW'}
  fields[n]=dict(family=g,alpha=a,shade=s,topology=topo,error=error)
  for side,kind in topo.items():measurements[(g,'h' if side in 'NS' else 'v',kind)].append((edge(a,side),edge(s,side)))
 profiles={}
 for key,values in measurements.items():
  g,axis,kind=key
  if g=='roads':
   profiles[key]=(values[0][0],values[0][1]);continue
  if kind in ('00','11','000','111'):
   a=np.full(512,int(kind[0]),float);s=np.ones((512,3) if g=='shore' else (512,))
  else:
   a=np.median(np.stack([v[0] for v in values]),0);s=np.median(np.stack([v[1] for v in values]),0)
   a=gaussian_filter(a,1)
   a[:32]=int(kind[0]);a[-32:]=int(kind[-1]);s[:32]=s[-32:]=1
  profiles[key]=(a,s)
 reports=[]
 for n,f in fields.items():
  g=f['family'];at={};st={}
  for side,kind in f['topology'].items():at[side],st[side]=profiles[(g,'h' if side in 'NS' else 'v',kind)]
  a=connect(f['alpha'].copy(),at);s=connect(f['shade'].copy(),st)
  if g=='roads':a=f['alpha'];s=f['shade']
  save(P/'transitions/masks'/f'{n}.png',a*255);save(P/'transitions/shading'/f'{n}.png',s*200)
  (P/'transitions/fields').mkdir(parents=True,exist_ok=True);np.savez_compressed(P/'transitions/fields'/f'{n}.npz',coverage=a.astype('float32'),shade=s.astype('float32'))
  if g=='roads':
   # roads_v4/compose.py owns the fitted border layer and gutter-aware export.
   result=read(P/'roads_v4/reviews'/f'{n}_runtime.png')
  elif g=='shore':
   rgb=seams.pad(dirt,'wrap')*seams.pad(s,'edge');alpha=seams.pad(a,'edge')
   # Premultiplied filtering prevents fringes from hidden RGB.
   premul=seams.reduce(rgb*alpha[:,:,None]).astype(float)
   coverage=seams.reduce(alpha*255).astype(float)/255
   rgb=seams.reduce(rgb).astype(float);nonzero=coverage>0;rgb[nonzero]=premul[nonzero]/coverage[nonzero,None]
   result=np.dstack([rgb,coverage*255])
  else:
   alpha=seams.pad(a,'edge')[:,:,None]
   rgb=seams.srgb(seams.linear(seams.pad(dirt,'wrap'))*(1-alpha)+seams.linear(seams.pad(mats[g],'wrap'))*alpha)*seams.pad(s,'edge')[:,:,None]
   result=seams.reduce(rgb)
  save(OUT/f'{n}.png',result)
  reports.append(dict(name=n,family=g,topology=f['topology'],reconstruction_mae=f['error'],shade_min=float(s.min()),sha256=sha(OUT/f'{n}.png')))
 for g in ('grass','sand','snow','swamp','waste','roads','shore'):
  members=[r for r in reports if r['family']==g];sheet=Image.new('RGB',(1024,280*len(members)),'#202933');draw=ImageDraw.Draw(sheet)
  for row,r in enumerate(members):
   n=r['name'];ims=[Image.open(P/'references'/f'{n}.png').resize((256,256)),Image.open(OUT/f'{n}.png'),Image.open(P/'transitions/masks'/f'{n}.png').resize((256,256)),Image.open(P/'transitions/shading'/f'{n}.png').resize((256,256))]
   for col,im in enumerate(ims):sheet.paste(im,(col*256,row*280+24));draw.text((col*256+4,row*280+5),n+' '+['original','x2','coverage','shade'][col],fill='white')
  (P/'transitions/sheets').mkdir(exist_ok=True);sheet.save(P/'transitions/sheets'/f'{g}.png')
 (P/'transitions/build.json').write_text(json.dumps(dict(tiles=reports,method='Native MM7 coverage/contact fields, connected by measured axis and topology; fixed restored material phase; premultiplied shore filtering.'),indent=2)+'\n')
 (P/'transitions/edge_profiles.json').write_text(json.dumps({':'.join(k):dict(coverage=a.tolist(),shade=s.tolist()) for k,(a,s) in profiles.items()},indent=2)+'\n')
 print('Built',len(reports),'transitions')
if __name__=='__main__':main()
