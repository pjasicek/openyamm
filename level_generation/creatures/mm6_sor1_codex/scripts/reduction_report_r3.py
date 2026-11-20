from pathlib import Path
import json,ast,numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter
p=Path(__file__).resolve().parents[1];out=p/'review/round3/reduction'
node=next(n for n in ast.parse((p/'scripts/reduction_metrics_r2.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='similarity');exec(compile(ast.Module(body=[node],type_ignores=[]),'reduction_metrics_r2.py','exec'))
report={'comparison':'Unreduced body/staff versus final LOD0, actual three-tier colours and tangent normals, neutral Cycles, body height about 700 px; eight views.','near':{},'lod_switches':{}}
for tier in 'abc':
 rows=[];sheet=Image.new('RGB',(1280,1360),(128,128,128));draw=ImageDraw.Draw(sheet)
 for i in range(8):
  pair=[Image.open(out/f'actor_pbr_{label}0_{tier}_{i}.png').convert('RGBA') for label in ['reference','candidate']];r=similarity(*[np.array(im,dtype=float)/255 for im in pair]);r['view_degrees']=i*45;rows.append(r)
  for j,im in enumerate(pair):
   im.thumbnail((320,320));x=(i%2)*640+j*320;y=(i//2)*340;sheet.paste(im,(x,y+20),im);draw.text((x+5,y+5),f"{i*45} deg {'source' if j==0 else 'rebaked LOD0'}",fill='white')
 sheet.save(out/f'tier_{tier}_comparison.jpg',quality=94)
 report['near'][tier]={'views':rows,'min_iou':min(r['silhouette_iou'] for r in rows),'min_ssim':min(r['textured_ssim'] for r in rows)}
 assert report['near'][tier]['min_iou']>=.99 and report['near'][tier]['min_ssim']>=.95
for n in range(1,4):
 parts={}
 for part in ['Body','Staff','Actor']:
  inter=union=0;rows=[]
  for i in range(8):
   a=np.array(Image.open(out/f'switch{n}_{part}_0_{i}.png'))[:,:,3]>127;b=np.array(Image.open(out/f'switch{n}_{part}_{n}_{i}.png'))[:,:,3]>127;x=int((a&b).sum());y=int((a|b).sum());inter+=x;union+=y;rows.append(x/y)
  parts[part]={'pooled_iou':inter/union,'views':rows}
 report['lod_switches'][str(n)]={'actor_height_px':[0,550,220,88][n],**parts};assert parts['Actor']['pooled_iou']>=.97
report['counts']={str(n):json.loads((out/f'lod{n}_bake.json').read_text())['counts'] for n in range(4)}
for name,caps in [('Body',[11365,11293,11153,11013]),('Staff',[2888,2830,2714,2598])]:
 counts=[report['counts'][str(n)][name]['after'] for n in range(4)];assert all(a>b for a,b in zip(counts,counts[1:])) and all(a<=b for a,b in zip(counts,caps))
report['pass']=True;(out/'metrics.json').write_text(json.dumps(report,indent=2));print('REDUCTION PASS',{k:(v['min_iou'],v['min_ssim']) for k,v in report['near'].items()},{k:v['Actor']['pooled_iou'] for k,v in report['lod_switches'].items()})
