from pathlib import Path
from PIL import Image,ImageDraw
import shutil,json
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');R=O.parent;D=O/'review/fixup_comparisons';D.mkdir(exist_ok=True)
def sheet(name,paths,rects,labels):
 page=Image.new('RGB',(1440,562),(40,40,40));draw=ImageDraw.Draw(page)
 for i,p in enumerate(paths):
  im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(85,85,85,255));bg.alpha_composite(im);im=bg.convert('RGB');scale=min(480/im.width,510/im.height);size=(round(im.width*scale),round(im.height*scale));im=im.resize(size,Image.Resampling.LANCZOS);x=i*480+(480-size[0])//2;y=42+(510-size[1])//2;page.paste(im,(x,y));draw.text((i*480+12,12),labels[i],fill='white')
  if rects[i]:draw.rectangle(tuple(x+v*scale if j%2==0 else y+v*scale for j,v in enumerate(rects[i])),outline=(255,95,60),width=4)
 page.save(D/(name+'.jpg'),quality=95)
# Keep unmarked evidence for exact comparisons.
old=D/'curved_blade_before.png';new=O/'review/final_playback/frames_Attack_front/006.png';shutil.copy2(new,D/'curved_blade_after.png')
sheet('blade_tip_native_before_after',[R/'stage1_20261006/source/frames/gobatb0.png',old,D/'curved_blade_after.png'],[(255,0,325,65),(490,0,670,150),(490,0,670,150)],['Native Attack b: 0.125 s','Before: guessed straight blade axis','After: actual curved-tip basis'])
sheet('head_native_before_after',[R/'stage1_20261006/source/frames/gobsta0.png',O/'review/pilots_v6/head_front.png',O/'review/pilots_v8/head_front.png'],[(160,30,225,93),(80,80,540,590),(80,80,540,590)],['Native face: shape evidence','Before: human brow / chin spur','After: goblin brow, snub nose, clean chin'])
sheet('palette_native_before_after',[Path('/tmp/goblin_palette_native.jpg'),O/'review/final_materials/palette_746.png',O/'review/final_materials_v2/palette_746.png'],[None,(200,180,500,590),(200,180,500,590)],['Native palette 745 / 746 / 747','Before: UV V-mask flip','After: correct glTF image-space mask'])
sheet('death_palm_native_before_after',[R/'stage1_20261006/source/frames/gobdyb0.png',D/'death_blade_plane_before.png',O/'review/final_playback/frames_Death_front/006.png'],[(160,135,325,225),(280,240,670,430),(280,240,670,430)],['Native Death b: broad blade face','Before: guessed downward blade normal','After: wrist roll follows native face'])
(D/'index.json').write_text(json.dumps({'scope':'Diagnostic annotations only; unmarked input views retained in the project','blade_tip':{'clip':'Attack','native_time_seconds':.125,'view':'front','region':'blade tip','before':'Tip projected above native canvas due to curved-tip offset ignored','after':'Actual prop basis fits original 2D tip; bone lengths and native timing preserved'},'head':{'clip':'Standing','time_seconds':0,'view':'front','region':'brow, nose, chin','after':'Local anatomy repairs only'},'palette':{'clip':'Standing','time_seconds':0,'view':'quarter','region':'skin/leather UV charts','after':'Correct image-space V orientation; no new paid texture job'}},indent=2)+'\n')
