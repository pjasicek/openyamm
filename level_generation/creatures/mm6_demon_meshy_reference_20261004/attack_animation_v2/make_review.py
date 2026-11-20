"""Compose diagnostic render sheets and a playback preview; never edit model/source art."""
import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
frames = stage / 'review_frames'
plates = stage / 'review_plates'
plates.mkdir(exist_ok=True)
source = np.load(stage / 'source_geometry.npz')
poses = np.load(stage / 'attack_pose_arrays.npz')['vertices']
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
names = list(source['group_names'])
selectors = {}
for side in ('Right', 'Left'):
    columns = [j for j, name in enumerate(names) if name.startswith('mixamorig:' + side + 'Hand')]
    selectors[side] = source['weights'][:, columns].sum(1) > .75
selectors['Head'] = (source['weights'][:, [names.index(n) for n in ('mixamorig:Head','Bone_025')]].sum(1) > .5) & (source['vertices'][:,2]>1.45)

def crop_bounds(v, mask):
    points = v[mask]
    # AUTO sensor fit is horizontal for these landscape renders: ortho_scale spans image width.
    xy = np.stack([650 + points[:,0]*1300/2.35, 550 + (.86-points[:,2])*1300/2.35],axis=1)
    lo = np.floor(xy.min(0)-16).astype(int)
    hi = np.ceil(xy.max(0)+16).astype(int)
    return [max(0,int(lo[0])),max(0,int(lo[1])),min(1300,int(hi[0])),min(1100,int(hi[1]))]

for start in range(0,37,6):
    indices = list(range(start,min(start+6,37)))
    full = Image.new('RGB',(1950,1160),(24,30,36))
    hands = Image.new('RGB',(1950,780),(24,30,36))
    heads = Image.new('RGB',(1800,720),(24,30,36))
    for offset,frame in enumerate(indices):
        front=Image.open(frames/f'front_{frame:02d}.png').convert('RGB')
        side=Image.open(frames/f'side_{frame:02d}.png').convert('RGB')
        x,y=offset%3*650,offset//3*580
        full.paste(front.resize((650,550),Image.Resampling.LANCZOS),(x,y+30))
        ImageDraw.Draw(full).text((x+8,y+5),f'#{frame:02d}  {frame/48*1000:.1f} ms',font=font,fill='white')
        x,y=offset%3*650,offset//3*390
        for side_name,left in [('Right',0),('Left',325)]:
            crop=front.crop(crop_bounds(poses[frame],selectors[side_name]))
            assert crop.width<=325 and crop.height<=355,(frame,side_name,crop.size)
            hands.paste(crop,(x+left+(325-crop.width)//2,y+30))
        ImageDraw.Draw(hands).text((x+8,y+5),f'#{frame:02d}  R / L hand — original render pixels',font=small,fill='white')
        x,y=offset%3*600,offset//3*360
        crop=front.crop(crop_bounds(poses[frame],selectors['Head']))
        assert crop.width<=600 and crop.height<=320
        heads.paste(crop,(x+(600-crop.width)//2,y+30))
        ImageDraw.Draw(heads).text((x+8,y+5),f'#{frame:02d}  head/jaw — original render pixels',font=small,fill='white')
    full.save(plates/f'front_{start:02d}.jpg',quality=95)
    hands.save(plates/f'hands_{start:02d}.png')
    heads.save(plates/f'heads_{start:02d}.png')
    profile=Image.new('RGB',(1950,1160),(24,30,36))
    for offset,frame in enumerate(indices):
        x,y=offset%3*650,offset//3*580
        profile.paste(Image.open(frames/f'side_{frame:02d}.png').convert('RGB').resize((650,550),Image.Resampling.LANCZOS),(x,y+30))
        ImageDraw.Draw(profile).text((x+8,y+5),f'#{frame:02d}  {frame/48*1000:.1f} ms',font=font,fill='white')
    profile.save(plates/f'side_{start:02d}.jpg',quality=95)

animation=[]
for frame in range(37):
    image=Image.new('RGB',(1300,585),(24,30,36))
    image.paste(Image.open(frames/f'front_{frame:02d}.png').convert('RGB').resize((650,550),Image.Resampling.LANCZOS),(0,35))
    image.paste(Image.open(frames/f'side_{frame:02d}.png').convert('RGB').resize((650,550),Image.Resampling.LANCZOS),(650,35))
    ImageDraw.Draw(image).text((12,8),'MM6 demon — 750 ms attack | front / profile | endpoint held for preview',font=font,fill='white')
    animation.append(image)
durations=[max(10,(round((i+1)/48*100)-round(i/48*100))*10) for i in range(36)]+[350]
assert sum(durations[:-1])==750
animation[0].save(stage/'attack_preview.gif',save_all=True,append_images=animation[1:],duration=durations,loop=0,disposal=2)
# A six-anchor source comparison keeps one common ground/figure scale within each representation.
comparison=Image.new('RGB',(3420,1320),(24,30,36))
for i,letter in enumerate('abcdef'):
    x,y=i%3*1140,i//3*660
    native=Image.open(stage.parent.parent/'mm6_dmn/native'/f'dmnatk{letter}0.png').convert('RGBA')
    native=native.resize((531,495),Image.Resampling.NEAREST)
    # Native and model figure heights are both ~386px; neither pose is independently fitted.
    model=Image.open(frames/f'front_{i*6:02d}.png').convert('RGB').resize((534,452),Image.Resampling.LANCZOS)
    native_ground=329*1.5
    model_ground=(550+.858*1300/2.35)*(452/1100)
    comparison.paste(native,(x+10,y+80),native)
    comparison.paste(model,(x+565,y+round(80+native_ground-model_ground)))
    ImageDraw.Draw(comparison).text((x+8,y+8),f'{letter.upper()} / {i*125} ms — native | supplied model',font=font,fill='white')
comparison.save(stage/'native_comparison.jpg',quality=95)
print('Saved all-pose review sheets, 100% hand/head crops and front/profile playback preview.')
