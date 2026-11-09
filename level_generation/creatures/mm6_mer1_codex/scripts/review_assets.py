"""Compose labelled technical review sheets, native skin statistics and reduction evidence."""
import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];O=P/'review';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def tile(path,size):
 im=Image.open(path).convert('RGBA');box=im.getbbox();im=im.crop(box)if box else im;im.thumbnail((size[0]-16,size[1]-16),Image.Resampling.LANCZOS);bg=Image.new('RGBA',size,(58,62,66,255));bg.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2));return bg.convert('RGB')
frames=json.loads((O/'final_frames/frames.json').read_text())
for role,views in frames.items():
 sheet=Image.new('RGB',(6*360,3*510+45),(35,38,41));d=ImageDraw.Draw(sheet);d.text((12,10),'MM6 Merchant — '+role+' — actual exported GLB',font=font,fill='white')
 for row,(view,items)in enumerate(views.items()):
  for col,(path,label)in enumerate(items):
   x,y=col*360,45+row*510;sheet.paste(tile(path,(360,480)),(x,y));d.text((x+8,y+483),view+' / '+label,font=font,fill='white')
 sheet.save(O/f'clip_{role}.jpg',quality=92)
texture=json.loads((O/'texture_report.json').read_text());selection=json.loads((O/'reduction/selection.json').read_text());skin={}
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
for level,info in enumerate(selection['body']):
 for mi,name in [(0,'hands'),(1,'face')]:
  f=P/info['textures'];c=np.asarray(Image.open(f/f'{mi}_material_classes.png').convert('RGB'));mr=np.asarray(Image.open(f/f'{mi}_metal_rough.png').convert('RGB'));mask=(abs(c[:,:,0].astype(float)-1)<.5)&(mr[:,:,0]>65)&(mr[:,:,0]<90)
  rgb=np.asarray(Image.open(f/f'{mi}_basecolor.png').convert('RGB'),float)/255;luma=linear(rgb)[mask]@np.array([.2126,.7152,.0722]);assert len(luma)>100
  stats={'mean':float(luma.mean()),'p90':float(np.percentile(luma,90)),'p95':float(np.percentile(luma,95))}
  native=texture['native_hands_linear_luminance'if name=='hands'else'native_skin_linear_luminance'];skin[f'LOD{level}_{name}']={'pixels':len(luma),'native':native,'baked':stats,'not_darker':all(stats[k]>=native[k]for k in stats)}
(O/'final_skin_luminance.json').write_text(json.dumps(skin,indent=2))
curves={};lines=['# Measured reduction','', 'Reference: unreduced final textured merchant, actual three native tier ramps. LOD0: 700 px, 8 views × 4 body poses × 3 tiers; club 8 views. Distance selection: pooled silhouette IoU >= 0.97 at 550/220/88 px. Probe rows are geometry-only; selected rows have complete fresh UV bakes and actual tier SSIM.','','| Part / LOD | Triangles | IoU (minimum near, pooled far) | SSIM minimum | Gates |','|---|---:|---:|---:|---|']
plot_rows=[]
for kind in ['body','club']:
 for level in range(4):
  d=json.loads((O/f'reduction/{kind}_lod{level}_curve.json').read_text());curves[f'{kind}_LOD{level}']=d
  picked=next(r for r in d['steps']if r['blend']==d['accepted']);v=picked['visual'];lines.append(f"| {kind} / {level} | {picked['triangles']} | {v['min_iou']if level==0 else v['pooled_iou']:.5f} | {v['min_ssim']:.5f} | {picked['gates']['pass']} |")
  plot_rows.append((kind,level,d['steps']))
  folder=P/picked['renders'];ref=O/f'reduction/{kind}_lod{level}/reference_final';sheet=Image.new('RGB',(4*410,2*440+45),(35,38,41));draw=ImageDraw.Draw(sheet);draw.text((12,10),f'{kind} LOD{level} — reference / selected {picked["triangles"]} triangles',font=font,fill='white')
  for col,idx in enumerate([0,1,2,4]):
   name=f'a_Standing_{idx}.png'
   for row,base in enumerate([ref,folder]):
    sheet.paste(tile(base/name,(410,410)),(410*col,45+440*row));draw.text((410*col+8,45+440*row+412),('reference'if row==0 else'selected')+f' / view {idx}',font=font,fill='white')
  sheet.save(O/f'reduction/{kind}_lod{level}_comparison.jpg',quality=94)
chart=Image.new('RGB',(1400,900),'white');draw=ImageDraw.Draw(chart)
colors=['#1b6ca8','#a84326','#528425','#813ab0']
for row,kind in enumerate(['body','club']):
 for col,metric in enumerate(['iou','ssim']):
  x0,y0=col*700+75,row*450+55;w,h=580,320;draw.text((x0,y0-30),kind+' / '+metric,font=font,fill='black');draw.rectangle((x0,y0,x0+w,y0+h),outline='black')
  selected=[(level,steps)for k,level,steps in plot_rows if k==kind];maximum=max(s['triangles']for _,steps in selected for s in steps)
  for level,steps in selected:
   points=[]
   for step in steps:
    vv=step['visual'];value=vv['min_ssim']if metric=='ssim'else vv['min_iou'if level==0 else'pooled_iou']
    if value is None:continue
    points.append((x0+w*step['triangles']/maximum,y0+h*(1-value)/.3))
   if len(points)>1:draw.line(points,fill=colors[level],width=2)
   for x,y in points:draw.ellipse((x-3,y-3,x+3,y+3),fill=colors[level])
   draw.text((x0+level*140,y0+h+12),'LOD'+str(level),font=font,fill=colors[level])
  draw.text((x0+w-100,y0+h+40),str(maximum)+' tris',font=font,fill='black');draw.text((x0-55,y0),'1.00',font=font,fill='black');draw.text((x0-55,y0+h-20),'0.70',font=font,fill='black')
chart.save(O/'reduction/curves.png')
lines+=['','The original inherited-UV trials are retained as *_curve_first_bake.json for geometry provenance; their SSIM values are superseded by the fresh final bakes. Body LOD0 step 5 (8,591 triangles) fails SSIM 0.95; club step 3 (1,068 triangles) fails silhouette 0.99.','']
(O/'reduction/README.md').write_text('\n'.join(lines))
for tier in 'abc':shutil.copyfile(O/f'viewer/mm6_mer1_{tier}.glb',P/f'export/mm6_mer1_portable_{tier}.glb')
print('Sheets, curves, portable tiers and skin report ready')
