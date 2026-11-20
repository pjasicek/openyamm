"""Package rendered masters into native-size RGBA sheets, shared-palette BMPs and explicit timing manifests."""
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'spritesheets'
KEY=(0,252,252)
BG=(43,47,48,255)

def background(image):
    result=Image.new('RGBA',image.size,BG);result.alpha_composite(image);return result.convert('RGB')

def build():
    manifest=json.loads((OUT/'render_manifest.json').read_text());width,height=manifest['frame_size']
    assert (OUT/'status.txt').read_text().startswith(('RENDER COMPLETE','PACKED','COMPLETE'))
    assert hashlib.sha256((ROOT/'mm6_goblin.blend').read_bytes()).hexdigest()==manifest['source_blend_sha256']
    folders={name:OUT/name for name in ['png_355x289','bmp_355x289','sheets_8view','previews']}
    for folder in folders.values():folder.mkdir(exist_ok=True)
    images={};samples=[];bounds=[]
    for clip in manifest['clips']:
        for frame in clip['frames']:
            for direction in range(8):
                name=frame['texture_stem']+str(direction)
                with Image.open(OUT/'masters_710x578'/(name+'.png')) as original:
                    assert original.size==tuple(manifest['master_size']) and original.mode=='RGBA'
                    image=original.convert('RGBa').resize((width,height),Image.Resampling.LANCZOS).convert('RGBA')
                box=image.getchannel('A').getbbox()
                assert box and box[0]>0 and box[1]>0 and box[2]<width and box[3]<height,(name,box)
                image.save(folders['png_355x289']/(name+'.png'));images[name]=image
                pixels=[pixel[:3] for pixel in image.getdata() if pixel[3]>=128]
                samples.extend(pixels[::max(1,len(pixels)//2048)])
                bounds.append({'name':name,'alpha_bounds':box})
    training=Image.new('RGB',(1024,math.ceil(len(samples)/1024)))
    training.putdata(samples+[samples[-1]]*(training.width*training.height-len(samples)))
    quantizer=training.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    opaque=quantizer.getpalette()[:765]
    reference=Image.new('P',(1,1));reference.putpalette(opaque+opaque[:3]);palette=list(KEY)+opaque
    assert len(palette)==768
    for name,image in images.items():
        indices=image.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE).tobytes()
        alpha=image.getchannel('A').tobytes()
        pixels=bytes(1+(index if index<255 else 0) if a>=128 else 0 for index,a in zip(indices,alpha))
        bmp=Image.frombytes('P',(width,height),pixels);bmp.putpalette(palette)
        target=folders['bmp_355x289']/(name+'.bmp');bmp.save(target)
        with Image.open(target) as checked:
            assert checked.mode=='P' and checked.size==(width,height) and checked.getpalette()==palette
            assert all((index==0)==(a<128) for index,a in zip(checked.tobytes(),alpha))
    colors=[palette[i:i+3] for i in range(0,768,3)]
    (OUT/'palette.json').write_text(json.dumps({'transparent_index':0,'colors_rgb':colors},indent=2)+'\n')
    (OUT/'palette.gpl').write_text('GIMP Palette\nName: Restored MM6 Goblin\nColumns: 16\n#\n'+
        ''.join(f'{r:3} {g:3} {b:3}\t{i}\n' for i,(r,g,b) in enumerate(colors)))
    legacy={'schema_version':1,'prefix':manifest['prefix'],'raw_unit_seconds':1/16,
        'directions':8,'mirrors':False,'anchor':'Bottom anchored; no Center flag. Art pivot is recorded separately.',
        'integration':'Staged art only; no live registry IDs allocated. Use all eight genuine views, no Image1 or Mirror flags.',
        'clips':{}}
    for clip in manifest['clips']:
        atlas=Image.new('RGBA',(width*clip['count'],height*8),(0,0,0,0))
        for frame in clip['frames']:
            for direction in range(8):
                atlas.paste(images[frame['texture_stem']+str(direction)],(width*frame['index'],height*direction))
        atlas.save(folders['sheets_8view']/(clip['name'].lower()+'.png'))
        total=round(clip['duration_seconds']*16);count=min(clip['count'],total)
        raw=[round((i+1)*total/count)-round(i*total/count) for i in range(count)]
        assert min(raw)>0 and sum(raw)==total
        frames=[];elapsed=0
        for i,length in enumerate(raw):
            phase=elapsed/(total if clip['loop'] else max(1,total-raw[-1]))
            selected=min(clip['frames'],key=lambda f:abs(f['phase']-phase))
            frames.append({'texture_stem':selected['texture_stem'],'dense_frame_index':selected['index'],
                'frame_length_raw':length,'ideal_phase':phase,'rendered_phase':selected['phase']})
            elapsed+=length
        assert len({f['dense_frame_index'] for f in frames})==len(frames)
        legacy['clips'][clip['name']]={'animation_length_raw':total,'duration_seconds':total/16,'frames':frames}
        # Labeled previews are separate from the usable atlas. GIF centisecond rounding preserves total duration.
        pictures=[];delays=[];total_cs=round(clip['duration_seconds']*100)
        for frame in clip['frames']:
            picture=Image.new('RGB',(8*178,170),BG[:3]);draw=ImageDraw.Draw(picture)
            for direction in range(8):
                tile=background(images[frame['texture_stem']+str(direction)]).resize((178,145),Image.Resampling.LANCZOS)
                picture.paste(tile,(178*direction,25))
                draw.text((178*direction+4,6),f"{clip['name']} / {direction}",fill='white')
            pictures.append(picture);i=frame['index']
            delays.append(10*(round((i+1)*total_cs/clip['count'])-round(i*total_cs/clip['count'])))
        pictures[0].save(folders['previews']/(clip['name'].lower()+'.gif'),save_all=True,
            append_images=pictures[1:],duration=delays,loop=0,disposal=2)
        pictures[0].save(folders['previews']/(clip['name'].lower()+'_directions.png'))
    (OUT/'legacy_manifest.json').write_text(json.dumps(legacy,indent=2)+'\n')
    manifest['outputs']={'masters':len(images),'individual_pngs':len(images),'indexed_bmps':len(images),'eight_view_sheets':7}
    manifest['palette']={'file':'palette.json','transparent_index':0,'transparent_rgb':list(KEY)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report={'frame_count':len(images),'shared_palette':'PASS','transparency':'PASS','nonempty_unclipped':'PASS',
        'source_hash':'PASS','legacy_positive_timings':'PASS','bounds':bounds}
    assert len(images)==552
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'status.txt').write_text('PACKED: technical checks passed; visual palette/sheet review pending')
    print('Packed 552 genuine direction frames; review output before creating the release ZIP')

def archive():
    assert (OUT/'README.md').exists(),'Write actual usage and visual review notes before archiving'
    with ZipFile(OUT/'mm6_goblin_mm_sprites.zip','w',ZIP_DEFLATED,compresslevel=6) as archive:
        for file in sorted(OUT.rglob('*')):
            if file.is_file() and file.suffix!='.zip' and file.name!='status.txt':archive.write(file,file.relative_to(OUT))

if __name__=='__main__':build()
