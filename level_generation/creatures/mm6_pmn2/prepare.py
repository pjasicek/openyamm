"""Inventory pmn2 native mage artwork and prepare unambiguous restoration batches."""
from pathlib import Path
import hashlib,json
import numpy as np
import yaml
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
ASSETS=REPO/'assets_dev'
PALETTES=[801,802,803]
CANVAS=(331,272)

def native(name,palette=802,aligned=True):
    ix=np.array(Image.open(ASSETS/f'engine/sprites/{name}.bmp'))
    rgb=np.frombuffer((ASSETS/f'worlds/mm6/textures/pal{palette:03d}.act').read_bytes()[:768],np.uint8).reshape(256,3)
    im=Image.fromarray(np.dstack([rgb[ix],(ix!=0).astype(np.uint8)*255]))
    if not aligned:return im
    out=Image.new('RGBA',CANVAS);out.paste(im,((CANVAS[0]-im.width)//2,CANVAS[1]-im.height))
    return out

def run():
    for d in ['native','references','prompts','raw','review']:(ROOT/d).mkdir(exist_ok=True)
    # C loader is used only for source data; no external engine implementation is copied.
    table=yaml.load((ASSETS/'engine/rendering/sprite_frame_data_common.yml').read_text(),Loader=yaml.CSafeLoader)
    groups=[g for g in table['sprites'] if g['sprite_name'].lower().startswith(('pmn1','pmn2','pmn3'))]
    files=sorted((ASSETS/'engine/sprites').glob('pmn2*.bmp'));sources={};used=set()
    for g in groups:
        for f in g['frames']:
            name=f['texture_name'].lower()
            used.update([name] if 'Image1' in f['flags'] else [name+str(v) for v in range(5)])
    for p in files:
        im=native(p.stem);im.save(ROOT/f'native/{p.stem}.png');original=native(p.stem,aligned=False)
        sources[p.stem]={'path':str(p.relative_to(REPO)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'size':list(original.size),'visible_bounds':original.getbbox(),'aligned_bounds':im.getbbox(),
            'native_offset':[(331-original.width)//2,272-original.height],'referenced':p.stem in used}
    assert len(files)==59 and len(used)==58 and set(sources)-used=={'pmn2fib0'}
    batches={'standing':{'frames':[f'pmn2sta{v}' for v in range(5)],'view':'front, front-oblique, profile, rear-oblique, back'}}
    for v in range(5):batches[f'walk_{v}']={'frames':[f'pmn2wa{l}{v}' for l in 'abcdef'],'view':['front','front-oblique','profile','rear-oblique','back'][v]}
    for key,code in [('attack','at'),('hit','wi'),('fidget','fi'),('death_corpse','de')]:
        batches[key]={'frames':[f'pmn2{code}{l}0' for l in ('abc' if key=='fidget' else 'abcdef')],'view':'front; final death poses falling/prone' if key=='death_corpse' else 'front'}
    for key,b in batches.items():
        cols=2 if key=='fidget' else 3
        b.update(columns=cols,rows=2,cell_size=704,native_scale=2,native_offset=[21,80],reference=f'references/{key}.png')
        sheet=Image.new('RGB',(cols*704,1408),(255,0,255))
        for i,name in enumerate(b['frames']):
            im=native(name).resize((662,544),Image.Resampling.NEAREST)
            sheet.paste(im,(i%cols*704+21,i//cols*704+80),im)
        sheet.save(ROOT/b['reference'])
        prompt=f'''Use case: style-transfer. Restore a Might and Magic VI male town mage sprite sheet to detailed, believable, high-quality game artwork, faithful to the reference.
Input 1 is the exact pose/layout authority: {cols} columns, 2 rows, {len(b['frames'])} figures ordered left to right then top to bottom. View/action: {key}; {b['view']}. Keep every distinct pose, full figure, staff angle, grip, planted/lifted foot, torso turn and facial direction. Leave unused cells empty. Preserve native-relative position and common anatomical scale, no per-cell zoom. Output a sheet matching the input aspect ratio with generous empty gutters and no labels.
This is the SAME middle-aged adult human mage in all cells: shoulder-length dark brown hair, full dark beard and mustache, stern weathered face, ordinary human proportions. Short muted green cloth shoulder cape/cowl with pointed back, dark brown near-black sleeveless leather belted tunic/skirt, thin ochre rope belt with hanging green pouches, green trousers, dark steel-blue/black tall boots and wrist bracers, bare upper arms and hands. Plain long brown wooden staff with slightly bulbous irregular tip, NO jewel or magical glow. Follow the exact clothing and staff in the native pixels; no hood over head, helmet, armor plates, invented accessories or oversized equipment. In attack and hit poses do not substitute a standing or generic spellcasting pose.
Clarify hair strands, beard, woven cloth folds, worn leather and wood grain with restrained realistic detail. Keep dark original tonal weight, modest contrast, diffuse upper-left baked light, no rim light, no ground shadow. Avoid cartoon/toy proportions, smooth plastic or glossy skin. Green cape, trousers and pouches must remain separate from warm skin, brown staff/leather, gold rope and cool boots for selective palette changes.
Background: perfectly uniform pure magenta RGB(255,0,255), with no gradient, checkerboard, colored bounce, reflection, halo, labels or grid lines. No intended magenta character materials. Keep hair, staff tips and entire body inside their own cells. Aim at about twice native detail per figure; preserve the source silhouette and pose rather than redesigning it.
'''
        if key=='fidget':prompt+='These three front idle poses differ subtly in breathing and expression; keep hands and staff nearly stationary, no invented gesture or large motion.\n'
        if key!='standing':prompt+='Input 2 is the accepted enhanced standing sheet, identity/material reference ONLY. Match its same face, hair, beard, clothes, staff and rendering detail. Input 1 still controls every action pose.\n'
        (ROOT/f'prompts/{key}.txt').write_text(prompt)
    (ROOT/'batches.json').write_text(json.dumps(batches,indent=2)+'\n')
    palette_meta={str(p):{'path':f'assets_dev/worlds/mm6/textures/pal{p}.act','sha256':hashlib.sha256((ASSETS/f'worlds/mm6/textures/pal{p}.act').read_bytes()).hexdigest()} for p in PALETTES}
    (ROOT/'sources.json').write_text(json.dumps({'creature':'mm6:pmn2','monster_ids':[610,611,612],'names':['Apprentice Mage','Journeyman Mage','Mage'],'sources':sources,'groups':groups,'palettes':palette_meta,'base_palette':802,'logical_canvas':CANVAS,'logical_pivot':[165.5,272],'anchor':'bottom-center; no Center flag','scale':0.699997,'unreferenced':['pmn2fib0'],'scope':'59 native images restored; 58 referenced; original fidget a,a,c,d,e,f retained'},indent=2)+'\n')
    print('59 images, 10 batches, 3 palettes; variable native canvases aligned around bottom center')
if __name__=='__main__':run()
