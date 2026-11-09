"""Verify exported RGB joins for the corrected map and synthetic legal layouts; emit review mosaics."""
import collections
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--project-directory',type=Path,help='Independent catalogue and report destination')
parser.add_argument('--version',default='v4')
parser.add_argument('--runtime-dir',type=Path,default=P/'runtime_x2/worlds/mm6/terrain_x2')
parser.add_argument('--authoring-dir',type=Path,help='Also verify the512px colour composites')
args=parser.parse_args()
if args.project_directory:P=args.project_directory.resolve(strict=True)
runtime=args.runtime_dir
images={f.stem:Image.open(f).convert('RGB') for f in runtime.glob('*.png')}
assert len(images)==36
arrays={n:np.asarray(im,dtype=int) for n,im in images.items()}
for n,im in images.items():assert im.size==(256,256)
mapgrid=json.loads((P/'corrected_map_cells.json').read_text())
cases=json.loads((P/'test_cases.json').read_text())
counts=collections.Counter()
for grid in [mapgrid]+[c['tiles'] for c in cases if c['group']=='Large legal layouts']:
 for y,row in enumerate(grid):
  for x,a in enumerate(row):
   for dx,dy,axis in [(1,0,'east'),(0,1,'south')]:
    if y+dy>=len(grid) or x+dx>=len(row):continue
    b=grid[y+dy][x+dx]
    if a in images and b in images:counts[a,axis,b]+=1
checks=[]
for (a,axis,b),count in sorted(counts.items()):
 aa,bb=arrays[a],arrays[b]
 diff=np.abs(aa[:,-1]-bb[:,0]) if axis=='east' else np.abs(aa[-1]-bb[0])
 checks.append({'a':a,'direction':axis,'b':b,'count':count,'max_rgb_difference':int(diff.max()),
                'mean_rgb_difference':float(diff.mean()),'pass':bool(diff.max()<=1)})
report={'runtime_tiles':len(images),'unique_join_checks':len(checks),'placed_joins':sum(counts.values()),
        'failures':[c for c in checks if not c['pass']], 'checks':checks,
        'limits':'Pixel boundary equality is structural evidence only; inspect interiors, mipmaps and game views.'}
if args.authoring_dir:
 authored={f.stem:Image.open(f).convert('RGB') for f in args.authoring_dir.glob('*.png')}
 assert set(authored)==set(images)
 assert all(im.size==(512,512) for im in authored.values())
 authored={n:np.asarray(im,dtype=int) for n,im in authored.items()}
 author_checks=[]
 for a,axis,b in sorted(counts):
  aa,bb=authored[a],authored[b]
  diff=np.abs(aa[:,-1]-bb[:,0]) if axis=='east' else np.abs(aa[-1]-bb[0])
  author_checks.append({'a':a,'direction':axis,'b':b,'max_rgb_difference':int(diff.max()),
                        'pass':bool(diff.max()<=1)})
 report['authoring']={'size':512,'checks':len(author_checks),
                      'failures':[c for c in author_checks if not c['pass']]}
 assert not report['authoring']['failures'],report['authoring']['failures'][:5]
(P/'reports'/f'rgb_join_check_{args.version}.json').write_text(json.dumps(report,indent=2)+'\n')
# Render all valid observed pair types as labelled pages, preserving each join at runtime resolution.
pairs=[c for c in cases if c['group']=='Observed pairs' and not c.get('conflict')]
for start in range(0,len(pairs),20):
 sheet=Image.new('RGB',(4*520,5*540),'#202a34');draw=ImageDraw.Draw(sheet)
 for i,c in enumerate(pairs[start:start+20]):
  ox=i%4*520;oy=i//4*540;draw.text((ox+4,oy+4),c['id'],fill='white')
  for y,row in enumerate(c['tiles']):
   for x,name in enumerate(row):sheet.paste(images[name],(ox+x*256,oy+24+y*256))
 sheet.save(P/'reports'/f'pairs_{args.version}_{start//20:02}.png')
for c in cases:
 if c['group']!='Large legal layouts':continue
 image=Image.new('RGB',(len(c['tiles'][0])*256,len(c['tiles'])*256))
 for y,row in enumerate(c['tiles']):
  for x,name in enumerate(row):image.paste(images[name],(x*256,y*256))
 image.save(P/'reports'/(c['id'].replace(':','_')+f'_{args.version}.png'))
print('RGB checks:',len(checks),'unique joins,',len(report['failures']),'failures')
if report['failures']:print(report['failures'][:5]);raise SystemExit(1)

# Small labelled sheets make every pair and original four-tile context reviewable.
for group,stem in [('Observed pairs','pairs'),('Observed 2×2 corners','corners')]:
 selected=[c for c in cases if c['group']==group and (stem=='corners' or not c.get('conflict'))]
 for start in range(0,len(selected),40):
  sheet=Image.new('RGB',(2080,1400),'#29313a');draw=ImageDraw.Draw(sheet)
  for i,c in enumerate(selected[start:start+40]):
   x=i%8*260;y=i//8*280
   if c.get('conflict'):draw.rectangle((x,y,x+259,y+19),fill='#942626')
   draw.text((x+2,y+2),c['id']+(' SOURCE CONFLICT' if c.get('conflict') else ''),fill='white')
   for yy,row in enumerate(c['tiles']):
    for xx,name in enumerate(row):
     if name:sheet.paste(images[name].resize((128,128)),(x+xx*128,y+20+yy*128))
  sheet.save(P/'reports'/f'{stem}_overview_{args.version}_{start//40:02}.png')

for i,(cx,cy) in enumerate([(18,86),(54,91),(57,95),(16,99)],1):
 original=[row[:] for row in mapgrid]
 for change in json.loads((P/'map_corrections/patch.json').read_text())['changes']:
  original[change['row']][change['column']]=change['before']
 sheet=Image.new('RGB',(1536,800),'#29313a');draw=ImageDraw.Draw(sheet)
 for j,grid in enumerate([original,mapgrid]):
  draw.text((j*768+8,8),'Original layout' if j==0 else 'Corrected layout',fill='white')
  for yy in range(6):
   for xx in range(6):
    name=grid[cy-2+yy][cx-2+xx]
    if name in images:sheet.paste(images[name].resize((128,128)),(j*768+xx*128,32+yy*128))
 sheet.save(P/'reports'/f'corrected_context_{i}_{args.version}.png')
