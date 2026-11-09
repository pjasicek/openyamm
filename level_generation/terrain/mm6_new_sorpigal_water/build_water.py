"""Bake one AI water master into a coherent loop and exact-master dirt shore overlays."""
import collections
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, map_coordinates

P=Path(__file__).resolve().parent
C=P.parent/'mm6_new_sorpigal'
L=P.parent/'mm6_new_sorpigal_transitions'
OUT=P/'runtime_x2/worlds/mm6/terrain_x2'
N=512

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def edge(a,side):return {'N':lambda:a[0], 'S':lambda:a[-1], 'W':lambda:a[:,0], 'E':lambda:a[:,-1]}[side]()
def strip(a,side,i):return {'N':lambda:a[i], 'S':lambda:a[-1-i], 'W':lambda:a[:,i], 'E':lambda:a[:,-1-i]}[side]()
def signed(a):return distance_transform_edt(a)-distance_transform_edt(~a)
def lock_wrap(a):
 a=a.astype(float).copy()
 for axis in [0,1]:
  for i in range(24):
   w=1 if i<8 else float(smooth((24-i)/16))
   u,v=(a[i],a[-1-i]) if axis==0 else (a[:,i],a[:,-1-i])
   avg=(u+v)/2;u[:]=u*(1-w)+avg*w;v[:]=v*(1-w)+avg*w
 return a

