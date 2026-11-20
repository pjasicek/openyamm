"""Compose the native/model review at a shared standing-body height and ground line."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
ROOT=Path(__file__).resolve().parent
out=ROOT/'review'
native=ROOT.parent/'source_audit/frames'
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
# GIF's 10 ms time units sum to exactly 750 ms: 40,40,50 repeated six times.
frames[0].save(out/'native_vs_model.gif',save_all=True,append_images=frames[1:],duration=[40,40,50]*6,loop=0)
contact=Image.new('RGB',(1920,870*6),background[:3])
for row,index in enumerate([0,3,6,9,12,15]):contact.paste(frames[index],(0,row*870))
contact.resize((960,2610),Image.Resampling.LANCZOS).save(out/'native_vs_model_six_poses.jpg',quality=92)
for view,indices in [('pbr_front',[0,3,6,9,12,15]),('pbr_quarter',list(range(6)))]:
 sheet=Image.new('RGBA',(1920,1280),background)
 for j,index in enumerate(indices):sheet.alpha_composite(Image.open(out/f'{view}_{index:02}.png').convert('RGBA'),(j%3*640,j//3*640))
 sheet.convert('RGB').save(out/f'{view}_sheet.jpg',quality=92)
body='''<!doctype html><meta charset="utf-8"><title>MM6 goblin sword and native attack</title><style>body{font:17px system-ui;background:#202124;color:#eee;max-width:1300px;margin:32px auto;padding:0 16px}img{max-width:100%;background:#303235}a{color:#a9d4ff}p{line-height:1.5}</style><h1>Goblin sword and original-style slash</h1><p>Original sprites guide the blade silhouette and six attack phases. The authored attack lasts 0.75 seconds. Both figures use one fixed scale based on standing body height and share a ground line.</p><h2>Motion comparison</h2><img src="review/native_vs_model.gif"><p><a href="review/native_vs_model_six_poses.jpg">Six paired poses</a> · <a href="review/pbr_quarter_sheet.jpg">Three-quarter poses</a></p><h2>Sword</h2><img src="review/sword.png"><p><a href="mm6_goblin_sword.glb">Standalone sword GLB</a> · <a href="goblin_sword_attack.glb">Animated goblin GLB</a> · <a href="goblin_sword.blend">Editable Blender project</a></p><p>In the model viewer choose <b>MM6_Attack_Native</b> or <b>MM6_Standing_Sword</b>. Meshy-prefixed clips are retained references and are not the new native-style attack. The sword and grip are present throughout; other imported actions still need weapon/contact review.</p><p>This is a reconstruction from the supplied sprites. Meshy body proportions and costume differ from the original, and only the original frontal attack is available to constrain depth. The other views are consistent 3D interpretations.</p>'''
(ROOT/'review.html').write_text(body)
print(json.dumps({'comparison':str(out/'native_vs_model.gif'),'model_scale':scale,'ground_y':ground}))
