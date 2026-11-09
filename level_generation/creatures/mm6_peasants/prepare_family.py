"""Prepare a configured family for this eight-family goal; no AI calls or engine edits."""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]

def load(family, root=None):
    root=Path(root).resolve() if root is not None else HERE.parent/f'mm6_{family}'
    config=json.loads((root/'config.json').read_text())
    inventory_path = root / config['inventory_file'] if 'inventory_file' in config else HERE / 'inventory.json'
    inv=json.loads(inventory_path.read_text())[family]
    return root,config,inv

def native(name,palette,canvas,inventory=None):
    source = inventory['sources'][name] if inventory is not None else {}
    palette = source.get('fixed_palette', palette)
    path = source.get('path', f'assets_dev/engine/sprites/{name}.bmp')
    palette_paths = inventory.get('palette_paths', {}) if inventory is not None else {}
    palette_path = palette_paths.get(str(palette), f'assets_dev/worlds/mm6/textures/pal{palette}.act')
    ix=np.array(Image.open(REPO/path))
    colors=np.frombuffer((REPO/palette_path).read_bytes()[:768],np.uint8).reshape(256,3)
    im=Image.fromarray(np.dstack([colors[ix],(ix!=0).astype(np.uint8)*255]));out=Image.new('RGBA',canvas)
    out.paste(im,((canvas[0]-im.width)//2,canvas[1]-im.height));return out

def run(family):
    root,config,inv=load(family);base=config['base_palette'];canvas=inv['logical_canvas']
    for d in ['native','references','prompts','raw','review']:(root/d).mkdir(exist_ok=True)
    sources={}
    for name,s in inv['sources'].items():
        im=native(name,base,canvas);im.save(root/f'native/{name}.png')
        sources[name]=dict(s,aligned_bounds=im.getbbox(),native_offset=[(canvas[0]-s['size'][0])//2,canvas[1]-s['size'][1]])
    actions=inv['variants'][str(base)]['actions'];aliases=inv['pixel_aliases'];batches={}
    for action in ['standing','walk','attack','hit','fidget','death']:
        group=actions[action];single='Image1' in group['frames'][0]['flags']
        if action=='standing':
            f=group['frames'][0]['texture_name'].lower();names=[f] if single else [f+str(v) for v in range(5)]
            batches[action]={'frames':names,'view':'front, front-oblique, profile, rear-oblique, back' if not single else 'front'}
        elif action=='walk':
            for v in range(1 if single else 5):
                names=[f['texture_name'].lower()+('' if single else str(v)) for f in group['frames']]
                batches[f'walk_{v}']={'frames':list(dict.fromkeys(names)),'view':['front','front-oblique','profile','rear-oblique','back'][v]}
        else:
            names=[f['texture_name'].lower() for f in group['frames']]
            if action=='death':names.extend(f['texture_name'].lower() for f in actions['corpse']['frames'])
            # Preserve unused native artwork in its own action sheet without adding playback entries.
            code=names[0][len(family):len(family)+2]
            names=sorted(set(names)|{n for n in inv['unreferenced'] if n[len(family):len(family)+2]==code})
            batches['death_corpse' if action=='death' else action]={'frames':names,'view':'front'}
    seen=set()
    for key,b in batches.items():
        b['frames']=[n for n in b['frames'] if n not in aliases]
        assert len(b['frames'])<=8 and b['frames'];assert not seen.intersection(b['frames']);seen.update(b['frames'])
        cols=3 if len(b['frames'])>4 else 2;rows=(len(b['frames'])+cols-1)//cols
        cellw=max(canvas[0]*2+64,576);cellh=max(canvas[1]*2+64,576)
        bg=(255,0,255) if config['matte']=='magenta' else (0,255,255)
        sheet=Image.new('RGB',(cols*cellw,rows*cellh),bg)
        for i,name in enumerate(b['frames']):
            im=native(name,base,canvas).resize((canvas[0]*2,canvas[1]*2),Image.Resampling.NEAREST)
            sheet.paste(im,(i%cols*cellw+(cellw-im.width)//2,i//cols*cellh+(cellh-im.height)//2),im)
        sheet.save(root/f'references/{key}.png');b.update(columns=cols,rows=rows,cell_size=[cellw,cellh])
        prompt=f'''Use case: style-transfer. Faithfully restore a low-resolution Might and Magic VI character sprite sheet into detailed, believable high-quality fantasy game artwork.
Input 1 controls exact POSE, VIEW and LAYOUT: {cols} columns by {rows} rows, {len(b['frames'])} occupied cells in row-major order. Action {key}; view {b['view']}. Keep distinct body/limb positions, expressions, planted versus lifted feet, garment motion and full silhouette in EACH cell. Leave unused cells empty. Preserve native camera angle and common anatomical scale, no independent per-cell zoom or recentering.
Identity/materials: {config['description']}
Clarify facial detail, natural hair strands, fabric weave/folds and seams with restrained realistic shading. Maintain the source's muted dark tonal weight and soft upper-left baked illumination. No glossy plastic, cute/toy proportions, exaggerated face, fashion retouching, rim light or ground shadow. Preserve native age, body build, skin tone and character design. No new equipment or objects. Every body, hair strand and accessory wholly inside its own cell with generous empty gutters.
Palette-critical region: {config['regions']}. Keep these materials distinct for deterministic selective recoloring.
Background: perfectly uniform pure {config['matte']} RGB{bg}; no gradients, checkerboard, labels, grid lines, text, watermark, colored bounce, reflections or halos. Do not paint the background color into contour pixels. Aim for a 2048-wide sheet or higher if supported, with useful per-figure detail rather than a tiny contact sheet.
'''
        if key!='standing':prompt+='Input 2 is accepted enhanced standing artwork, IDENTITY AND MATERIAL authority only. Preserve the same face, hair, clothing and proportions; input 1 controls every animation pose.\n'
        if key=='fidget':prompt+='These are subtle native idle/fidget poses. Keep their small expression/posture differences without inventing large gestures.\n'
        if key=='death_corpse':prompt+='Match the native falling and prone body poses and foreshortening exactly; keep a consistent body mass, no enlarging collapsed bodies to fill cells. Depict a non-graphic fall and resting body, no added blood or injury detail.\n'
        if key in config.get('action_notes',{}):prompt+=config['action_notes'][key]+'\n'
        (root/f'prompts/{key}.txt').write_text(prompt)
    assert seen|set(aliases)==set(sources),(family,set(sources)-seen-set(aliases))
    palmeta={p:{'path':f'assets_dev/worlds/mm6/textures/pal{p}.act','sha256':hashlib.sha256((REPO/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()).hexdigest()} for p in inv['variants']}
    (root/'sources.json').write_text(json.dumps(dict(inv,sources=sources,base_palette=base,palette_sources=palmeta,
        logical_pivot=[canvas[0]/2,canvas[1]],anchor='bottom-center; native offsets recorded'),indent=2)+'\n')
    (root/'batches.json').write_text(json.dumps(batches,indent=2)+'\n')
    contact=Image.new('RGB',(5*(canvas[0]+12),3*(canvas[1]+28)),(43,45,43));d=ImageDraw.Draw(contact)
    names=batches['standing']['frames']
    for row,pal in enumerate(inv['variants']):
        for col,name in enumerate(names):
            im=native(name,int(pal),canvas);x=col*(canvas[0]+12);y=row*(canvas[1]+28)
            contact.paste(im,(x+6,y+24),im);d.text((x+4,y+4),f'{pal}: {name}',fill='white')
    contact.save(root/'references/native_variants.png')
    print(f'{family}: {len(sources)} files, {len(seen)} unique images, {len(batches)} batches')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('family');run(parser.parse_args().family)