def save(a,path,size=256):
 im=Image.fromarray(np.uint8(np.clip(np.rint(a),0,255)))
 if im.size!=(size,size):im=im.resize((size,size),Image.Resampling.LANCZOS)
 im.save(path);return np.array(im)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 author=P/'authoring/v1';author.mkdir(parents=True,exist_ok=True)
 reports=P/'reports';reports.mkdir(exist_ok=True)
 cat=json.loads((C/'catalogue.json').read_text())
 shores=[t for t in cat['tiles'] if t['family']=='shoreline']
 dirt=np.array(Image.open(L/'material_seams/connected_v2/dirt.png').convert('RGB'),dtype=float)
 master=np.array(Image.open(P/'raw/water_v1.png').convert('RGB').resize((N,N),Image.Resampling.LANCZOS),dtype=float)
 master=lock_wrap(master)
 save(master,author/'water_master.png',N)
 yy,xx=np.mgrid[:N,:N];u=xx/(N-1);v=yy/(N-1)
 frames=[]
 for f in range(14):
  phase=2*np.pi*f/14
  # Spatially periodic, temporally closed deformation of the same master; no independent frame inventions.
  dx=5*np.sin(2*np.pi*v+phase)+2*np.sin(4*np.pi*(u+v)-phase)
  dy=4*np.sin(2*np.pi*u-phase)+2*np.sin(4*np.pi*(u-v)+phase)
  warped=np.stack([map_coordinates(master[:,:,c],[yy+dy,xx+dx],order=1,mode='grid-wrap') for c in range(3)],axis=2)
  warped=lock_wrap(warped)
  name=f'6hdwtr{f:03}'
  save(warped,author/(name+'.png'),N)
  frames.append(save(warped,OUT/(name+'.png')))
 Image.fromarray(frames[0]).save(OUT/'6wtrtyl.png')
 # Shore coverage comes from native alpha; only narrow shared-edge repairs and subpixel softening are applied.
 native={t['name']:np.array(Image.open(C/t['shore_alpha']).resize((N,N),Image.Resampling.NEAREST))>127 for t in shores}
 dist={n:signed(a) for n,a in native.items()}
 groups=collections.defaultdict(list);keys={}
 for n,a in native.items():
  for side in 'NSWE':
   e=edge(a,side);key=('H' if side in 'NS' else 'V',bool(e[0]),bool(e[-1]))
   keys[n,side]=key
   groups[key].append(edge(dist[n],side))
 profiles={}
 for key,values in groups.items():
  if key[1]==key[2]:profile=np.full(N,N if key[1] else -N,dtype=float)
  else:
   crossing=int(np.median([np.argmin(abs(e)) for e in values]))
   profile=(crossing-np.arange(N) if key[1] else np.arange(N)-crossing).astype(float)
  profiles[key]=profile
 # Shared premultiplied colour/alpha profiles are fixed at borders; land-only sides are EXACT accepted dirt.
 coverage={};results={};changes=[]
 for n,a in native.items():
  d=dist[n].copy()
  for side in 'NSWE':
   p=profiles[keys[n,side]]
   for i in range(64):
    w=1 if i<8 else float(smooth((64-i)/56))
    s=strip(d,side,i);s[:]=s*(1-w)+p*w
  alpha=smooth((d+1.5)/3)
  # Exact accepted dirt phase everywhere; a local contact shade, never replacement earth artwork.
  shade=1-.18*np.exp(-np.maximum(d,0)/10)
  rgb=dirt*shade[:,:,None]
  for side in 'NSWE':
   key=keys[n,side];p=profiles[key]
   pa=smooth((p+1.5)/3)
   ps=1-.18*np.exp(-np.maximum(p,0)/10)
   if key[1] and key[2]:ps=np.ones(N)
   for i in range(32):
    w=1 if i<8 else float(smooth((32-i)/24))
    s=strip(rgb,side,i);s[:]=s*(1-w)+strip(dirt,side,i)*ps[:,None]*w
  rgba=np.dstack([rgb,alpha*255])
  save(rgba,author/(n+'.png'),N)
  # Pillow RGBA downsampling uses premultiplied alpha, avoiding transparent-pixel colour halos.
  results[n]=save(rgba,OUT/(n+'.png'))
  coverage[n]=alpha
  changed=np.count_nonzero((alpha>.5)!=a)
  changes.append({'tile':n,'coverage_pixels_changed':int(changed),'coverage_fraction_changed':changed/(N*N),
                  'source_alpha_sha256':digest(C/'alpha/shore_visible'/(n+'.png'))})
 def composite(name,frame):
  if name=='6wtrtyl':return frame
  if name in results:
   rgba=results[name].astype(float);a=rgba[:,:,3:]/255
   return np.uint8(np.rint(rgba[:,:,:3]*a+frame*(1-a)))
  return np.array(Image.open(L/'runtime_x2/worlds/mm6/terrain_x2'/(name+'.png')).convert('RGB'))
 grid=json.loads((P/'corrected_map_cells.json').read_text())
 counts=collections.Counter()
 for y,row in enumerate(grid):
  for x,n in enumerate(row):
   for dx,dy,side in [(1,0,'E'),(0,1,'S')]:
    if y+dy<len(grid) and x+dx<len(row):
     b=grid[y+dy][x+dx]
     if n in results or b in results or n=='6wtrtyl' or b=='6wtrtyl':counts[n,side,b]+=1
 checks=[]
 for (n,side,b),count in sorted(counts.items()):
  maxdiff=0
  for frame in frames:
   aa=composite(n,frame).astype(int);bb=composite(b,frame).astype(int)
   maxdiff=max(maxdiff,int(np.abs(edge(aa,side)-edge(bb,'W' if side=='E' else 'N')).max()))
  checks.append({'a':n,'side':side,'b':b,'placements':count,'max_rgb_difference':maxdiff,'pass':maxdiff<=1})
 # All native three-by-three shore contexts, across all fourteen frames.
 context_frames=[]
 for f,frame in enumerate(frames):
  sheet=Image.new('RGB',(4*384,3*410),'#202933');draw=ImageDraw.Draw(sheet)
  for i,t in enumerate(shores):
   x=i%4*384;y=i//4*410;draw.text((x+5,y+5),t['name'],fill='white')
   for cy,row in enumerate(t['context_tiles']):
    for cx,name in enumerate(row):sheet.paste(Image.fromarray(composite(name,frame)).resize((128,128)),(x+cx*128,y+26+cy*128))
  context_frames.append(sheet)
 context_frames[0].save(reports/'shore_contexts_v1.png')
 context_frames[0].save(reports/'shore_contexts_v1.webp',save_all=True,append_images=context_frames[1:],duration=117,loop=0,lossless=True)
 repeat=[]
 for frame in frames:
  im=Image.fromarray(np.tile(frame,(3,3,1)));repeat.append(im)
 repeat[0].save(reports/'water_repeat_v1.png')
 repeat[0].save(reports/'water_loop_v1.webp',save_all=True,append_images=repeat[1:],duration=117,loop=0,lossless=True)
 fs=Image.new('RGB',(7*256,2*280),'#202933');draw=ImageDraw.Draw(fs)
 for i,frame in enumerate(frames):fs.paste(Image.fromarray(frame),(i%7*256,i//7*280+24));draw.text((i%7*256+5,i//7*280+5),str(i),fill='white')
 fs.save(reports/'animation_frames_v1.png')
 delta=[float(np.abs(frames[(i+1)%14].astype(float)-frames[i]).mean()) for i in range(14)]
 report={'version':'v1','runtime_size':256,'authoring_size':512,'shore_tiles':12,'water_frames':14,
  'water_master':'raw/water_v1.png','dirt_source':str(L/'material_seams/connected_v2/dirt.png'),
  'dirt_sha256':digest(L/'material_seams/connected_v2/dirt.png'),'shore_method':'Exact accepted dirt with a narrow 18% contact shade; no generated bank material used',
  'coverage_repairs':changes,'checks':checks,'failures':[c for c in checks if not c['pass']],
  'animation':{'frame_ticks':15,'ticks_per_second':128,'loop_seconds':210/128,'method':'One AI master, periodic deformation, no runtime shader changes','successive_mean_abs_rgb':delta,'wrap_step_ratio_to_mean':delta[-1]/np.mean(delta),
   'frame_luminance_means':[float(f.mean()) for f in frames],
   'all_frame_opposite_edges_equal':all(np.array_equal(f[0],f[-1]) and np.array_equal(f[:,0],f[:,-1]) for f in frames)},
  'files':{f.name:digest(f) for f in sorted(OUT.glob('*.png'))}}
 (reports/'validation_v1.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'tiles':len(report['files']),'joins':len(checks),'failures':report['failures'],'animation':report['animation']},indent=2))

if __name__=='__main__':main()
