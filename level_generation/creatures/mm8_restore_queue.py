"""Resumable MM8 native source audit and built-in imagegen preparation.

Run from the repository as python3 level_generation/creatures/mm8_restore_queue.py prepare.
Preparation never marks artwork validated. Native files and gameplay remain read-only.
"""
from pathlib import Path
from collections import defaultdict, Counter
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
import numpy as np
import yaml
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
A = REPO / 'assets_dev'
ACTIONS = ['standing', 'walk', 'attack', 'attack2', 'hit', 'death', 'corpse', 'fidget']
QUEUE = HERE / 'mm8_remaining'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

def resolve(frame, view):
    name = frame['texture_name'].lower()
    flags = frame.get('flags', [])
    mirrored = f'Mirror{view}' in flags
    if 'Image1' in flags:
        return name, mirrored
    if 'Images3' in flags:
        stored = 4 if view in (3, 4, 5) else 2 if view in (2, 6) else 0
    elif 'Fidget' in flags:
        if view in (3, 4, 5):
            return name[:-3] + ('sta4' if view == 4 else 'sta3'), mirrored
        stored = 0 if view == 0 else 2 if view in (2, 6) else 1
    else:
        stored = 8 - view if mirrored else view
    return (name if name.endswith(str(stored)) else name + str(stored)), mirrored

def native(root, name, palette=None):
    inv = json.loads((root / 'sources.json').read_text())
    s = inv['sources'][name]
    im = Image.open(REPO / s['path'])
    ix = np.asarray(im)
    pal = str(s['base_palette'] if palette is None else palette)
    if pal == '0':
        colors = np.asarray(im.convert('RGB'))
    else:
        lut = np.frombuffer((REPO / inv['palette_sources'][pal]['path']).read_bytes()[:768], np.uint8).reshape(256, 3)
        colors = lut[ix]
    return Image.fromarray(np.dstack((colors, (ix != 0).astype(np.uint8) * 255)))

