"""Validate all compatible joins; distinguish original map placement conflicts from asset seams."""
import collections,json,csv
import numpy as np
from PIL import Image,ImageDraw
from common import *
from inventory import GROUPS

def ratios(joined,columns):
 energy=np.mean(np.diff(joined,axis=1)**2,axis=2);e=energy[:,np.asarray(columns)-1]
 near=np.stack([np.mean(np.concatenate([energy[:,c-5:c-1],energy[:,c:c+4]],1),1) for c in columns],1)
 def windows(a):
  integral=np.concatenate([np.zeros((1,a.shape[1])),np.cumsum(a,0)],0);starts=np.arange(0,241,4)
  return (integral[starts+16]-integral[starts])/16
 return np.sqrt(windows(e))/np.maximum(1,np.sqrt(windows(near)))
def metrics(aa,bb,side):
 if side=='S':aa=aa.transpose(1,0,2);bb=bb.transpose(1,0,2)
 joined=np.concatenate([aa,bb],1)
 b=ratios(joined,[256]).ravel();i=ratios(joined,[c for c in range(16,497,16) if c!=256]).ravel()
 bp,bm,ip,im=float(np.percentile(b,95)),float(b.max()),float(np.percentile(i,95)),float(np.percentile(i,99.9))
 return dict(boundary_p95=bp,boundary_max=bm,interior_p95=ip,interior_p999=im,passed=bp<1.25*ip and bm<1.25*im),joined,int(b.argmax())*4

