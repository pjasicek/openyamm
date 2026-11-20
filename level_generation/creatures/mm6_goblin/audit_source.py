"""Inventory native goblin descriptors, build lossless references and contact/playback sheets."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from PIL import Image, ImageDraw
import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OUT = ROOT / 'source_audit'
GROUPS = {'Standing':'gobsta','Walk':'gobwaa','Attack':'gobata0','Hit':'gobwia0',
          'Death':'gobdya0','Corpse':'gobdyf0','Fidget':'gobfia'}

def run():
    OUT.mkdir(exist_ok=True)
    (OUT/'frames').mkdir(exist_ok=True)
    rows=yaml.safe_load((REPO/'assets_dev/engine/rendering/sprite_frame_data_common.yml').read_text())['sprites']
    native={r['sprite_name']:r for r in rows}
    clips=[]; filenames=set()
    for action,group in GROUPS.items():
        row=native[group]; clip={'name':action,'group':group,'descriptor':row,'frames':[]}
        for frame in row['frames']:
            directions=[0] if 'Image1' in frame['flags'] else list(range(5))
            paths=[frame['texture_name']+(str(d) if 'Image1' not in frame['flags'] else '')+'.bmp' for d in directions]
            clip['frames'].append({'paths':paths,'duration_ms':frame['frame_length_raw']*62.5})
            filenames.update(paths)
        clips.append(clip)
    assert len(filenames)==59
    images={}; records=[]
    for name in sorted(filenames):
        path=REPO/'assets_dev/engine/sprites'/name
        with Image.open(path) as src:
            assert src.mode=='P'
            indices=np.asarray(src); palette=src.getpalette()
            rgba=src.convert('RGBA');rgba.putalpha(Image.fromarray(np.where(indices==0,0,255).astype('uint8')))
            box=rgba.getbbox()
            rgba.save(OUT/'frames'/f'{path.stem}.png');images[name]=rgba
            records.append({'name':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'size':src.size,'mode':src.mode,'transparent_index':0,'palette_zero_rgb':palette[:3],
                'visible_bounds':box,'palette_sha256':hashlib.sha256(bytes(palette)).hexdigest()})
    background=(62,66,68,255)
    def tile(name,size=(355,289)):
        rgba=images[name]
        t=Image.new('RGBA',rgba.size,background);t.alpha_composite(rgba)
        return t.convert('RGB').resize(size)
    for clip in clips:
        cols=len(clip['frames']); dirs=len(clip['frames'][0]['paths'])
        sheet=Image.new('RGB',(cols*355,dirs*315),background[:3]);draw=ImageDraw.Draw(sheet)
        for i,f in enumerate(clip['frames']):
            for d,name in enumerate(f['paths']):
                sheet.paste(tile(name),(i*355,d*315+24));draw.text((i*355+6,d*315+6),name,fill='white')
        sheet.save(OUT/f"{clip['name'].lower()}_native.png")
        movie=[tile(f['paths'][0]) for f in clip['frames']]
        movie[0].save(OUT/f"{clip['name'].lower()}_native.gif",save_all=True,append_images=movie[1:],
            duration=[round(f['duration_ms']/10)*10 for f in clip['frames']],loop=0,disposal=2)
    # Compact overview of every front action, retaining the source canvas and alignment.
    overview=Image.new('RGB',(6*355,7*315),background[:3]);draw=ImageDraw.Draw(overview)
    for row,c in enumerate(clips):
        draw.text((8,row*315+4),c['name'],fill='white')
        for i,f in enumerate(c['frames']):overview.paste(tile(f['paths'][0]),(i*355,row*315+24))
    overview.save(OUT/'actions_front.png')
    # Four native action extremes, explicitly labeled for restoration input.
    picks=['gobwaa0.bmp','gobwac0.bmp','gobatb0.bmp','gobatd0.bmp','gobwib0.bmp','gobdyc0.bmp','gobdyf0.bmp','gobfic0.bmp']
    sheet=Image.new('RGB',(4*355,2*315),background[:3]);draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(picks):
        x=(i%4)*355;y=(i//4)*315
        sheet.paste(tile(name),(x,y+24));draw.text((x+8,y+5),name,fill='white')
    sheet.save(OUT/'restoration_action_inputs.png')
    variants=[r for r in rows if any(re.fullmatch(r'gob(?:st|wa|at|wi|dy|fi)[a-z][0-7]?',
        f['texture_name']) for f in r['frames'])]
    manifest={'source':'MM6 Goblin / merged descriptors 550–552','images':records,'clips':clips,
        'palette_variants':variants,'excluded_glob_matches':['goblet.bmp'],
        'anchor_note':'Native rows omit Center and use bottom anchoring. Canvas and visible bounds are recorded; actor heightScale and frame scale also affect world size. Generated ground pivot and any bottom margin must be documented explicitly.'}
    (ROOT/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Audited',len(images),'native images. Palette keys:',Counter(tuple(r['palette_zero_rgb']) for r in records))

if __name__=='__main__':run()
