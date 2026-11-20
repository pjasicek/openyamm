"""Assemble reference/model review sheets and inspect the portable asset's structure."""
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
BG=(43,47,48,255)
def displayed(path,size):
    im=Image.open(path).convert('RGBA')
    if path.suffix.lower()=='.bmp':
        pixels=im.load();transparent=im.getpixel((0,0))[:3]
        for y in range(im.height):
            for x in range(im.width):
                if pixels[x,y][:3]==transparent:pixels[x,y]=(0,0,0,0)
    im=im.resize(size,Image.Resampling.LANCZOS)
    bg=Image.new('RGBA',size,BG);bg.alpha_composite(im)
    return bg.convert('RGB')
sheet=Image.new('RGB',(1280,570),BG[:3]);draw=ImageDraw.Draw(sheet)
for i,label in enumerate(['front','three_quarter','side','rear_three_quarter','back']):
    for row,path in enumerate([REPO/'assets_dev/engine/sprites'/f'm242sa{i}.bmp',ROOT/'review'/f'{label}.png']):
        sheet.paste(displayed(path,(256,256)),(i*256,row*285+25))
        draw.text((i*256+8,row*285+7),('Reference ' if row==0 else 'Brown model ')+label,fill='white')
sheet.save(ROOT/'review/comparison.png')
# Equal-height silhouette comparison, preserving each model's width proportions.
comparison=Image.new('RGB',(1080,540),BG[:3]);labels=ImageDraw.Draw(comparison)
for column,(label,path) in enumerate([
    ('Native reference',REPO/'assets_dev/engine/sprites/m242sa1.bmp'),
    ('Previous 3D model',ROOT/'revisions/v1/three_quarter.png'),
    ('Revised 3D model',ROOT/'review/three_quarter.png')]):
    im=Image.open(path).convert('RGBA')
    if path.suffix=='.bmp':
        pixels=im.load();key=im.getpixel((0,0))[:3]
        for y in range(im.height):
            for x in range(im.width):
                if pixels[x,y][:3]==key:pixels[x,y]=(0,0,0,0)
    box=im.getchannel('A').getbbox();im=im.crop(box)
    im=im.resize((round(im.width*460/im.height),460),
                 Image.Resampling.NEAREST if path.suffix=='.bmp' else Image.Resampling.LANCZOS)
    tile=Image.new('RGBA',(360,500),BG);tile.alpha_composite(im,((360-im.width)//2,20))
    comparison.paste(tile.convert('RGB'),(column*360,35))
    labels.text((column*360+40,15),label,fill='white')
comparison.save(ROOT/'review/revision_comparison.png')

poses=['front','attack','float_low','float_high','hit','corpse']
sheet=Image.new('RGB',(960,700),BG[:3]);draw=ImageDraw.Draw(sheet)
for i,name in enumerate(poses):
    x=i%3*320;y=i//3*350
    sheet.paste(displayed(ROOT/'review'/f'{name}.png',(320,320)),(x,y+26))
    draw.text((x+10,y+8),name.replace('_',' '),fill='white')
sheet.save(ROOT/'review/poses.png')
animation_data=json.loads((ROOT/'animations.json').read_text())
clips=animation_data['clips']
expected_count=clips[-1]['timeline_end']
assert len(list((ROOT/'review/frames').glob('*.png')))==expected_count
frames=[]
frame_report=[]
for file in sorted((ROOT/'review/frames').glob('*.png')):
    frame=int(file.stem)
    rgba=Image.open(file).convert('RGBA');bounds=rgba.getchannel('A').getbbox()
    assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<rgba.width and bounds[3]<rgba.height,(file,bounds)
    frame_report.append({'frame':frame,'bounds':bounds})
    label=next(c['name'] for c in clips if c['timeline_start']<=frame<=c['timeline_end'])
    image=displayed(file,(320,320));ImageDraw.Draw(image).text((10,8),f'Brown ghost | {label}',fill='white')
    frames.append(image)
frames[0].save(ROOT/'review/animations.gif',save_all=True,append_images=frames[1:],duration=[(round((i+1)*100/animation_data['fps'])-round(i*100/animation_data['fps']))*10 for i in range(len(frames))],loop=0,disposal=2)
(ROOT/'review/frame_validation.json').write_text(json.dumps({'fps':animation_data['fps'],'rendered_frames':len(frames),'nonempty_and_unclipped':'PASS'},indent=2)+'\n')
file=ROOT/'brown_ghost.glb'
if file.exists():
    data=file.read_bytes();magic,version,length=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and length==len(data)
    chunk_size,chunk_type=struct.unpack_from('<II',data,12)
    assert chunk_type==0x4e4f534a
    doc=json.loads(data[20:20+chunk_size])
    assert len(doc.get('meshes',[]))==1,'The export must contain only the combined character mesh'
    report={'file_bytes':len(data),'skins':[len(s['joints']) for s in doc.get('skins',[])],
            'animations':[{ 'name':a['name'],'duration':max(doc['accessors'][s['input']]['max'][0] for s in a['samplers'])-min(doc['accessors'][s['input']]['min'][0] for s in a['samplers']),'paths':sorted({c['target']['path'] for c in a['channels']})} for a in doc.get('animations',[])],
            'embedded_images':len([i for i in doc.get('images',[]) if 'bufferView' in i]),
            'morph_target_counts':sorted({len(p.get('targets',[])) for m in doc.get('meshes',[]) for p in m['primitives']})}
    (ROOT/'review/glb_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['skins']==[32],report
    assert {a['name'] for a in report['animations']}=={c['name'] for c in clips},report
    assert all('weights' in a['paths'] and 'rotation' in a['paths'] for a in report['animations']),report
    for animation in report['animations']:
        clip=next(c for c in clips if c['name']==animation['name'])
        assert abs(animation['duration']-(clip['timeline_end']-clip['timeline_start'])/animation_data['fps'])<.001,animation
    assert report['embedded_images']>=1 and report['morph_target_counts']==[len(json.loads((ROOT/'poses.json').read_text()))],report
    print(json.dumps(report,indent=2))