def prepare():
    inventory = json.loads((HERE / 'remaining_inventory.json').read_text())
    tables = [A/'engine/rendering/sprite_frame_data_common.yml', *sorted((A/'engine/rendering/sprite_frames/monsters').glob('*.yml'))]
    groups = {g['sprite_name'].lower():g for p in tables for g in yaml.load(p.read_text(), Loader=yaml.CSafeLoader)['sprites']}
    descriptors = {int(c[0]):c for line in (A/'engine/data_tables/monster_descriptors.txt').read_text().splitlines() if (c:=line.split('\t'))[0].isdigit()}
    sprites = {}
    palettes = {}
    for folder in [A/'engine/sprites', A/'worlds/mm8/sprites']:
        sprites.update({p.stem.lower():p for p in folder.glob('*') if p.suffix.lower()=='.bmp'})
    for folder in [A/'engine/textures', A/'worlds/mm8/textures']:
        palettes.update({p.stem.lower():p for p in folder.glob('*') if p.suffix.lower()=='.act'})
    old = json.loads((QUEUE/'progress.json').read_text()) if (QUEUE/'progress.json').exists() else {'families':{}}
    ledger = {'schema_version':1, 'updated_utc':datetime.now(timezone.utc).isoformat(),
              'scope':'All MM8 native descriptor families plus stored orphan poses under their exact art prefixes.',
              'status_definitions':{'pending':'Sources inventoried; no enhanced artwork accepted', 'partial':'Some restoration work saved; full gate not passed', 'validated':'Full native coverage and all visual/export gates passed', 'blocked':'Concrete unresolved dependency; exact resume steps recorded'},
              'families':{}}
    for row in inventory['families']:
        if row['world'] != 'mm8':
            continue
        prefix = re.match(r'm\d{3}',row['standing_images'][0]).group()
        prior = old['families'].get(prefix,{})
        if row['completed_package'] and prior:
            ledger['families'][prefix] = dict(prior, status='validated', completed_package=row['completed_package'])
            print(prefix, 'reused validated package')
            continue
        root = HERE / ('mm8_' + prefix)
        root.mkdir(exist_ok=True)
        bindings = {}
        uses = defaultdict(list)
        first_palettes = {}
        for descriptor in row['descriptors']:
            d = descriptors[descriptor['id']]
            actions = {}
            for action, key in zip(ACTIONS, d[11:19]):
                group = groups[key.lower()]
                views = {}
                for v in range(8):
                    steps = []
                    for f in group['frames']:
                        name, mirror = resolve(f,v)
                        null = name.startswith('null')
                        step = dict(frame=None if null else name, native_texture=name, mirrored=mirror,
                                    duration_raw=f['frame_length_raw'], duration_ticks=f['frame_length_raw']*8,
                                    duration_ms=f['frame_length_raw']*62.5, palette=f.get('palette_id',0),
                                    scale=f.get('scale',1), flags=f.get('flags',[]),
                                    anchor='center' if 'Center' in f.get('flags',[]) else 'bottom-center')
                        steps.append(step)
                        if not null:
                            uses[name].append(dict(descriptor_id=descriptor['id'], action=action, view=v, palette=step['palette'], anchor=step['anchor']))
                            first_palettes.setdefault(name,step['palette'])
                    views[str(v)] = steps
                actions[action] = dict(native_group=key, native_group_record=group, views=views,
                                       playback='loop' if action in ('standing','walk') else 'hold' if action=='corpse' else 'once')
            bindings[str(descriptor['id'])] = dict(label=d[1], native_descriptor=d, actions=actions)
        assert set(uses)==set(row['images']), (prefix, set(uses)^set(row['images']))
        names = set(uses) | {n for n in sprites if re.fullmatch(prefix+r'[a-z]+[0-7]', n)}
        sources = {}
        duplicate = {}
        aliases = {}
        missing = []
        palette_ids = set(row['palettes'])
        default_pal = next(iter(bindings.values()))['actions']['standing']['views']['0'][0]['palette']
        for n in sorted(names):
            path = sprites.get(n)
            if path is None:
                missing.append(n)
                continue
            im = Image.open(path)
            assert im.mode=='P', (n,im.mode)
            ix=np.array(im)
            base=first_palettes.get(n,default_pal)
            palette_ids.add(base)
            if base:
                palpath=palettes.get('pal'+str(base))
                if palpath is None:
                    missing.append('palette:'+str(base));continue
                palhash=sha(palpath)
            else:
                palhash=hashlib.sha256(bytes(im.getpalette())).hexdigest()
            digest=hashlib.sha256(str(im.size).encode()+im.tobytes()+palhash.encode()).hexdigest()
            if digest in duplicate:
                aliases[n]=duplicate[digest]
            else:
                duplicate[digest]=n
            sources[n]=dict(path=str(path.relative_to(REPO)),sha256=sha(path),size=list(im.size),
                            pixel_hash=digest,base_palette=base,transparent_index=0,
                            referenced=n in uses, anchors=sorted({u['anchor'] for u in uses[n]}) if n in uses else [],
                            native_bbox=Image.fromarray((ix!=0).astype(np.uint8)*255).getbbox())
        pal_sources={}
        for pal in sorted(palette_ids):
            if pal==0:continue
            path=palettes.get('pal'+str(pal))
            if path:
                pal_sources[str(pal)]={'path':str(path.relative_to(REPO)),'sha256':sha(path)}
            else:missing.append('palette:'+str(pal))
        inv=dict(schema_version=1,creature='mm8:'+prefix,label=row['label'],sources=sources,pixel_aliases=aliases,
                 palette_sources=pal_sources,base_palette=default_pal,bindings=bindings,
                 orphan_images=sorted(names-set(uses)),source_tables=inventory['source_tables'],
                 descriptor_table={'path':'assets_dev/engine/data_tables/monster_descriptors.txt','sha256':sha(A/'engine/data_tables/monster_descriptors.txt')},
                 provenance_note='Pixel aliases include source size and base palette; timelines retain every native reference. Orphan poses receive no invented timing.')
        save(root/'sources.json',inv)
        # Identity first, then direction/action batches with exact indexed-pixel reuse.
        seen=set()
        jobs={}
        def add(key,ns,action,view):
            chosen=[]
            for n in ns:
                canonical=aliases.get(n,n)
                if canonical in sources and canonical not in seen:
                    chosen.append(canonical);seen.add(canonical)
            count=(len(chosen)+7)//8
            chunks=np.array_split(chosen,count) if count else []
            for j,chunk in enumerate(chunks):
                job=key if count==1 else key+'_'+str(j)
                jobs[job]=dict(frames=chunk.tolist(),action=action,view=view,state='pending',identity_required=key!='identity')
        first=next(iter(bindings.values()))['actions']
        identity=[]
        for v in range(8):
            n=first['standing']['views'][str(v)][0]['frame']
            if n:identity.append(n)
        add('identity',identity,'standing','native stored views')
        # Keep unbound stored poses with the matching native direction/stem;
        # generation grouping does not create playback bindings or durations.
        grouped=defaultdict(list)
        for n in sorted(names):
            code=n[len(prefix):-2]
            if code=='x':code='d'  # native corpse follows falling poses in one reference sheet
            grouped[(code,n[-1])].append(n)
        for (code,view),ns in sorted(grouped.items()):
            used_actions=sorted({u['action'] for n in ns for u in uses.get(n,[])})
            add(f'native_{code}_v{view}',ns,', '.join(used_actions) or f'unbound native stem {code}',view)
        assert seen==set(sources)-set(aliases),(prefix,set(sources)-set(aliases)-seen)
        previous=json.loads((root/'batches.json').read_text()) if (root/'batches.json').exists() else {}
        for key,job in jobs.items():
            if key in previous:
                assert previous[key]['frames']==job['frames'], 'Source changed: explicitly migrate existing checkpoints'
                job.update(previous[key])
        save(root/'batches.json',jobs)
        prior=old['families'].get(prefix,{})
        status=prior.get('status','pending')
        if missing:status='blocked'
        ledger['families'][prefix]=dict(prior,label=row['label'],status=status,project=str(root.relative_to(HERE)),
            referenced_images=len(uses),all_native_files=len(sources),unique_base_images=len(seen),pixel_aliases=len(aliases),
            orphan_images=len(names-set(uses)),batches=len(jobs),completed_package=row['completed_package'],
            blockers=sorted(set(missing)),resume=f'python3 level_generation/creatures/mm8_restore_queue.py references {prefix}',
            gates=prior.get('gates',dict(full_coverage=False,visual=False,animation=False,variants=False,edge_spill=False,atlas=False)))
        print(prefix,len(sources),'files',len(seen),'unique',len(jobs),'batches',status)
    ledger['summary']=dict(Counter(r['status'] for r in ledger['families'].values()))
    ledger['totals']={k:sum(r[k] for r in ledger['families'].values()) for k in ('referenced_images','all_native_files','unique_base_images','pixel_aliases','orphan_images','batches')}
    save(QUEUE/'progress.json',ledger)
    print(json.dumps(ledger['totals']))

