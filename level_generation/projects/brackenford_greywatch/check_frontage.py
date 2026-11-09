"""Fast visual/data calibration from actual tile bitmap corners and native door faces.

No gameplay scenarios. Center distances are layout proxies, not painted-road edge clearance.
"""
from pathlib import Path
import argparse
import csv
import json
import math
import sys
import numpy as np
from PIL import Image, ImageDraw

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
BASELINE=PROJECT/'review/frontage_revision'
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file

parser=argparse.ArgumentParser()
parser.add_argument('--source',action='store_true')
parser.add_argument('--review-directory',default='frontage_revision')
args=parser.parse_args()
OUT=PROJECT/'review'/args.review_directory
OUT.mkdir(parents=True,exist_ok=True)
semantic=json.loads((PROJECT/'source/lg01.semantic.json').read_text())
terrain=json.loads((PROJECT/'source/lg01.terrain.yml').read_text())
tiles=np.array(list(bytes.fromhex(terrain['tile_map_hex']))).reshape(128,128)
if not args.source:
    native=parse_odm_file(PROJECT/'runtime/worlds/mm8/maps/lg01.odm')['payload']
    assert np.array_equal(tiles,np.array(native['tile_map']).reshape(128,128))
table={int(r['index']):r['texture_name'].lower() for r in csv.DictReader(
    (ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t')}
paths={p.stem.lower():p for p in (ROOT/'assets_dev/worlds/mm8/textures').glob('*.bmp')}
images={}
def tile_image(raw):
    key=table[int(raw) if raw<198 else int(raw)-198+414]
    if key not in images:images[key]=Image.open(paths[key]).convert('RGB')
    return images[key]

# Independent classification of the bitmap corner colors; never import the author's mask dictionary.
def corners(raw):
    if 1<=raw<=12 or raw>=198:return ['dirt']*4
    if raw==126:return ['water']*4
    a=np.array(tile_image(raw),float)
    result=[]
    for x,y in [(0,0),(120,0),(0,120),(120,120)]:
        red,green,blue=a[y:y+8,x:x+8].mean((0,1))
        if 90<=raw<126:kind='grass' if green>red else 'dirt'
        elif 126<=raw<162:kind='water' if red>180 and blue>180 else 'dirt'
        elif 162<=raw<198:kind='rock' if red>85 else 'dirt'
        else:raise AssertionError(raw)
        result.append(kind)
    return result
colors={int(raw):corners(int(raw)) for raw in np.unique(tiles)}
def seam_errors(tilemap):
    errors=[]
    for r in range(127):
        for c in range(127):
            a=colors[int(tilemap[r,c])]
            if c<126:
                b=colors[int(tilemap[r,c+1])]
                if [a[1],a[3]]!=[b[0],b[2]]:errors.append([r,c,'east',a,b])
            if r<126:
                b=colors[int(tilemap[r+1,c])]
                if [a[2],a[3]]!=[b[0],b[1]]:errors.append([r,c,'south',a,b])
    return errors

seams=seam_errors(tiles)
before_tiles=np.array(list(bytes.fromhex(json.loads((BASELINE/'before/lg01.terrain.yml').read_text())['tile_map_hex']))).reshape(128,128)
colors.update({int(raw):corners(int(raw)) for raw in np.unique(before_tiles) if int(raw) not in colors})
before_seams=seam_errors(before_tiles)

# Native active house faces, not labels or texture-name guesses (MM8 doors are often t14*03).
reference=parse_odm_file(ROOT/'assets_dev/worlds/mm8/maps/out02.odm')['payload']
cat=json.loads((ROOT/'level_generation/catalogues/mm8_ravenshore/catalogue.json').read_text())
ref_doors=[]
for model in cat['models']:
    for service in model['services']:
        if not service['houses'] or not service['active_faces']:continue
        faces=[model['face_records'][i] for i in service['active_faces']]
        points=np.array([f['center'][:2] for f in faces])
        ref_doors.append(dict(model=model['index'],event=service['event'],title=service['title'],
                              xy=points.mean(0).tolist()))

def road_centers(tilemap):
    rows,cols=np.where(np.array(tilemap).reshape(128,128)>=198)
    return np.array([(c*512-32512,32512-r*512) for r,c in zip(rows,cols)])

def distance_records(doors,centers):
    return [dict(d,nearest_road_cell_center=round(float(np.linalg.norm(centers-d['xy'],axis=1).min()),1))
            for d in doors]

def quartiles(records):
    return np.percentile([r['nearest_road_cell_center'] for r in records],[25,50,75]).round(1).tolist()
ref_records=distance_records(ref_doors,road_centers(reference['tile_map']))
generated={}
for label,s in [('before',json.loads((BASELINE/'before/lg01.semantic.json').read_text())),('after',semantic)]:
    centers=np.array(list({(c*512-32512,32512-r*512) for p in s['roads'] for r,c in p['cells']}))
    entries=[dict(building=b['id'],xy=b['door_position'][:2]) for b in s['buildings']]
    generated[label]=distance_records(entries,centers)
    # Exclude automatic one-house spurs when comparing the ordinary frontage to the shared street.
    ordinary=[b for b in s['buildings'] if b['id'] not in ['civic_hall','temple','tavern']]
    street=np.array(list({(c*512-32512,32512-r*512) for path in s['roads']
        if not path['id'].endswith('_lane') for r,c in path['cells']}))
    generated[label+'_shared_street']=distance_records(
        [dict(building=b['id'],xy=b['door_position'][:2]) for b in ordinary],street)
    print(label,quartiles(generated[label]))
# Clearance in each rotated house's local coordinates: roads may not run underneath it.
roads=np.array(list({(c*512-32512,32512-r*512) for p in semantic['roads'] for r,c in p['cells']}))
lane_alignments=[]
for b in semantic['buildings']:
    if b.get('approach_kind')!='dedicated_lane':continue
    delta=roads-np.array(b['door_position'][:2]);nearest=delta[np.linalg.norm(delta,axis=1).argmin()]
    nx,ny=b['door_outward'];lateral=abs(nearest[0]*ny-nearest[1]*nx)
    lane_alignments.append(dict(building=b['id'],lateral_error=round(float(lateral),2)))
    assert lateral<=64,(b['id'],lateral)
assert max(r['nearest_road_cell_center'] for r in generated['after_shared_street'])<550
collisions=[]
for b in semantic['buildings']:
    theta=math.radians(b['rotation_degrees']);co,si=math.cos(theta),math.sin(theta)
    offsets=roads-b['xy'];local=offsets@np.array([[co,-si],[si,co]])
    w,d=b['local_footprint']
    if np.any((np.abs(local[:,0])<w/2+96)&(np.abs(local[:,1])<d/2+96)):collisions.append(b['id'])

# Draw an orthographic textured terrain plan with actual facade locations and door normals.
r0,r1,c0,c1=45,80,24,57
size=64
canvas=Image.new('RGB',((c1-c0)*size,(r1-r0)*size))
for r in range(r0,r1):
    for c in range(c0,c1):canvas.paste(tile_image(int(tiles[r,c])).resize((size,size)),((c-c0)*size,(r-r0)*size))
def screen(x,y):return ((x/512+64-c0)*size,(64-y/512-r0)*size)
draw=ImageDraw.Draw(canvas)
for b in semantic['buildings']:
    x,y=b['xy'];w,d=b['local_footprint'];a=math.radians(b['rotation_degrees']);co,si=math.cos(a),math.sin(a)
    polygon=[screen(x+co*u-si*v,y+si*u+co*v) for u,v in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
    draw.polygon(polygon,fill='#9d815b',outline='white',width=2)
    dx,dy=b['door_position'][:2];nx,ny=b['door_outward']
    draw.line([screen(dx,dy),screen(dx+nx*300,dy+ny*300)],fill='cyan',width=4)
    draw.text(screen(x-w/2,y+d/2+140),b['id'],fill='white',stroke_fill='black',stroke_width=1)
decor=json.loads((PROJECT/'source/lg01.decorations.json').read_text())
for e in decor['records']:
    x,y=screen(*e['position'][:2]);radius={'trees':9,'plants':3,'rocks':5,'props':4,'lights':5}[e['category']]
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill={'trees':'#32d054','plants':'#edcf74','rocks':'#aabbcc','props':'orange','lights':'#ff7799'}[e['category']])
for p in semantic['content_landmarks']:
    x,y=screen(*p['position'][:2]);radius=45 if p['id']=='town_fountain' else 14
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),outline='cyan',width=3)
canvas.save(OUT/'frontage_plan.png')
report=dict(mode='source' if args.source else 'native',reference_method='Active house entrance face centroids to nearest road tile center; this is a conservative grid-distance proxy, not exact painted-edge setback.',
 reference=dict(count=len(ref_records),quartiles=quartiles(ref_records),records=ref_records),
 generated={k:dict(quartiles=quartiles(v),records=v) for k,v in generated.items()},
 lane_alignments=lane_alignments,tile_corners=colors,corner_seam_errors=seams,before_corner_seam_error_count=len(before_seams),road_house_collisions=collisions,
 decoration_counts=decor['counts'])
(OUT/'frontage_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('Ravenshore',len(ref_records),quartiles(ref_records),'seams',len(seams),'collisions',collisions)
assert not seams,seams[:10]
assert not collisions,collisions
