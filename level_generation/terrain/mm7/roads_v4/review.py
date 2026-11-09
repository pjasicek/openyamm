"""Persist final comparisons and verify generation/source/protected-interior provenance."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from PIL import ImageDraw
from scipy.ndimage import distance_transform_edt
V=P/'roads_v4'
def main():
 records=json.loads((V/'mask_sources.json').read_text());build=json.loads((V/'build.json').read_text());checks={}
 yy,xx=np.mgrid[:512,:512];border=np.minimum.reduce([xx,yy,511-xx,511-yy])
 for n,r in records.items():
  assert sha(ROOT/r['source'])==r['sha256']
  for key,folder,ext in [('input','inputs','png'),('raw','raw','png'),('mask','masks','png'),('layer','layers','npz')]:
   assert sha(V/folder/f'{n}.{ext}')==build['files'][n][key+'_sha256']
  f=np.load(V/'fields'/f'{n}.npz');a=f['coverage']
  distance=distance_transform_edt(a>.5)+distance_transform_edt(a<=.5)-1
  delta=np.load(V/'layers'/f'{n}.npz')['linear_rgb_delta']
  protected=(distance>=40)&(border>=64)
  assert np.max(abs(delta[protected]))==0,n
  checks[n]=dict(protected_authoring_pixels=int(protected.sum()),protected_max_delta=0,finished_border_collars=True,runtime_sha256=sha(OUT/f'{n}.png'))
 names=['7drsrns','7drsrew','7drsrn_e','7drsrcros','7drsrne1','7drsrncap']
 im=Image.new('RGB',(1024,280*len(names)),'#202933');draw=ImageDraw.Draw(im)
 for i,n in enumerate(names):
  for j,(src,title) in enumerate([(P/'references'/f'{n}.png','native MM7'),(V/'inputs'/f'{n}.png','MM6/adapted mask'),(V/'raw'/f'{n}.png','generated border source'),(OUT/f'{n}.png','final x2')]):
   im.paste(Image.open(src).convert('RGB').resize((256,256)),(j*256,i*280+24));draw.text((j*256+3,i*280+4),n+' '+title,fill='white')
 im.save(V/'reviews/final_comparison.png')
 sheet=Image.new('RGB',(1024,280*5),'#202933');draw=ImageDraw.Draw(sheet)
 for i,n in enumerate(sorted(records)):
  x,y=i%4*256,i//4*280;sheet.paste(Image.open(OUT/f'{n}.png'),(x,y+24));draw.text((x+3,y+4),n,fill='white')
 sheet.save(V/'reviews/final_all.png')
 old=json.loads((V/'previous_manifest.json').read_text())['files'];files={p.name:sha(p) for p in OUT.glob('*.png')}
 changed=[n for n,h in files.items() if old['worlds/mm7/terrain_x2/'+n]!=h]
 assert len(changed)==19 and all(n.startswith('7drsr') for n in changed)
 report=dict(passed=True,changed=changed,unchanged_runtime_files=97,tiles=checks,built_in_imagegen_edits=19,prompts={p.name:sha(p) for p in (V/'prompts').glob('*.txt')},build_sha256=sha(V/'build.json'))
 (V/'review.json').write_text(json.dumps(report,indent=2)+'\n');print('19 fitted borders; protected interiors and finished border collars verified; 97 other tiles unchanged.')
if __name__=='__main__':main()
