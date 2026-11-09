"""Package native-key plates, GIFs and a dependency-free local review page."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
study = json.loads((stage.parent/'animation_study/animation_motion_spec.json').read_text())
native = stage.parent.parent/'mm6_dmn/native'
clips = {'Standing': ('standing', 6), 'Walk_Native': ('walk', 54), 'Hit': ('hit', 36),
         'Fidget': ('fidget', 30), 'Death': ('death', 60), 'Ash_Remains': ('corpse', 6)}
notes = {
    'Standing': 'One held ready pose. Both feet stay supported; the curved tail is held without an invented idle cycle.',
    'Walk_Native': 'Native A–F timing, changing finger fan/curl, restrained head yaw and tilt, opposing arm motion, fixed-length legs and rigid feet. The tail follows the native tip path while keeping a hanging curve and slight lag.',
    'Hit': 'Asymmetric recoil: left hand rises, right hand opens, left foot lifts and the curved tail swings up toward the right at D. E/C and F/B repeat the native poses.',
    'Fidget': 'Small body dip, jaw opening and a symmetric hand gesture. The descriptor plays only A–E; its unused stored F/B frame is excluded.',
    'Death': 'Upright disintegration with a native-inspired pink/dark fragment plume. The intact body disappears at D (375 ms); H and I keep their longer 187.5 ms intervals. Hidden anatomy is held rather than reconstructed from flames.',
    'Ash_Remains': 'A separate held charcoal mound using the native 1.75 / 0.699997 scale ratio. The demon body and plume are absent. This state is selected after Death.'}
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
review = {}
overview = Image.new('RGB', (1200, 910), '#202630')
od = ImageDraw.Draw(overview)
for number, (clip, (key, end)) in enumerate(clips.items()):
    c = study['clips'][key]
    anchors = []
    for i, a in enumerate(c['anchors']):
        binding = c['native_binding']['frames'][i]['texture_name']
        anchors.append(dict(sample=a['sample'], binding=binding, phase=a['phase'], letter=chr(65+i)))
    policy = ('Loop closes at '+str(end)+'/48 seconds.' if c['loop'] else
              'Held indefinitely as a separate remains state.' if key == 'corpse' else
              'One shot. Hold the last native pose, then select Ash Remains.' if key == 'death' else
              'One shot. Hold the final B pose, then blend to Standing outside the 750 ms clip.' if key == 'hit' else
              'One shot. Hold the final C pose, then blend to Standing outside the 625 ms clip.')
    review[clip] = dict(label=clip.replace('_', ' '), end=end, anchors=anchors, loop=c['loop'],
                        single=c['single_view'], notes=notes[clip], policy=policy)
    sheet = Image.new('RGB', (len(anchors)*260, 910), '#202630')
    draw = ImageDraw.Draw(sheet)
    for i, a in enumerate(anchors):
        x=i*260
        source = Image.open(native/(a['binding']+('' if c['single_view'] else '0')+'.png')).convert('RGBA')
        source.thumbnail((240, 230), Image.Resampling.NEAREST)
        sheet.paste(source, (x+(260-source.width)//2, 38), source)
        for row, view in enumerate(('front', 'profile', 'oblique')):
            model = Image.open(stage/'preview_frames'/f"{clip}_{view}_{a['sample']:02d}.jpg").convert('RGB')
            model.thumbnail((245, 195))
            sheet.paste(model, (x+(260-model.width)//2, 286+row*205))
        draw.text((x+10, 10), f"{a['letter']} · frame {a['sample']} · {a['sample']/48:.3f}s", font=small, fill='#edc2a6')
    draw.text((10, 883), 'Native front / actual GLB front / profile / oblique', font=small, fill='#ddd7d0')
    sheet.save(stage/(clip+'_anchors.jpg'), quality=92)
    frames = []
    times = [0] if end == 6 else list(range(end))
    for frame in times:
        joined = Image.new('RGB', (684, 360), '#202630')
        for i, view in enumerate(('front', 'profile')):
            picture = Image.open(stage/'preview_frames'/f'{clip}_{view}_{frame:02d}.jpg').convert('RGB')
            picture = picture.resize((342, 360), Image.Resampling.LANCZOS)
            joined.paste(picture, (i*342, 0))
        frames.append(joined)
    # GIF timing resolution is 10 ms. Alternating 20/30 ms holds averages exactly 48 fps.
    durations = [round((i+1)*1000/48/10)*10-round(i*1000/48/10)*10 for i in range(len(frames))]
    if end == 6:
        durations = [1000]
    frames[0].save(stage/(clip+'_preview.gif'), save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=False, disposal=2)
    representative = {'Standing': 0, 'Walk_Native': 15, 'Hit': 18, 'Fidget': 18, 'Death': 24, 'Ash_Remains': 0}[clip]
    image = Image.open(stage/'preview_frames'/f'{clip}_front_{representative:02d}.jpg').convert('RGB')
    image.thumbnail((390, 410))
    x,y=(number%3)*400,(number//3)*455
    overview.paste(image, (x+(400-image.width)//2, y+35))
    od.text((x+14,y+10), clip.replace('_',' '), font=font, fill='#edc2a6')
overview.save(stage/'overview.jpg', quality=93)
(stage/'index.html').write_text((stage/'viewer.html').read_text().replace('__REVIEW_DATA__', json.dumps(review)))
(stage/'review_data.json').write_text(json.dumps(review, indent=2)+'\n')
print('Built six GIFs, six anchor plates, overview and interactive review.')