def main():
 inv=json.loads((P/'inventory.json').read_text());build=json.loads((P/'transitions/build.json').read_text());grids=json.loads((P/'grids.json').read_text())
 records={r['name']:r for r in inv['tiles']};meta={}
 for r in build['tiles']:
  g=r['family'];meta[r['name']]={}
  for side,k in r['topology'].items():
   label=('dirt' if k=='11' else 'water') if g=='shore' and k in ('00','11') else 'dirt' if k in ('00','000') else g if k in ('11','111') else g+':'+k
   meta[r['name']][side]=label
 for r in inv['tiles']:
  if r['kind'] in ('base','variant'):meta[r['name']]=dict.fromkeys('NSEW',r['family'])
 original={};tiles={};water=[read(OUT/f'7hdwtr{i:03}.png') for i in range(14)]
 for n,r in records.items():
  if r['kind']=='animation':continue
  im=np.asarray(Image.open(OUT/f'{n}.png'),float)
  tiles[n]=[im[:,:,:3]*(im[:,:,3:]/255)+w*(1-im[:,:,3:]/255) for w in water] if im.shape[2]==4 else water if r['family']=='water' else [im]
  old=read(P/'references'/f'{n}.png',256)
  if r['family']=='shore':
   a=~((old[:,:,0]>240)&(old[:,:,1]<10)&(old[:,:,2]>240));old=old*a[:,:,None]+read(P/'references/7hdwtr000.png',256)*(~a[:,:,None])
  original[n]=old
 opp={'E':'W','S':'N'}
 def compatible(a,s,b):return meta[a][s]==meta[b][opp[s]]
 actual=collections.Counter();locations={};incompatible=[]
 for mid,grid in grids.items():
  for y,row in enumerate(grid):
   for x,a in enumerate(row):
    for s,yy,xx in [('E',y,x+1),('S',y+1,x)]:
     if yy>=127 or xx>=127:continue
     b=grid[yy][xx];key=(a,s,b);actual[key]+=1;locations.setdefault(key,dict(map=mid,row=y,column=x))
     if not compatible(a,s,b):incompatible.append(dict(map=mid,row=y,column=x,a=a,side=s,b=b))
 checks=[];worst=[]
 for a in sorted(meta):
  for b in sorted(meta):
   for side in ('E','S'):
    if not compatible(a,side,b):continue
    for frame in range(max(len(tiles[a]),len(tiles[b]))):
     m,joined,start=metrics(tiles[a][frame%len(tiles[a])],tiles[b][frame%len(tiles[b])],side)
     checks.append(dict(a=a,side=side,b=b,frame=frame,placements=actual[(a,side,b)],**m))
     score=max(m['boundary_p95']/max(m['interior_p95'],1e-6),m['boundary_max']/max(m['interior_p999'],1e-6))
     worst.append((score,f'{a} {side} {b} f{frame}',start,joined));worst=sorted(worst,key=lambda v:-v[0])[:20]
 (P/'reports').mkdir(exist_ok=True);(P/'contexts').mkdir(exist_ok=True)
 sheet=Image.new('RGB',(1024,5*160),'#202933');draw=ImageDraw.Draw(sheet)
 for i,(score,label,start,j) in enumerate(worst):
  x,y=i%4*256,i//4*160;start=max(0,min(start-8,224));draw.text((x+2,y+2),label,fill='white');draw.text((x+2,y+16),'relative %.2f'%score,fill='white');sheet.paste(Image.fromarray(seams.byte(j[start:start+32,224:288])).resize((256,128)),(x,y+32))
 sheet.save(P/'reports/worst_joins.png')
 fixtures={}
 for g in ('grass','sand','snow','swamp','waste','shore'):
  base,pre=GROUPS[g];base=base or '7wtrtyl';d='7dirttyl'
  island=[[d]*5,[d,pre+'nw',pre+'n',pre+'ne',d],[d,pre+'w',base,pre+'e',d],[d,pre+'sw',pre+'s',pre+'se',d],[d]*5]
  hole=[[base]*5,[base,pre+'xse',pre+'s',pre+'xsw',base],[base,pre+'e',d,pre+'w',base],[base,pre+'xne',pre+'n',pre+'xnw',base],[base]*5]
  fixtures[g]=[island,hole]
  for layout in fixtures[g]:
   for y,row in enumerate(layout):
    for x,n in enumerate(row):
     if x<4:assert compatible(n,'E',row[x+1]),(g,n,row[x+1])
     if y<4:assert compatible(n,'S',layout[y+1][x]),(g,n,layout[y+1][x])
  sheet=Image.new('RGB',(1280,664),'#202933');draw=ImageDraw.Draw(sheet)
  for z,grid in enumerate(fixtures[g]):
   draw.text((z*640+5,4),g+[' island',' dirt hole'][z],fill='white')
   for y,row in enumerate(grid):
    for x,n in enumerate(row):sheet.paste(Image.fromarray(seams.byte(tiles[n][0])).resize((128,128)),(z*640+x*128,24+y*128))
  sheet.save(P/'contexts'/f'{g}_flat.png')
 # Native contexts for every used tile, with before/after and map coordinates.
 contexts=[]
 for g in GROUPS:
  members=[n for n,r in records.items() if r['family']==g and r['maps']];sheet=Image.new('RGB',(768,len(members)*408),'#202933');draw=ImageDraw.Draw(sheet)
  for row,n in enumerate(members):
   candidates=[(mid,y,x) for mid,grid in grids.items() for y in range(1,126) for x in range(1,126) if grid[y][x]==n]
   mid,y,x=max(candidates,key=lambda v:len({q for rr in grids[v[0]][v[1]-1:v[1]+2] for q in rr[v[2]-1:v[2]+2]}))
   grid=[rr[x-1:x+2] for rr in grids[mid][y-1:y+2]];contexts.append(dict(tile=n,map=mid,row=y,column=x,grid=grid))
   draw.text((4,row*408+4),f'{n} {mid} ({x},{y}) original / restored',fill='white')
   for z in (0,1):
    for yy,rr in enumerate(grid):
     for xx,name in enumerate(rr):sheet.paste(Image.fromarray(seams.byte(original[name] if z==0 else tiles[name][0])).resize((128,128)),(z*384+xx*128,row*408+24+yy*128))
  sheet.save(P/'contexts'/f'{g}_native.png')
 (P/'reports/flat_fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n');(P/'reports/native_contexts.json').write_text(json.dumps(contexts,indent=2)+'\n')
 with (P/'reports/native_layout_mismatches.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['map','row','column','a','side','b']);w.writeheader();w.writerows(incompatible)
 failures=[r for r in checks if not r['passed']];report=dict(compatible_join_checks=len(checks),failures=failures,checks=checks,native_incompatible_placements=len(incompatible),files={p.name:sha(p) for p in OUT.glob('*.png')},complete_inventory_coverage=set(records)=={p.stem for p in OUT.glob('*.png')})
 (P/'reports/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('checks','files','failures')},indent=2));print('Failures',len(failures),failures[:5])
if __name__=='__main__':main()
