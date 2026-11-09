"""Paired real-map views for the materials beyond Emerald Island, including underwater Shoals."""
import argparse,json,subprocess,sys
from common import *
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quality',choices=['x1','x2'],required=True);ap.add_argument('--map');args=ap.parse_args()
 inv=json.loads((P/'inventory.json').read_text());grids=json.loads((P/'grids.json').read_text());poses={}
 for mid,name in [('7out06','7sand'),('out10','7snow'),('7out05','7wastetile'),('7out13','7swtyl'),('7out15','7sand')]:
  if args.map and mid!=args.map:continue
  m=next(m for m in inv['maps'] if m['id']==mid);d=parse_odm_file(ROOT/m['source'])['payload'];grid=grids[mid]
  candidates=[(y,x) for y in range(8,119) for x in range(8,119) if grid[y][x]==name]
  if not candidates:candidates=[(y,x) for y in range(8,119) for x in range(8,119) if grid[y][x]!='7wtrtyl']
  def score(pos):
   y,x=pos;region=[n for rr in grid[y-3:y+4] for n in rr[x-3:x+4]]
   heights=[d['height_map'][yy*128+xx] for yy in range(y-2,y+3) for xx in range(x-2,x+3)]
   span=max(heights)-min(heights)
   return (int(span<=4),region.count(name),-span,min(len(set(region)),5),-abs(x-64)-abs(y-64))
  if mid in ('out10','7out05'):y,x=max(candidates,key=score)
  else:
   y,x=max(candidates,key=lambda pos:(min(len({n for rr in grid[pos[0]-3:pos[0]+4] for n in rr[pos[1]-3:pos[1]+4]}),5),sum(n==name for rr in grid[pos[0]-3:pos[0]+4] for n in rr[pos[1]-3:pos[1]+4]),-abs(pos[1]-64)-abs(pos[0]-64)))
  height=max(d['height_map'][yy*128+xx] for yy in (y,y+1) for xx in (x,x+1))*32
  pose=[(x+.5-64)*512,(64-y-.5)*512,height+161,1.5707963268,-.48]
  poses[mid]=dict(tile=name,column=x,row=y,pose=pose)
  mode='original' if args.quality=='x1' else 'enhanced'
  cmd=['python3',str(ROOT/'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),'mm7_real_'+mid+'_'+args.quality,'--world','mm7','--map',mid+'.odm','--stage','/tmp/openyamm-mm7-terrain-review/'+mode,'--binary','/tmp/openyamm-mm7-terrain-review/openyamm','--review-directory',str(P/'captures'),'--pose',*[str(v) for v in pose],'--warmup','1','--seconds','0']
  if mid=='7out15':cmd+=['--party-file',str(P/'fixture/shoals_party.json')]
  with (P/'captures'/f'capture_real_{mid}_{args.quality}.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
  print('Captured',mid,args.quality,flush=True)
 path=P/'reports'/f'real_map_poses_{args.quality}.json'
 old=json.loads(path.read_text()) if path.exists() else {}
 old.update(poses);path.write_text(json.dumps(old,indent=2)+'\n')
if __name__=='__main__':main()
