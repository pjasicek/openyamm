#!/usr/bin/env python3
"""Measure native decoration placement and prepare first-frame Blender study data.

Read-only game data; outputs are evidence, not a runtime decoration exporter.
Building distance is distance to the nearest BModel XY bounding box, not a city classifier.
Slope is the source terrain triangle grade; indoors nearest-wall distance is XY only.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / 'level_generation'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file, parse_odm_file


def load_catalog():
    table = ROOT / 'assets_dev/engine/data_tables/decoration_data.txt'
    catalog, names, aliases = {}, {}, {}
    for row in csv.reader(table.open(), delimiter='\t'):
        if not row or not row[0].isdigit():
            continue
        entry = dict(id=int(row[0])-1, name=row[1].lower(), hint=row[2],
                     radius=int(row[4]), height=int(row[5]), light_radius=int(row[6]),
                     light_rgb=list(map(int, row[7:10])), flags=row[11], sprite_id=int(row[12]))
        catalog[entry['id']] = entry
        names[entry['name']] = entry
        for alias in (row[14].split(',') if len(row) > 14 else []):
            aliases[alias.strip().lower()] = entry
    sprites = {}
    path = ROOT / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
    data = yaml.load(path.read_text(), Loader=yaml.CSafeLoader)
    for sprite in data['sprites']:
        frame = sprite['frames'][0]
        sprites[sprite['sprite_id']] = dict(name=sprite['sprite_name'], **frame)
    return catalog, names, aliases, sprites


def category(entry):
    name, hint = entry['name'], entry['hint'].lower()
    if 'tree' in name or 'tree' in hint or 'palm' in hint:
        return 'trees'
    if 'plant' in name or any(s in hint for s in ['flower', 'shrub', 'bush', 'cactus', 'mushroom']):
        return 'plants'
    if 'rock' in name or any(s in hint for s in ['rock', 'boulder', 'stalag', 'stalact', 'crystal']):
        return 'rocks'
    if entry['light_radius'] or any(s in hint for s in ['torch', 'brazier', 'fire', 'lamp', 'candle']):
        return 'lights'
    return 'props'


def terrain_sample(p, x, y):
    gx, gy = np.clip(x/512+64, 0, 126.999), np.clip(64-y/512, 0, 126.999)
    ix, iy = int(gx), int(gy)
    u, v = gx-ix, gy-iy
    heights = p['height_map']
    a, b, c, d = [heights[yy*128+xx]*32 for xx, yy in
                   [(ix, iy), (ix+1, iy), (ix, iy+1), (ix+1, iy+1)]]
    if u+v <= 1:
        z, dx, dy = a+u*(b-a)+v*(c-a), b-a, c-a
    else:
        z, dx, dy = d+(1-u)*(c-d)+(1-v)*(b-d), d-c, d-b
    return round(z, 2), round(float(np.hypot(dx, dy)/512), 3)


def measure(world, stem, kind, catalog_data):
    catalog, names, aliases, sprites = catalog_data
    path = ROOT / 'assets_dev/worlds' / world / 'maps' / (stem + ('.odm' if kind == 'outdoor' else '.blv'))
    p = (parse_odm_file if kind == 'outdoor' else parse_blv_file)(path)['payload']
    scene_path = path.with_suffix('.scene.yml')
    scene = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader)
    overrides = {e['entity_index']: e for e in scene.get('entities', [])}
    roots = [ROOT/'assets_dev/worlds'/world, ROOT/'assets_dev/engine']
    roots += sorted(r for r in (ROOT/'assets_dev/worlds').iterdir() if r.is_dir() and r.name != world)
    paths = {}
    for root in roots:
        for image in (root/'sprites').glob('*'):
            if image.suffix.lower() in ('.bmp', '.png'):
                paths.setdefault(image.stem.lower(), image)
    result = dict(world=world, map=path.name, kind=kind,
                  sources=[dict(path=str(f.relative_to(ROOT)), sha256=hashlib.sha256(f.read_bytes()).hexdigest())
                           for f in [path, scene_path, ROOT/'assets_dev/engine/data_tables/decoration_data.txt',
                                     ROOT/'assets_dev/engine/rendering/sprite_frame_data_common.yml']],
                  records=[], missing_sprites=[], models=[])
    if kind == 'outdoor':
        for model in p['bmodels']:
            vertices = np.array([[v[a] for a in 'xyz'] for v in model['vertices']])
            if not len(vertices):
                continue
            result['models'].append(dict(index=model['index'], name=model['name'],
                                         bounds=[vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
                                         textures=dict(Counter(f['texture_name'] for f in model['faces'])),
                                         events=sorted(set(f['cog_triggered_number'] for f in model['faces'])-{0})))
        heights = np.array(p['height_map']).reshape(128,128)*32
        result['height_percentiles'] = np.percentile(heights, [0,10,25,50,75,90,100]).tolist()
        result['grade_percentiles'] = np.percentile(np.hypot(*np.gradient(heights/512)), [25,50,75,90,100]).tolist()
    for source in p['entities']:
        e = dict(source)
        e.update(overrides.get(e['index'], {}))
        name = e['name'].strip().lower()
        raw = catalog.get(e['decoration_list_id'])
        entry = names.get(name) if name else catalog[0]
        if entry is None:
            entry = aliases.get(name) if raw is None or raw['name'] == 'pending' else None
            entry = entry or raw
        if entry is None:
            raise ValueError('Unresolved decoration: ' + repr(e))
        flags = entry['flags']
        visible = bool(entry['sprite_id']) and not ('DontDraw' in flags or
            (flags.isdigit() and int(flags)&2) or e.get('initial_decoration_flag', e['ai_attributes'])&32)
        record = dict(index=e['index'], source_name=e['name'], **entry,
                      category=category(entry), position=[e['position'][a] for a in 'xyz'],
                      facing=e['facing'], event=e['event_id_secondary'], visible=visible,
                      initial_flags=e.get('initial_decoration_flag',e['ai_attributes']))
        frame = sprites.get(entry['sprite_id'])
        if visible and frame:
            texture = frame['texture_name'].lower()
            image_path = paths.get(texture)
            if image_path is None and 'Image1' not in frame.get('flags', []):
                image_path = paths.get(texture+'0')
            if image_path:
                with Image.open(image_path) as image:
                    size = image.size
                    corner = list(image.convert('RGB').getpixel((0,0)))
                    rgb = np.array(image.convert('RGB'))
                    alpha = ~(((rgb[:,:,0]>=248)&(rgb[:,:,1]<=8)&(rgb[:,:,2]>=248)) |
                              ((rgb[:,:,0]<=8)&(rgb[:,:,1]>=248)&(rgb[:,:,2]>=248)))
                    palette_path = None
                    if image.mode == 'P':
                        indices = np.array(image)
                        alpha &= indices != 0
                        palette_name = 'pal%03d.act' % frame.get('palette_id',0)
                        palette_path = next((r/'textures'/palette_name for r in roots
                                             if (r/'textures'/palette_name).exists()), None)
                        if palette_path:
                            palette = np.frombuffer(palette_path.read_bytes()[:768],dtype=np.uint8).reshape(256,3)
                            rgb = palette[indices]
                    # Decode native indexed art and transparency, not a painted approximation.
                    sprite_dir = STUDY/'evidence'/world/'decoration_frames'
                    sprite_dir.mkdir(exist_ok=True)
                    decoded = sprite_dir/(entry['name']+'.png')
                    Image.fromarray(np.dstack((rgb,alpha.astype(np.uint8)*255))).save(decoded)
                record['preview'] = dict(path=str(image_path.relative_to(ROOT)), pixels=list(size),
                    scale=frame.get('scale',1.0), palette_id=frame.get('palette_id',0),
                    flags=frame.get('flags',[]), transparent_rgb=corner,
                    decoded_path=str(decoded.relative_to(ROOT)),
                    palette_path=str(palette_path.relative_to(ROOT)) if palette_path else None)
            else:
                result['missing_sprites'].append(dict(index=e['index'], texture=texture))
        elif visible:
            result['missing_sprites'].append(dict(index=e['index'], sprite_id=entry['sprite_id']))
        if kind == 'outdoor':
            x,y,z = record['position']
            ground, grade = terrain_sample(p,x,y)
            record.update(ground_z=ground, ground_offset=round(z-ground,2), grade=grade)
            distances = []
            for m in result['models']:
                lo, hi = m['bounds']
                distances.append(float(np.hypot(max(lo[0]-x,0,x-hi[0]), max(lo[1]-y,0,y-hi[1]))))
            record['nearest_bmodel_xy'] = round(min(distances),1) if distances else None
        result['records'].append(record)
    visible = [e for e in result['records'] if e['visible']]
    result['counts'] = dict(native=len(p['entities']), visible=len(visible),
        categories=dict(Counter(e['category'] for e in visible)),
        palette=dict(Counter(e['name'] for e in visible).most_common()),
        light_emitters=sum(bool(e['light_radius']) for e in visible))
    if kind == 'outdoor':
        result['placement'] = {}
        for cat in ['trees','plants','rocks','lights','props']:
            rows = [e for e in visible if e['category']==cat]
            result['placement'][cat] = dict(count=len(rows),
                within_1024_bmodel=sum(e['nearest_bmodel_xy'] is not None and e['nearest_bmodel_xy']<=1024 for e in rows),
                flat_grade_le_0125=sum(e['grade']<=.125 for e in rows),
                steep_grade_gt_05=sum(e['grade']>.5 for e in rows),
                median_ground_offset=float(np.median([e['ground_offset'] for e in rows])) if rows else None)
    target = STUDY/'evidence'/world/(stem+'_decorations.json')
    target.write_text(json.dumps(result,indent=2)+'\n')
    draw_plan(p,result,target.with_suffix('.png'))
    print(world+'/'+stem, result['counts']['categories'], 'missing', len(result['missing_sprites']), flush=True)
    return result


COLORS = dict(trees='#237d39', plants='#84a82b', rocks='#76553b', lights='#f19a18', props='#a538a8')


def draw_plan(p, report, target):
    fig, ax = plt.subplots(figsize=(10,9))
    if report['kind']=='outdoor':
        h=np.array(p['height_map']).reshape(128,128)*32
        ax.imshow(h,extent=(-32768,32768,-32768,32768),cmap='Greys',alpha=.25)
        for model in report['models']:
            lo,hi=np.array(model['bounds'])
            ax.add_patch(plt.Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor='#555b65',alpha=.4))
    else:
        v=np.array([[x[a] for a in 'xy'] for x in p['vertices']])
        edges=[]
        for face in p['faces']:
            if face['facet_type'] in (5,6) or face['is_portal']:
                continue
            points=v[face['vertex_indices']]
            edges.extend(zip(points,np.roll(points,-1,axis=0)))
        ax.add_collection(LineCollection(edges,colors='#91979c',linewidths=.35))
    for cat,color in COLORS.items():
        rows=[e for e in report['records'] if e['visible'] and e['category']==cat]
        if rows:
            xy=np.array([e['position'][:2] for e in rows])
            ax.scatter(xy[:,0],xy[:,1],s=12 if cat!='lights' else 25,c=color,
                       marker='*' if cat=='lights' else 'o', label=cat+' ('+str(len(rows))+')',alpha=.75)
    ax.autoscale();ax.set_aspect('equal')
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc='upper left',fontsize=9)
    ax.set_title(report['world']+'/'+report['map']+' — native decoration placement\n'
                 'Initial visible records; grey = terrain / geometry, not gameplay screenshot')
    ax.set_xlabel('X, native game units');ax.set_ylabel('Y, native game units')
    fig.tight_layout();fig.savefig(target,dpi=140);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map');args=parser.parse_args()
    manifest=json.loads((STUDY/'reference_maps.json').read_text())
    catalog=load_catalog()
    for kind,worlds in manifest.items():
        for world,maps in worlds.items():
            for stem in maps:
                if not args.map or args.map==world+'/'+stem:
                    measure(world,stem,kind,catalog)


if __name__=='__main__':
    main()
