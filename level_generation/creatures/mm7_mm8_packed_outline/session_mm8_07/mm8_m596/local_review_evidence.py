"""MM8 local review contacts and final atlas contour audit; writes only assigned staging families."""
from pathlib import Path
import json,sys,hashlib,math
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT.parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d): p.write_text(json.dumps(d,indent=2)+'\n')
def strips(stem):
 o=ROOT/f'mm8_{stem}'/'redo_2x';d=json.loads((o/'review/material_checks.json').read_text());pages=d['pages'];count=5 if len(d['all_native_palettes'])==1 else 2;result=[]
 for start in range(0,len(pages),count):
  ps=pages[start:start+count];ims=[Image.open(REPO/p['path']).convert('RGB') for p in ps];im=Image.new('RGB',(sum(x.width for x in ims),max(x.height for x in ims)),(40,40,40));x=0
  for ii in ims:im.paste(ii,(x,0));x+=ii.width
  p=o/'review'/f'material_strip_{start//count:02d}.png';im.save(p);result.append(dict(path=str(p.relative_to(o)),sha256=sha(p),source_pages=ps,frames=[n for pp in ps for n in pp['frames']]))
 save(o/'review/material_strips.json',dict(status='visual_review_pending',pages=result,artwork_resized=False))
 print(stem,'material strips',len(result))

def edges(stem):
 o=ROOT/f'mm8_{stem}'/'redo_2x';manifest=json.loads((o/'draft_manifest.json').read_text());run=json.loads((o/'run.json').read_text())
 sys.path.insert(0,str(REPO/'level_generation/creatures/mm6_peasants'))
 from package_family import edge_stats
 audit={};patches=[]
 for job in run['jobs']:
  if not job.get('selected_raw'):continue
  report=json.loads((o/'review'/f"{job['id']}_extraction.json").read_text())
  assert report['raw']==job['selected_raw']
  for frame in report['frames']:
   path=REPO/frame['clean_path'];im=Image.open(path).convert('RGBA');stats=edge_stats(im,'magenta')
   audit['clean:'+job['id']+':'+frame['frame']]=dict(path=str(path.relative_to(o)),sha256=sha(path),**stats)
   patches.append((stats['max_score'],'clean '+frame['frame'],im.copy(),stats['position']))
 pages={i:Image.open(o/p['base']).convert('RGBA') for i,p in enumerate(manifest['pages'])}
 for name,frame in manifest['frames'].items():
  x,y,w,h=frame['atlas_xywh'];im=pages[frame['page']].crop((x,y,x+w,y+h));stats=edge_stats(im,'magenta')
  audit['atlas:'+name]=dict(page=frame['page'],atlas_xywh=frame['atlas_xywh'],**stats)
  patches.append((stats['max_score'],'atlas '+name,im,stats['position']))
 selected=sorted(patches,key=lambda x:x[0],reverse=True)[:8];panel=Image.new('RGB',(1072,308),'#333333');dr=ImageDraw.Draw(panel);evidence=[]
 for i,(score,label,im,center) in enumerate(selected):
  x=i%4*268;y=i//4*154;dr.text((x+3,y+3),f'{label} score {score:.1f}',fill='white');cx,cy=center;rect=[cx-64,cy-64,cx+64,cy+64];patch=im.crop(rect)
  for side,col in enumerate(['#262a28','#eee9df']):
   bg=Image.new('RGBA',(128,128),col);bg.alpha_composite(patch);panel.paste(bg,(x+side*134,y+22))
  evidence.append(dict(label=label,score=score,position=center,rectangle=rect))
 path=o/'review/final_atlas_edge_100pct.png';panel.save(path)
 save(o/'review/final_edge_checks.json',dict(status='visual_review_pending',frames=audit,cleaned_pose_instances=sum(k.startswith('clean:') for k in audit),atlas_frames=len(manifest['frames']),all_atlas_frames_scanned=True,band_physical_px=4,method='Shared alpha-weighted magenta excess within four pixels of the visible contour, including alpha below 128. Hidden RGB ignored; intended crystal pink is protected and scores are candidates requiring visual inspection.',contact=dict(path=str(path.relative_to(o)),sha256=sha(path),samples=evidence)))
 print(stem,'final edge audit',len(audit))
if __name__=='__main__':
 if sys.argv[1]=='--edges':
  for s in sys.argv[2:]:edges(s)
 else:
  for s in sys.argv[1:]:strips(s)