def references(prefix):
    root=HERE/('mm8_'+prefix)
    inv=json.loads((root/'sources.json').read_text())
    batches=json.loads((root/'batches.json').read_text())
    for d in ('references','prompts','raw','review'):(root/d).mkdir(exist_ok=True)
    canvas=[max(s['size'][axis] for s in inv['sources'].values()) for axis in (0,1)]
    # Common source scale and origin, never silhouette fitting.
    scale=2
    cell=[v*scale+64 for v in canvas]
    for key,b in batches.items():
        cols=min(4 if len(b['frames'])>6 else 3,len(b['frames'])); rows=(len(b['frames'])+cols-1)//cols
        sheet=Image.new('RGBA',(cols*cell[0],rows*cell[1]))
        layout=[]
        for i,n in enumerate(b['frames']):
            im=native(root,n)
            offset=[(canvas[0]-im.width)//2,canvas[1]-im.height]
            x=i%cols*cell[0]+32+offset[0]*scale;y=i//cols*cell[1]+32+offset[1]*scale
            sheet.paste(im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST),(x,y))
            layout.append(dict(frame=n,cell_xywh=[i%cols*cell[0],i//cols*cell[1],*cell],source_origin=[x,y],native_size=list(im.size)))
        sheet.save(root/f'references/{key}.png')
        b.update(columns=cols,rows=rows,cell_size=cell,reference_scale=scale,common_canvas=canvas,layout=layout)
        prompt=f'''Use case: identity-preserve.
Asset type: high-detail restored Might and Magic VIII native creature sprites, {inv['label']}.
Input 1 is the exact native pose, appearance, color, lighting and layout authority: {cols} columns by {rows} rows, {len(b['frames'])} occupied cells, row-major order {', '.join(b['frames'])}. Action: {b['action']}; views: {b['view']}. Preserve each original pose and stored camera direction exactly.
Restore coherent finer surface detail for the SAME original creature. Preserve original anatomy, face, equipment, material boundaries, silhouette proportions, colors and dark/mid/light tonal weight. Preserve handedness, limb angles, foot lift and contact, foreshortening, tiny features and original expression. No redesign, added equipment, brightening, glossy toy surfaces or invented action.
Preserve equal cells, common source scale, source-relative positions and native empty margins. No individual recentering, stretching or fitting silhouettes to equal bounds. Keep each whole figure inside its assigned cell; empty cells remain empty. No duplicate, omitted or extra figures, text, grid lines, labels or watermarks.
Use a genuinely transparent PNG background with real alpha, clean edges, no matte spill, no painted checkerboard and no cast ground shadow. Retain intended translucent native effects if present. Deliver useful high-resolution per-pose detail, ideally at least the reference sheet size; packaging will separately preserve native logical dimensions.
'''
        if key!='identity':prompt+='Input 2 is the accepted restored identity/material reference only; its poses must not replace the requested native poses in input 1.\n'
        path=root/f'prompts/{key}.txt'
        if not path.exists():path.write_text(prompt)
    save(root/'batches.json',batches)
    ns=batches['identity']['frames'][:5]
    pals=[int(p) for p in inv['palette_sources']] or [0]
    cw,ch=320,340
    contact=Image.new('RGB',(cw*len(ns),ch*len(pals)),(45,45,45));draw=ImageDraw.Draw(contact)
    for y,pal in enumerate(pals):
        for x,n in enumerate(ns):
            im=native(root,n,pal)
            im.thumbnail((cw-16,ch-35),Image.Resampling.NEAREST)
            contact.paste(im,(x*cw+(cw-im.width)//2,y*ch+ch-im.height),im)
            draw.text((x*cw+8,y*ch+8),f'{n} palette {pal}',fill='white')
    contact.save(root/'references/native_variants.png')
    print(root, len(batches),'reference sheets')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','references'])
    parser.add_argument('family',nargs='?')
    args=parser.parse_args()
    if args.command=='prepare':prepare()
    else:references(args.family)
