import json,sys,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import binary_dilation,gaussian_filter
P=Path(__file__).resolve().parents[1];R=P/'review/round4'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def composite(path):
 a=Image.open(path).convert('RGBA');bg=Image.new('RGBA',a.size,(64,67,70,255));return Image.alpha_composite(bg,a).convert('RGB')
def panel(canvas,path,xy,label):
 im=composite(path);canvas.paste(im,(xy[0],xy[1]+30));ImageDraw.Draw(canvas).text(xy,label,font=font,fill='white')
canvas=Image.new('RGB',(1660,1490),(64,67,70))
for row,view in enumerate(['front','quarter']):
 for col,key in enumerate(['accepted','reduced']):
  panel(canvas,R/f'{key}_hook_{view}.png',(col*830,row*745),f'{key.title()} hook — {view}')
  panel(canvas,R/f'{key}_grip_{view}.png',(col*830+480,row*745),f'{key.title()} grip')
canvas.save(R/'staff_closeup.png')
canvas=Image.new('RGB',(720,855),(64,67,70))
for i,(view,key)in enumerate((v,k)for v in ['front','quarter']for k in ['accepted','reduced']):panel(canvas,R/f'{key}_ingame_{view}.png',(i*180,0),key.title())
ImageDraw.Draw(canvas).text((12,833),'Staff at 700-pixel actor scale; identical lighting.',font=font,fill='white');canvas.save(R/'staff_ingame.png')
rows=[]
for level,pixels in enumerate([700,550,220,88]):
 views=[];inter=union=0
 for view in range(8):
  paths=[R/f'{k}_lod{level}_view{view}.png'for k in ['accepted','reduced']];a,b=[np.asarray(Image.open(p).convert('RGBA'))for p in paths];ma,mb=a[:,:,3]>127,b[:,:,3]>127;u=ma|mb;n=int((ma&mb).sum());den=int(u.sum());inter+=n;union+=den
  a,b=[np.asarray(composite(p))for p in paths];yy,xx=np.where(u);x0=max(0,xx.min()-5);x1=min(1000,xx.max()+6);y0=max(0,yy.min()-5);y1=min(1000,yy.max()+6)
  x=a.astype(float)/255;y=b.astype(float)/255;mu=gaussian_filter(x,(1.5,1.5,0));nu=gaussian_filter(y,(1.5,1.5,0));vx=gaussian_filter(x*x,(1.5,1.5,0))-mu*mu;vy=gaussian_filter(y*y,(1.5,1.5,0))-nu*nu;cov=gaussian_filter(x*y,(1.5,1.5,0))-mu*nu
  map_=((2*mu*nu+.01**2)*(2*cov+.03**2))/((mu*mu+nu*nu+.01**2)*(vx+vy+.03**2));roi=binary_dilation(u,iterations=5);foreground=float(map_[roi].mean());bbox=float(map_[y0:y1,x0:x1].mean())
  views.append({'view_degrees':view*45,'iou':n/den,'ssim_bbox':bbox,'ssim_foreground':foreground})
 rows.append({'lod':level,'actor_height_px':pixels,'before_triangles':[2018,1108,503,472][level],'after_triangles':[866,472,214,86][level],'pooled_iou':inter/union,'minimum_iou':min(v['iou']for v in views),'minimum_ssim_bbox':min(v['ssim_bbox']for v in views),'views':views})
 # Paired crops preserve the exact on-screen scale, including LOD switch sizes.
 paths=[R/f'{k}_lod{level}_view0.png'for k in ['accepted','reduced']];masks=[np.asarray(Image.open(p))[:,:,3]>0 for p in paths];yy,xx=np.where(masks[0]|masks[1]);box=(max(0,xx.min()-15),max(0,yy.min()-15),min(1000,xx.max()+16),min(1000,yy.max()+16));width=box[2]-box[0];height=box[3]-box[1]
 spacing=max(width,140);c=Image.new('RGB',(max(650,spacing*2),height+65),(64,67,70));dr=ImageDraw.Draw(c);dr.text((10,5),f'LOD{level}: actor {pixels}px, staff {rows[-1]["before_triangles"]} → {rows[-1]["after_triangles"]} triangles',font=font,fill='white')
 for i,path in enumerate(paths):c.paste(composite(path).crop(box),(i*spacing,60));dr.text((i*spacing+10,32),'Accepted'if i==0 else'Reduced',font=font,fill='white')
 c.save(R/f'lod{level}_comparison.png')
report={'method':'Paired full-actor silhouettes at matched accepted LOD, unchanged body, 8 views; alpha>127; SSIM on union bounding box plus 5px. These scores are full-actor metrics, not staff-only metrics. No native game launched.','rows':rows}
# Thin staff alone is reported separately, without hiding it inside the unchanged body silhouette.
staff=[]
for view in ['front','quarter']:
 a,b=[np.asarray(Image.open(R/f'{k}_ingame_{view}.png'))[:,:,3]>127 for k in ['accepted','reduced']];staff.append({'view':view,'iou':float((a&b).sum()/(a|b).sum())})
report['staff_only_700px_scale']=staff
(R/'visual_metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in r.items()if k!='views'}for r in rows],indent=2));print(staff)
