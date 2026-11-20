"""Compose the native/model review at a shared standing-body height and ground line."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
ROOT=Path(__file__).resolve().parent
out=ROOT/'review'
native=ROOT.parent.parent/'source_audit/frames'
# Original standing body is 256 pixels tall. Model rest height is 1.700 units.
# Render camera: square 640 px, ortho width/height 2.65, target height 1.10.
scale=(256*2/1.7)/(640/2.65)
model_size=round(640*scale)
ground=790
model_x=480-model_size//2
model_y=round(ground-model_size*(.5+1.10/2.65))
source_x=480-355
source_y=ground-578
background=(47,50,53,255)
frames=[]
for i in range(18):
 canvas=Image.new('RGBA',(1920,870),background);draw=ImageDraw.Draw(canvas)
 draw.text((35,24),'Original MM6 - six native frames',fill='white')
 draw.text((995,24),'Meshy goblin + authored sword/attack - 24 fps',fill='white')
 ref=Image.open(native/f'gobat{"abcdef"[i//3]}0.png').convert('RGBA').resize((710,578),Image.Resampling.NEAREST)
 canvas.alpha_composite(ref,(source_x,source_y))
 model=Image.open(out/f'pbr_front_{i:02}.png').convert('RGBA').resize((model_size,model_size),Image.Resampling.LANCZOS)
 canvas.alpha_composite(model,(960+model_x,model_y))
 draw.line((15,ground,1905,ground),fill=(90,95,100),width=1)
 frames.append(canvas.convert('RGB'))
# GIF delays total 750 ms (15 x 40 ms + 3 x 50 ms).
frames[0].save(out/'native_vs_model.gif',save_all=True,append_images=frames[1:],duration=[40,40,40,40,40,50]*3,loop=0)
contact=Image.new('RGB',(1920,870*6),background[:3])
for row,index in enumerate([0,3,6,9,12,15]):contact.paste(frames[index],(0,row*870))
contact.resize((960,2610),Image.Resampling.LANCZOS).save(out/'native_vs_model_six_poses.jpg',quality=92)
for view,indices in [('pbr_front',[0,3,6,9,12,15]),('pbr_quarter',list(range(6)))]:
 sheet=Image.new('RGBA',(1920,1280),background)
 for j,index in enumerate(indices):sheet.alpha_composite(Image.open(out/f'{view}_{index:02}.png').convert('RGBA'),(j%3*640,j//3*640))
 sheet.convert('RGB').save(out/f'{view}_sheet.jpg',quality=92)

# Preserve continuous playback in the side/elevated diagnostic views.
for view in ['quarter','overhead']:
 images=[]
 for i in range(18):
  canvas=Image.new('RGBA',(640,640),background)
  canvas.alpha_composite(Image.open(out/f'{view}_{i:02}.png').convert('RGBA'))
  images.append(canvas.convert('RGB'))
 images[0].save(out/f'{view}_motion.gif',save_all=True,append_images=images[1:],duration=[40,40,40,40,40,50]*3,loop=0)
for view in ['front','overhead']:
 sheet=Image.new('RGBA',(1920,1280),background)
 for j,i in enumerate([0,3,6,9,12,15]):sheet.alpha_composite(Image.open(out/f'{view}_{i:02}.png').convert('RGBA'),(j%3*640,j//3*640))
 sheet.convert('RGB').save(out/f'{view}_sheet.jpg',quality=90)
print('Composed comparison and continuous diagnostic playback')
