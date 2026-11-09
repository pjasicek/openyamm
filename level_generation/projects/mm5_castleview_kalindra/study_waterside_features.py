"""Review bounded shore fits for original bottles and wreck without changing the active map."""
import csv
import hashlib
import json
import math
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from author_props import ground_at
from prepare_message_bottles import FITS as BOTTLE_FITS

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT/'review/waterside_placements_v1'
# Bottle contacts drift to the same local bank; the wreck's stern reaches the southern shore.
# These are deliberate local fits, not a search that can move a source feature across the region.
FITS = {**BOTTLE_FITS,
    'source_4_2_7': {'point':[-20736,-13696], 'standing':[-20736,-14656],
                     'hullBounds':[-224,-640,224,640], 'contact':[-20736,-14336]},
}


def main():
    OUTPUT.mkdir(exist_ok=True)
    terrain_path = PROJECT/'implementation/source/mm5_sw.terrain.yml'
    terrain = yaml.safe_load(terrain_path.read_text())
    tiles = bytes.fromhex(terrain['tile_map_hex'])
    height = bytes.fromhex(terrain['height_map_hex'])
    rows = list(csv.DictReader((PROJECT/'implementation/terrain_rows.tsv').open(), delimiter='\t'))
    names = {90+i:r['texture_name'] for i,r in enumerate(rows)}
    paths = {p.stem.lower():p for w in ['mm7','mm8']
             for p in (ROOT/'assets_dev/worlds'/w/'textures').iterdir() if p.is_file()}
    paths['mm5void'] = PROJECT/'implementation/runtime/worlds/mm5/textures/mm5void.png'
    images = {n:Image.open(paths[n]).convert('RGB') for n in {names[t] for t in tiles}}

    def sample(point):
        c,r = (point[0]+32768)/512,(32768-point[1])/512
        name = names[tiles[math.floor(r)*128+math.floor(c)]]
        im = images[name]
        x,y = int((c%1)*im.width),int((r%1)*im.height)
        red,green,blue = im.getpixel((x,y))
        wet = name=='wtrtyl' or (name.startswith('wtrdr') and red>200 and green<80 and blue>200)
        return {'texture':name,'pixel':[x,y],'paintedWater':wet,'void':name=='mm5void',
                'nativeGroundZ':ground_at(height,point)}

    rendered = {}
    for name,im in images.items():
        im = im.copy()
        if name.startswith('wtrdr'):
            water = images['wtrtyl'].resize(im.size)
            for y in range(im.height):
                for x in range(im.width):
                    r,g,b = im.getpixel((x,y))
                    if r>200 and g<80 and b>200: im.putpixel((x,y),water.getpixel((x,y)))
        rendered[name] = im.resize((128,128),Image.Resampling.NEAREST)
    features = {f['id']:f for f in json.loads((PROJECT/'layout.json').read_text())['features']}
    records = []
    for identity,fit in FITS.items():
        source = features[identity]
        standing = [sample([fit['standing'][0]+96*math.cos(i*math.tau/16),
                            fit['standing'][1]+96*math.sin(i*math.tau/16)]) for i in range(16)]
        assert all(not p['paintedWater'] and not p['void'] for p in standing),(identity,standing)
        assert math.dist(source['point'],fit['point'])<=768,identity
        contact = fit.get('contact',fit['point'])
        assert math.dist(contact,fit['standing'])<=384,identity
        record = {'id':identity,'sourceFeature':source,**fit,
                  'placementChange':math.dist(source['point'],fit['point']),
                  'contactSample':sample(contact),'standingSample':sample(fit['standing']),
                  'standingRadius':96,'standingRingSamples':standing}
        records.append(record)
        c,r = math.floor(source['point'][0]/512+64),math.floor(64-source['point'][1]/512)
        c0,r0 = c-3,r-3
        canvas = Image.new('RGB',(896,950),'#202428')
        for rr in range(7):
            for cc in range(7):canvas.paste(rendered[names[tiles[(r0+rr)*128+c0+cc]]],(cc*128,rr*128))
        draw = ImageDraw.Draw(canvas)
        screen = lambda p: ((p[0]/512+64-c0)*128,(64-p[1]/512-r0)*128)
        a,b = screen(source['point']),screen(fit['point'])
        draw.line([a,b],fill='#fff060',width=3)
        for name,point,color in [('source',source['point'],'#fff060'),('geometry',fit['point'],'#ff90ff'),
                                  ('stand',fit['standing'],'#60ffff')]:
            x,y = screen(point)
            draw.ellipse((x-5,y-5,x+5,y+5),outline=color,width=3)
            draw.text((x+8,y+5),name,fill=color,stroke_width=1,stroke_fill='black')
        x,y = screen(fit['standing'])
        draw.ellipse((x-24,y-24,x+24,y+24),outline='#60ffff',width=2)
        if 'hullBounds' in fit:
            x,y = fit['point']; x0,y0,x1,y1 = fit['hullBounds']
            draw.rectangle([screen([x+x0,y+y1]),screen([x+x1,y+y0])],outline='#ff90ff',width=3)
        draw.text((12,904),identity+'  |  original → local shore fit; cyan: dry standing ring',fill='white')
        draw.text((12,924),'512 units per tile. Proposal only: geometry, native click and water context still require review.',fill='white')
        canvas.save(OUTPUT/(identity+'.png'))
    (OUTPUT/'placements.json').write_text(json.dumps({
        'status':'Proposed shore fits; active geometry/scenery unchanged',
        'terrainSourceSha256':hashlib.sha256(terrain_path.read_bytes()).hexdigest(),'features':records,
        'limits':'Painted shore and standing ring checks only; actual model, clearance, ground access and clicks remain.'
    },indent=2)+'\n')
    print([{'id':r['id'],'shift':r['placementChange'],'contact':r['contactSample'],
            'standing':r['standingSample']} for r in records])


if __name__=='__main__':
    main()
