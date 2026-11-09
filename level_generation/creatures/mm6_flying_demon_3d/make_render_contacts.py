from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;R=P/'review'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
def fit(path,w,h,crop=None,native=False):
 im=Image.open(path).convert('RGBA')
 if crop:im=im.crop(crop)
 im.thumbnail((w,h),Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS)
 out=Image.new('RGB',(w,h),(42,45,49));out.paste(im,((w-im.width)//2,(h-im.height)//2),im if im.mode=='RGBA' else None);return out
def sheet(items,dest,columns=6,w=192,h=192):
 out=Image.new('RGB',(columns*w,math.ceil(len(items)/columns)*(h+28)),(24,27,31));d=ImageDraw.Draw(out)
 for i,(path,label,crop,native) in enumerate(items):
  x=(i%columns)*w;y=(i//columns)*(h+28);out.paste(fit(path,w,h,crop,native),(x,y+28));d.text((x+5,y+5),label,fill=(240,231,213),font=font)
 out.save(dest,quality=93)
study=json.loads((P/'motion_study.json').read_text());views=['front','diagonal','profile','rear_diagonal','back']
for clip,record in study['clips'].items():
 end=round(record['duration_s']*48);frames=range(end+1) if clip!='Ash_Remains' else [0]
 for view in views:
  items=[(R/'preview_frames'/f'{clip}_{view}_{n:02d}.jpg',f'{clip} {view} f{n}',None,False) for n in frames]
  sheet(items,R/f'{clip}_{view}_dense.jpg')
  if view in ('front','profile','back') and clip!='Ash_Remains':
   sheet([(p,l,(160,80,480,400),False) for p,l,_,_ in items],R/f'{clip}_{view}_upper.jpg',6,256,256)
 items=[]
 anchors=record.get('anchors',[{'frame':0,'source':'m496xa'}]);single=clip in ('Attack','Hit','Death')
 for i,view in enumerate(views):
  for a in anchors:
   source=a['source']+('' if single else str(i))
   items.extend([(P/'source/native'/f'{source}.png',f'Native {"front reused" if single and view!="front" else view} f{a["frame"]}',None,True),(R/'preview_frames'/f'{clip}_{view}_{a["frame"]:02d}.jpg',f'Export {view} f{a["frame"]}',None,False)])
 sheet(items,R/f'{clip}_anchors.jpg',len(anchors)*2,192,192)
sheet([(R/f'{v}_{view}.jpg',f'{v.upper()} {view}',None,False) for v in 'abc' for view in ('front','profile','back','face')],R/'palettes.jpg',4,300,300)
sheet([(p,p.stem.replace('detail_',''),None,False) for p in sorted(R.glob('detail_*.jpg'))],R/'details.jpg',3,400,400)
sheet([(P/'source/native/wdmdthe0.png','Native E / body gone',None,True),(R/'a_death_peak_before.jpg','Previous triangular fragments',None,False),(R/'a_death_peak.jpg','Soft alpha flame ribbons',None,False)],R/'flame_comparison.jpg',3,400,400)
print('Built complete dense and native-anchor contacts from actual exports.')
