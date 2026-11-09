"""Read-only native inventory and palette contact for the eight-family restoration goal."""
from pathlib import Path
import json, hashlib
from collections import defaultdict
import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
FAMILIES={'pfem':595,'fmp':598,'mfp':601,'natf':604,'pman':607,'pmn2':610,'mep':613,'natm':616}
ACTIONS=['standing','walk','attack','attack2','hit','death','corpse','fidget']

def native(name,palette):
    ix=np.array(Image.open(REPO/f'assets_dev/engine/sprites/{name}.bmp'))
    colors=np.frombuffer((REPO/f'assets_dev/worlds/mm6/textures/pal{palette}.act').read_bytes()[:768],np.uint8).reshape(256,3)
    return Image.fromarray(np.dstack([colors[ix],(ix!=0).astype(np.uint8)*255]))

def run():
    table=REPO/'assets_dev/engine/rendering/sprite_frame_data_common.yml'
    groups={g['sprite_name'].lower():g for g in yaml.load(table.read_text(),Loader=yaml.CSafeLoader)['sprites']}
    descriptors={int(c[0]):c for line in (REPO/'assets_dev/engine/data_tables/monster_descriptors.txt').read_text().splitlines()
                 for c in [line.split('\t')] if c[0].isdigit()}
    result={};contact=Image.new('RGB',(1200,8*330),(43,45,43));draw=ImageDraw.Draw(contact)
    for row,(prefix,first_id) in enumerate(FAMILIES.items()):
        variants={};used=set()
        for col,mid in enumerate(range(first_id,first_id+3)):
            d=descriptors[mid];actions={a:groups[key.lower()] for a,key in zip(ACTIONS,d[11:19])}
            pal=actions['standing']['frames'][0]['palette_id']
            variants[str(pal)]={'descriptor_id':mid,'descriptor_label':d[1],'actions':actions}
            for g in actions.values():
                for f in g['frames']:
                    name=f['texture_name'].lower();used.update([name] if 'Image1' in f['flags'] else [name+str(v) for v in range(5)])
            f=actions['standing']['frames'][0];name=f['texture_name'].lower()+('' if 'Image1' in f['flags'] else '0')
            im=native(name,pal);scale=min(1,380/im.width,290/im.height)
            im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
            x=col*400+(400-im.width)//2;y=row*330+325-im.height
            contact.paste(im,(x,y),im);draw.text((col*400+8,row*330+6),f'{prefix}: {d[1]}, palette {pal}',fill='white')
        files=sorted((REPO/'assets_dev/engine/sprites').glob(prefix+'*.bmp'));sources={};duplicates=defaultdict(list)
        for path in files:
            im=Image.open(path);pixhash=hashlib.sha256(bytes(str(im.size),'ascii')+im.tobytes()).hexdigest()
            duplicates[pixhash].append(path.stem)
            sources[path.stem]={'path':str(path.relative_to(REPO)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'size':im.size,'pixel_hash':pixhash,'referenced':path.stem in used}
        assert used<=set(sources),(prefix,used-set(sources))
        aliases={name:names[0] for names in duplicates.values() for name in names[1:]}
        result[prefix]={'variants':variants,'sources':sources,'pixel_aliases':aliases,'unreferenced':sorted(set(sources)-used),
            'logical_canvas':[max(s['size'][0] for s in sources.values()),max(s['size'][1] for s in sources.values())]}
        print(prefix,len(sources),'files',len(duplicates),'unique',list(variants),'canvas',result[prefix]['logical_canvas'])
    (ROOT/'inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    contact.save(ROOT/'native_families.png')

if __name__=='__main__':run()
