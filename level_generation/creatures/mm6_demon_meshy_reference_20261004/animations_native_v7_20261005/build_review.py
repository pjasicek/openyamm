"""Package native-key plates, GIFs and a dependency-free local review page."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
study = json.loads((stage.parent/'animation_study/animation_motion_spec.json').read_text())
attack = json.loads((stage.parent/'attack_study/attack_motion_spec.json').read_text())
study['clips']['attack'] = dict(
    anchors=[dict(sample=a['planned_sample'], phase=a['phase']) for a in attack['anchors']],
    native_binding=dict(frames=[dict(texture_name=a['source_frame']) for a in attack['anchors']]),
    loop=False, single_view=True)
native = stage.parent.parent/'mm6_dmn/native'
clips = {'Standing': ('standing', 6), 'Walk_Native': ('walk', 54), 'Hit': ('hit', 36),
         'Fidget': ('fidget', 30), 'Death': ('death', 60), 'Ash_Remains': ('corpse', 6), 'Attack': ('attack', 36)}
notes = {
    'Standing': 'One held ready pose. Both feet stay supported; the curved tail is held without an invented idle cycle.',
    'Walk_Native': 'Native A–F timing, changing finger fan/curl, restrained head yaw and tilt, opposing arm motion, fixed-length legs and rigid feet. The tail hangs closer behind the hips with a tighter return curve and slight lag.',
    'Hit': 'Stronger head-back tilt, higher left-hand reach and straighter fingers at D. The right supporting foot pivots slightly inward; the left foot lifts. E/C and F/B repeat the native poses. Head angles and depth are authored interpretations.',
    'Fidget': 'Small body dip, jaw opening and a symmetric hand gesture, with a slight inward shift/pivot of the right foot and a smaller left-foot adjustment. The descriptor plays only A–E; its unused stored F/B frame is excluded.',
    'Attack': 'Corrected raised right hand: extended finger rays, less camera-facing depth and a modest arm lift, strongest at C. A/F retain the curled recovery shape; opening and sweep transitions remain continuous. The grounded foot pivot, left arm and other body motion are retained.',
    'Death': 'Upright disintegration with a native-inspired pink/dark fragment plume. The intact body disappears at D (375 ms); H and I keep their longer 187.5 ms intervals. Hidden anatomy is held rather than reconstructed from flames.',
    'Ash_Remains': 'A separate held charcoal mound using the native 1.75 / 0.699997 scale ratio. The demon body and plume are absent. This state is selected after Death.'}
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
review = {}
overview = Image.new('RGB', (1200, 1365), '#202630')
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
              'One shot. Native A–F, 750 ms. Right-hand correction; existing foot pivot retained.' if key == 'attack' else
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
    representative = {'Standing': 0, 'Walk_Native': 15, 'Hit': 18, 'Fidget': 18, 'Death': 24, 'Ash_Remains': 0, 'Attack': 24}[clip]
    image = Image.open(stage/'preview_frames'/f'{clip}_front_{representative:02d}.jpg').convert('RGB')
    image.thumbnail((390, 410))
    x,y=(number%3)*400,(number//3)*455
    overview.paste(image, (x+(400-image.width)//2, y+35))
    od.text((x+14,y+10), clip.replace('_',' '), font=font, fill='#edc2a6')
overview.save(stage/'overview.jpg', quality=93)
comparison = Image.new('RGB',(1800,650),'#202630')
draw = ImageDraw.Draw(comparison)
source = Image.open(native/'dmnstda0.png').convert('RGBA').crop((132,85,222,175)).resize((600,600),Image.Resampling.NEAREST)
native_panel = Image.new('RGB',(600,600),'#3e464f')
native_panel.paste(source,(0,0),source)
panels = [native_panel]+[Image.open(stage/'clasp_review_frames'/f'{version}_Standing_chest_front.jpg').resize((600,600),Image.Resampling.LANCZOS)
                         for version in ('before','after')]
for column,(panel,title) in enumerate(zip(panels,['Native chest band and skull','Previous revision 6','Larger skull; ring removed'])):
    comparison.paste(panel,(column*600,50))
    draw.text((column*600+12,15),title,font=small,fill='#edc2a6')
comparison.save(stage/'Clasp_comparison.jpg',quality=94)
closeups = Image.new('RGB',(2000,1590),'#202630')
draw = ImageDraw.Draw(closeups)
for row,view in enumerate(('front','profile','oblique')):
    for column,version in enumerate(('before','after')):
        picture = Image.open(stage/'clasp_review_frames'/f'{version}_Standing_skull_{view}.jpg')
        picture.thumbnail((990,485),Image.Resampling.LANCZOS)
        x,y = column*1000,row*530
        closeups.paste(picture,(x+(1000-picture.width)//2,y+40))
        draw.text((x+12,y+10),f'Skull clasp · {view} · {version}',font=font,fill='#edc2a6')
closeups.save(stage/'Clasp_closeups.jpg',quality=94)
poses = Image.new('RGB',(2000,1680),'#202630')
draw = ImageDraw.Draw(poses)
for row,(clip,frame) in enumerate([('Walk_Native',15),('Attack',12),('Hit',18),('Fidget',18)]):
    for column,(view,version) in enumerate([(v,r) for v in ('front','oblique') for r in ('before','after')]):
        picture = Image.open(stage/'clasp_review_frames'/f'{version}_{clip}_chest_{view}.jpg')
        picture.thumbnail((490,365),Image.Resampling.LANCZOS)
        x,y = column*500,row*420
        poses.paste(picture,(x+(500-picture.width)//2,y+42))
        draw.text((x+12,y+10),f'{clip} {frame} · {view} · {version}',font=small,fill='#edc2a6')
poses.save(stage/'Clasp_animated_poses.jpg',quality=94)
for clip in review:
    if clip!='Ash_Remains':
        review[clip]['notes'] += ' The chest clasp is a larger, shallow skull with no hanging ring; it stays rigidly attached to the chest band.'
(stage/'index.html').write_text((stage/'viewer.html').read_text().replace('__REVIEW_DATA__',json.dumps(review)))
(stage/'review_data.json').write_text(json.dumps(review,indent=2)+'\n')
print('Built seven GIFs, anchor plates, skull clasp comparisons and interactive review.')
