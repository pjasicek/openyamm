"""Pack Blender sprite renders into transparent sheets and a shared-palette MM-style BMP family."""
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'spritesheets'
BG=(43,47,48,255)
KEY=(0,252,252)

def on_background(image):
    result=Image.new('RGBA',image.size,BG);result.alpha_composite(image)
    return result.convert('RGB')

def pack():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert (OUT/'status.txt').read_text().startswith('RENDER COMPLETE'), 'Finish the Blender render job first'
    assert hashlib.sha256((ROOT/'brown_ghost.blend').read_bytes()).hexdigest()==manifest['source_blend_sha256']
    paths={name:OUT/name for name in ['png_256','bmp_256','sheets_5view','sheets_8view']}
    for path in paths.values():path.mkdir(exist_ok=True)
    frames={};samples=[];bounds=[]
    for clip in manifest['clips']:
        for entry in clip['frames']:
            stem=entry['texture_stem']
            for direction in range(5):
                name=f'{stem}{direction}'
                with Image.open(OUT/'masters_512'/f'{name}.png') as source:
                    assert source.size==(512,512) and source.mode=='RGBA'
                    image=source.convert('RGBa').resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
                box=image.getchannel('A').getbbox()
                assert box and min(box[:2])>0 and max(box[2:])<256,(name,box)
                image.save(paths['png_256']/f'{name}.png');frames[name]=image
                opaque=[rgb[:3] for rgb in image.getdata() if rgb[3]>=128]
                samples.extend(opaque[::max(1,len(opaque)//2048)])
                bounds.append({'name':name,'alpha_bounds':box})
            for direction in range(5,8):
                name=f'{stem}{direction}';image=ImageOps.mirror(frames[f'{stem}{8-direction}'])
                image.save(paths['png_256']/f'{name}.png');frames[name]=image
    # Train a single 255-color opaque palette; palette index 0 is always the native cyan key.
    width=1024;height=math.ceil(len(samples)/width)
    training=Image.new('RGB',(width,height));training.putdata(samples+[samples[-1]]*(width*height-len(samples)))
    quantizer=training.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    opaque_palette=quantizer.getpalette()[:765]
    reference=Image.new('P',(1,1));reference.putpalette(opaque_palette+opaque_palette[:3])
    native_palette=list(KEY)+opaque_palette
    assert len(native_palette)==768
    for clip in manifest['clips']:
        for entry in clip['frames']:
            for direction in range(5):
                name=f"{entry['texture_stem']}{direction}";image=frames[name]
                indices=image.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE).tobytes()
                alpha=image.getchannel('A').tobytes()
                pixels=bytes((1+(index if index<255 else 0)) if a>=128 else 0 for index,a in zip(indices,alpha))
                bmp=Image.frombytes('P',image.size,pixels);bmp.putpalette(native_palette)
                bmp.save(paths['bmp_256']/f'{name}.bmp')
                with Image.open(paths['bmp_256']/f'{name}.bmp') as check:
                    assert check.mode=='P' and check.size==(256,256)
                    assert check.getpalette()==native_palette and check.getpixel((0,0))==0
                    assert all((index==0)==(a<128) for index,a in zip(check.tobytes(),alpha))
    colors=[native_palette[i:i+3] for i in range(0,768,3)]
    (OUT/'palette.json').write_text(json.dumps({'transparent_index':0,'colors_rgb':colors},indent=2)+'\n')
    (OUT/'palette.gpl').write_text('GIMP Palette\nName: Brown ghost MM sprite family\nColumns: 16\n#\n'+
        ''.join(f'{r:3} {g:3} {b:3}\t{index}\n' for index,(r,g,b) in enumerate(colors)))
    for clip in manifest['clips']:
        clip['sheets']={}
        for count in [5,8]:
            atlas=Image.new('RGBA',(clip['count']*256,count*256),(0,0,0,0))
            for entry in clip['frames']:
                for direction in range(count):
                    atlas.paste(frames[f"{entry['texture_stem']}{direction}"],(entry['index']*256,direction*256))
            path=paths[f'sheets_{count}view']/f"{clip['name'].lower()}.png";atlas.save(path)
            clip['sheets'][str(count)]={'path':str(path.relative_to(OUT)),'size':list(atlas.size)}
    # Compact labeled previews are separate from the transparent, unlabelled usable atlases.
    preview=Image.new('RGB',(16*112,7*140),BG[:3]);draw=ImageDraw.Draw(preview)
    movie=[];movie_directions=[];durations=[];elapsed_ms=0
    for row,clip in enumerate(manifest['clips']):
        draw.text((8,row*140+5),f"{clip['name']}: {clip['count']} frames",fill='white')
        for entry in clip['frames']:
            image=frames[f"{entry['texture_stem']}0"]
            preview.paste(on_background(image).resize((112,112)),(entry['index']*112,row*140+24))
            tile=on_background(image);ImageDraw.Draw(tile).text((8,8),f"{clip['name']} {entry['index']+1}/{clip['count']}",fill='white')
            movie.append(tile)
            strip=Image.new('RGB',(8*128,152),BG[:3]);labels=ImageDraw.Draw(strip)
            for direction in range(8):
                strip.paste(on_background(frames[f"{entry['texture_stem']}{direction}"]).resize((128,128)),(direction*128,24))
                labels.text((direction*128+4,5),f"{clip['name']} / {direction}",fill='white')
            movie_directions.append(strip)
            duration=entry['duration_ms'];durations.append(round((elapsed_ms+duration)/10)*10-round(elapsed_ms/10)*10)
            elapsed_ms+=duration
    preview.save(OUT/'preview_front.png')
    for images,name in [(movie,'animations_front.gif'),(movie_directions,'animations_directions.gif')]:
        images[0].save(OUT/name,save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=2)
    strip=Image.new('RGB',(8*192,220),BG[:3]);draw=ImageDraw.Draw(strip)
    first=manifest['clips'][0]['frames'][0]['texture_stem']
    for direction in range(8):
        strip.paste(on_background(frames[f'{first}{direction}']).resize((192,192)),(direction*192,28))
        draw.text((direction*192+6,8),f"Direction {direction}"+(' (mirrored)' if direction>4 else ''),fill='white')
    strip.save(OUT/'preview_directions.png')
    manifest['palette']={'file':'palette.json','transparent_index':0,'transparent_rgb':list(KEY),'opaque_colors':255}
    manifest['outputs']={'masters_512':345,'png_256':552,'bmp_256':345,'five_view_sheets':7,'eight_view_sheets':7}
    manifest['integration']='Staged art only. Assign registry IDs/palette registration and new frame-table rows before runtime use.'
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    validation={'stored_frames':len(bounds),'png_frames':len(frames),'shared_palette':'PASS',
                'bmp_transparency_mask':'PASS','nonempty_and_unclipped':'PASS','source_blend_hash':'PASS',
                'durations_seconds':{c['name']:sum(f['frame_length_raw'] for f in c['frames'])/16 for c in manifest['clips']},
                'bounds':bounds}
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    assert len(bounds)==345 and len(frames)==552
    (OUT/'status.txt').write_text('PACKED AND VALIDATED')
    with ZipFile(OUT/'brown_ghost_mm_sprites.zip','w',ZIP_DEFLATED,compresslevel=6) as archive:
        for file in sorted(OUT.rglob('*')):
            if file.is_file() and file.suffix!='.zip' and file.name!='status.txt':
                archive.write(file,file.relative_to(OUT))
    print(json.dumps({k:v for k,v in validation.items() if k!='bounds'},indent=2))

if __name__=='__main__':pack()
