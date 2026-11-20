"""Reuse accepted MM6 road silhouettes; preserve MM7-only diagonal geometry and common openings."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from build_land import connect,edge,road_contact
from scipy.ndimage import gaussian_filter,binary_fill_holes,distance_transform_edt,label
V=P/'roads_v4'
D=T/'mm6_new_sorpigal_dirt_fidelity/transitions/masks/connected_v4'
R=T/'mm6_remaining/transitions/masks'
def alpha(path):return np.asarray(Image.open(path),float)/255

def main():
 records=[r for r in json.loads((P/'transitions/build.json').read_text())['tiles'] if r['family']=='roads']
 profiles={'h':edge(alpha(D/'6drsrns.png'),'N'),'v':edge(alpha(D/'6drsrew.png'),'W')}
 provenance={}
 for r in records:
  n=r['name'];donor='6'+n[1:];src=D/(donor+'.png')
  if not src.exists():src=R/(donor+'.png')
  if src.exists():
   a=alpha(src);method='Accepted MM6 silhouette'
   if n=='7drsrncap':
    src=R/'6drsrscap.png';a=np.rot90(alpha(src),2)
    method='MM6 south cap silhouette rotated 180 degrees; no scattered end stones'
  else:
   src=P/'references'/f'{n}.png';rgb=read(src)
   solid=binary_fill_holes((rgb[:,:,0]-rgb[:,:,2])/np.maximum(rgb.mean(2),1)<.32)
   solid=up(solid.astype(float))>.5
   padded=np.pad(solid,64,mode='edge')
   distance=distance_transform_edt(padded)-distance_transform_edt(~padded)
   distance=gaussian_filter(distance,16)[64:-64,64:-64]
   # These four pieces have no MM6 restored counterpart. Preserve their diagonal
   # route, removing source-pixel teeth at the scale of whole stone shoulders.
   a=np.clip(distance/2+.5,0,1);method='MM7-only diagonal, broad native route, MM6 openings'
  targets={side:(np.zeros(512) if k=='000' else profiles['h' if side in 'NS' else 'v']) for side,k in r['topology'].items()}
  a=connect(a,targets)
  components,_=label(a>.5);sizes=np.bincount(components.ravel());sizes[0]=0
  main=components==sizes.argmax()
  a[(components>0)&~main]=0;a[distance_transform_edt(~main)>3]=0
  solid=a>.5;filled=binary_fill_holes(solid);a[filled & ~solid]=1;a[distance_transform_edt(filled)>4]=1
  save(V/'masks'/f'{n}.png',a*255)
  st={side:road_contact(v) for side,v in targets.items()}
  shade=connect(road_contact(a),st)
  (V/'fields').mkdir(exist_ok=True)
  np.savez_compressed(V/'fields'/f'{n}.npz',coverage=a.astype('float32'),shade=shade.astype('float32'))
  base=seams.srgb(seams.linear(read(M/'materials/dirt.png'))*(1-a[:,:,None])+seams.linear(read(M/'materials/roads.png'))*a[:,:,None])*shade[:,:,None]
  save(V/'inputs'/f'{n}.png',base)
  provenance[n]=dict(source=str(src.relative_to(ROOT)),sha256=sha(src),method=method,topology=r['topology'])
 (V/'mask_sources.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print('Prepared',len(records),'road inputs')
if __name__=='__main__':main()
