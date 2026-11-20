"""Generate a quantized MM5 landscape draft and grounded, source-bound decoration placements.

Native geometry and gameplay registration are separate later authoring steps.
"""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import numpy as np
from scipy import ndimage,sparse
from scipy.sparse.linalg import spsolve
from matplotlib.path import Path as PolygonPath
from PIL import Image,ImageDraw,ImageFont
from build_plan import ROOT,OUT,SOURCE,read,write
from geography import SourceGeography,PLAYABLE,TERRAIN,CONTEXT_MAPS,CLASS_NAMES,CLASS_COLORS,MATERIALS

LAND=OUT/'landscape'
STEP=512


def segment_distance(q,a,b):
    q=np.asarray(q);a=np.asarray(a);v=np.asarray(b)-a
    t=np.clip(np.sum((q-a)*v,axis=-1)/np.sum(v*v),0,1)
    return np.sqrt(np.sum((q-a-t[...,None]*v)**2,axis=-1))


def box_distance(q,center,extent):
    d=np.maximum(np.abs(np.asarray(q)-center)-np.asarray(extent)/2,0)
    return np.sqrt(np.sum(d*d,axis=-1))


def ground(x,y,h):
    c0=x/512+64;r0=64-y/512
    assert 0<=r0<=127 and 0<=c0<=127,(x,y)
    c=min(126,int(math.floor(c0)));r=min(126,int(math.floor(r0)));u=c0-c;v=r0-r
    a,b,d,e=[float(h[rr,cc])*32 for rr,cc in [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]]
    return a+(b-a)*u+(d-a)*v if u+v<=1 else e+(d-e)*(1-u)+(b-e)*(1-v)


def surface_sampler():
    return SourceGeography()


def features(p):
    # The existing public well reservation becomes the central HP fountain; the well moves to a quiet back court.
    old=next(f for f in p['features'] if f['id']=='water_well')
    old.update(title='Secret back-court well',point=[-6048,1900],kind='gold_well',extent=[256,256],
        purpose='Discreet shared well north of the bank, between the diviners, workers and Nadia; useful exploration reward.',
        interaction=dict(status='specified; not registered in runtime',condition='party carried gold < 200',
            reward='add 200 carried gold',cooldown='once per game day, party-wide; failed checks consume nothing',
            state='mm5:sw/well/charity/last_day',bankGold='ignored',hint='Well',repeatHint='The bucket comes up empty.'))
    additions=[dict(id='healing_fountain',title='Central healing fountain',kind='healing_fountain',point=[-4204,-658],
        extent=[512,512],sources=[],evidence='user-requested MM6–8-style addition',
        purpose='A small stone basin in the central bank/boarding court, visible from the street with a clear approach.',
        interaction=dict(status='specified; not registered in runtime',target='selected living, non-eradicated character',
            effect='restore HP to current maximum; never reduce over-max HP',spellPoints=False,cureConditions=False,
            resurrection=False,cooldown='none',hint='Healing Fountain'))]
    barrels=[('forge',[-104,-2520]),('lodging',[-5450,-2140]),('maps',[-6540,-4140]),
             ('workers',[-5630,2350]),('temple',[-4140,5000]),('keeper',[980,2560])]
    for i,(owner,point) in enumerate(barrels,1):
        additions.append(dict(id='stat_barrel_'+owner,title=f'B{i}: stat barrel by {owner}',kind='stat_barrel',point=point,
            extent=[128,128],sources=[],evidence='user-requested additional reward',owner=owner,
            purpose='Single deliberate barrel in a side yard; accessible without blocking a house door.',
            interaction=dict(status='native rule reference; placement not exported',asset='dec03',
                effect='+2 permanent stat to selected character; stat chosen by native initial seed',
                fullEvents=[269,270,271,272,273,274,275],emptyEvent=268,
                consumption='once per barrel, shared depletion; preserve through save/load; no repeat reward on click',
                state='mm5:sw/barrel/'+owner,refill='proposed no refill for these six authored rewards')))
    additions.append(dict(id='reger_crossing',title='Reger islet foot crossing',kind='bridge',
        point=[-19904,-17664],extent=[3840,320],sources=[],evidence='terrain-fit accessibility adaptation',
        purpose='Narrow raised crossing from the hermitage islet eastern landing to the southern meadow bank. Preserve the original islet; bank ramps still need authored geometry.'))
    p['features']+=additions


def heightfield(p,surface):
    xx,yy=np.meshgrid((np.arange(128)-64)*512,(64-np.arange(128))*512);q=np.stack([xx,yy],axis=-1)
    smooth=lambda t:np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
    z=610+1050*np.exp(-((xx-16500)/10500)**2-((yy-16000)/9500)**2)
    z+=700*np.exp(-((xx+13000)/10500)**2-((yy-21000)/6500)**2)
    z+=500*np.exp(-((xx-20000)/7500)**2-((yy+14500)/10500)**2)
    z+=180*np.sin(xx/7100)*np.cos(yy/9100)
    # Coherent town shelf with a gradual rise north; individual pads resolve onto shared native vertices below.
    town=next(f for f in p['features'] if f['id']=='town_wall')['polygon']
    inside=PolygonPath(town).contains_points(q.reshape(-1,2)).reshape(128,128)
    town_weight=ndimage.gaussian_filter(inside.astype(float),1.5)
    city_target=640+320*smooth((yy+3000)/10000)
    z=z*(1-town_weight)+city_target*town_weight
    # Mark water cells and all four supporting vertices. They become flat surface planes, not sloping water.
    cell_class=np.array([[surface(x+256,y-256) for x,y in row] for row in q],dtype=np.uint8)
    fixed={};water_nodes={}
    for r,c in np.argwhere(np.isin(cell_class[:127,:127],[0,3,4,7])):
        level={0:0,3:256,4:768,7:1024}[int(cell_class[r,c])]
        for rr,cc in [(r,c),(r+1,c),(r,c+1),(r+1,c+1)]:
            node=rr*128+cc;previous=water_nodes.get(node,0)
            assert not (previous and level and previous!=level),('Incompatible water/lava surfaces',r,c)
            # A void shoreline may slope down; a shared water vertex must stay on its water plane.
            water_nodes[node]=max(previous,level)
    fixed.update(water_nodes)
    pads=[]
    for b in p['buildings']:
        if b['form'] in ['grove','hole','rope','drain','cave']:continue
        x,y=b['center'];w,d=b['envelope']
        if b['id']=='reger':
            w,d=448,384;b['foundationFootprint']=[w,d]
            b['terrainFitReason']='Compact hermitage foundation fits the single original river-islet cell; larger planning envelope includes roof/shore clearance.'
        # All vertices supporting the footprint, not just its center, must share the pad elevation.
        c0,c1=math.floor((x-w/2)/512+64),math.ceil((x+w/2)/512+64)
        r0,r1=math.floor(64-(y+d/2)/512),math.ceil(64-(y-d/2)/512)
        nodes={r*128+c for r in range(r0,r1+1) for c in range(c0,c1+1)}
        if nodes&water_nodes.keys():
            assert b['district']!='Castleview',('Town pad intersects water/rim',b['id'])
            original=list(b['center']);candidates=[]
            for dx in range(-1024,1025,256):
                for dy in range(-1024,1025,256):
                    cx,cy=x+dx,y+dy
                    nc0,nc1=math.floor((cx-w/2)/512+64),math.ceil((cx+w/2)/512+64)
                    nr0,nr1=math.floor(64-(cy+d/2)/512),math.ceil(64-(cy-d/2)/512)
                    ns={rr*128+cc for rr in range(nr0,nr1+1) for cc in range(nc0,nc1+1)}
                    if not ns&water_nodes.keys():candidates.append((dx*dx+dy*dy,dx,dy,ns))
            assert candidates,('No nearby dry foundation',b['id'])
            _,dx,dy,nodes=min(candidates,key=lambda a:a[0]);x+=dx;y+=dy
            b['terrainFitOriginalCenter']=original;b['center']=[x,y]
            if 'door' in b:b['door']=[b['door'][0]+dx,b['door'][1]+dy]
            b['terrainFitReason']='Small landward shift for a complete dry native foundation beside the original coarse shoreline.'
        pads.append(dict(owner=b['id'],nodes=nodes,target=float(z[round(64-y/512),round(x/512+64)])))
    # Neighbouring footprints sharing a grid vertex must share a physical shelf.
    components=[]
    for pad in pads:
        joined=[c for c in components if c['nodes']&pad['nodes']]
        nodes=set(pad['nodes']);members=[pad]
        for c in joined:nodes.update(c['nodes']);members+=c['members'];components.remove(c)
        components.append(dict(nodes=nodes,members=members))
    pad_records=[]
    for component in components:
        level=round(np.mean([m['target'] for m in component['members']])/32)*32
        for n in component['nodes']:fixed[n]=level
        for m in component['members']:
            b=next(b for b in p['buildings'] if b['id']==m['owner'])
            b['earlierPadHeightProposal']=b.get('padHeightProposal');b['padHeightProposal']=level
            b['terrainIntent']='Flat native supporting triangles, shared shelf where neighbouring footprint vertices overlap; graded connecting ground.'
            pad_records.append(dict(owner=b['id'],height=level,supportVertices=sorted(m['nodes'])))
    # Smooth the broad authored landform under exact water/pad constraints.
    n=128*128;matrix=sparse.lil_matrix((n,n));rhs=np.zeros(n);flat=z.ravel()
    for i in range(n):
        if i in fixed:matrix[i,i]=1;rhs[i]=fixed[i];continue
        r,c=divmod(i,128);neighbors=[rr*128+cc for rr,cc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)] if 0<=rr<128 and 0<=cc<128]
        matrix[i,i]=len(neighbors)+.08;rhs[i]=.08*flat[i]
        for j in neighbors:matrix[i,j]=-1
    h=np.clip(np.rint(spsolve(matrix.tocsr(),rhs).reshape(128,128)/32),0,255).astype(np.uint8)
    from grade_inner_road import apply as apply_inner_road_grade
    apply_inner_road_grade(h,pad_records)
    for b in p['buildings']:
        if 'terrainFitOriginalCenter' in b:
            for site in p['sourceSites']:
                if site['owner']==b['id']:site['plannedPoint']=b['center']
    # Native array orientation is north-up, sample r,c -> ((c-64)*512,(64-r)*512).
    Image.fromarray(h).save(LAND/'heightmap_u8.png')
    Image.fromarray(h.astype(np.uint16)*32).save(LAND/'heightmap_units_u16.png')
    (LAND/'heightmap.raw').write_bytes(h.tobytes())
    Image.fromarray(cell_class).save(LAND/'surface_classes.png')
    metadata=dict(status='Generated terrain source draft; not a packaged ODM',width=128,height=128,
        horizontalSpacing=512,verticalUnit=32,origin=[-32768,32768],rowDirection='south',columnDirection='east',
        sampleBounds=TERRAIN,travelBounds=p['travelBounds'],
        playableBounds=PLAYABLE,renderedQuadShape=[127,127],
        bufferWidths=dict(west=8192,north=8192,east=7680,south=7680),
        displayPolicy='Default minimaps crop to travel bounds; full terrain is a separate authoring view. Travel envelope includes water/void: it is not an all-walkable collision mask.',
        triangleSplit='NW–NE–SW when fractional column + fractional row <= 1; SE–SW–NE otherwise',
        files=dict(samplesU8='heightmap_u8.png',worldUnitsU16='heightmap_units_u16.png',raw='heightmap.raw'),
        terrainFitAdjustments=[dict(owner=b['id'],before=b['terrainFitOriginalCenter'],after=b['center']) for b in p['buildings'] if 'terrainFitOriginalCenter' in b],
        minimumHeight=int(h.min())*32,maximumHeight=int(h.max())*32,
        waterLevels=dict(river=256,acidPond=768,void=0),lavaLevel=1024,pads=pad_records,
        surfaceClasses={str(i):name for i,name in enumerate(CLASS_NAMES)},
        materialFamilies={str(i):name for i,name in enumerate(MATERIALS)},
        materialStatus='Source-based palette families, not final native tile-bank assignments; Acid Pond needs its own water tint.',
        terrainContextMaps=CONTEXT_MAPS,
        authoring='Broad hills and shared flat pads are authored adaptations; MM5 cells provide horizontal land/water geography, not recovered elevation.',
        sources=[dict(path=str((SOURCE/f'maps/dark_initial_state/maze{n:04}.dat.json').relative_to(ROOT)),
            sha256=hashlib.sha256((SOURCE/f'maps/dark_initial_state/maze{n:04}.dat.json').read_bytes()).hexdigest()) for n in range(1,25)])
    profiles={}
    for name,points in [('north',[[-24576+i*512,24576] for i in range(97)]),('east',[[24576,24576-i*512] for i in range(97)])]:
        profiles[name]=[dict(x=x,y=y,z=round(ground(x,y,h),3)) for x,y in points]
    (LAND/'travel_edge_profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
    (LAND/'terrain.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return h,cell_class,metadata


def catalogue():
    cat={}
    for name in ['out02','out03']:
        for r in read(ROOT/f'level_generation/evidence/mm8/{name}_decorations.json')['records']:
            if r.get('visible') and 'preview' in r:cat.setdefault(r['name'],r)
    return cat


def buffer_landscape(p,h,classes,surface,decor):
    """Record the complete rendered apron, with decorative scenery and source provenance."""
    mask=np.zeros((128,128),dtype=np.uint8)
    source_maps=np.zeros((128,128),dtype=np.uint8)
    cells=[]
    for r in range(127):
        for c in range(127):
            x,y=(c-64)*512+256,(64-r)*512-256
            inside=PLAYABLE[0]<x<PLAYABLE[1] and PLAYABLE[2]<y<PLAYABLE[3]
            mask[r,c]=1 if inside else 2
            source=surface.describe(x,y)
            source_maps[r,c]=0 if source['outsideSourceWorld'] else source['map']
            if not inside:cells.append((r,c,x,y,source))
    Image.fromarray(mask).save(LAND/'terrain_domain_mask.png')
    Image.fromarray((mask==1).astype(np.uint8)*255).save(LAND/'playable_crop_mask.png')
    Image.fromarray(source_maps).save(LAND/'source_map_ids.png')
    cat=catalogue();records=[]
    for r,c,x,y,source in cells:
        cls=int(classes[r,c]);forest=source['scenery'] in [2,3,5,6,8,11,13,14,15]
        if cls in [0,3,4,6,7]:continue
        rng=random.Random(f'mm5:sw/apron/{r}/{c}')
        probability=.26 if forest and cls in [1,2] else (.055 if cls in [2,5,8,10] else .10)
        if rng.random()>probability:continue
        name=rng.choice(['tree10','tree11','tree12']) if forest and cls in [1,2] else rng.choice(['rock01','rock02','rock05'])
        category='trees' if name.startswith('tree') else 'rocks'
        entry=cat[name];rad=max(entry['radius'],entry['preview']['pixels'][0]*entry['preview']['scale']/2)
        x+=rng.randint(-160,160);y+=rng.randint(-160,160)
        if not (TERRAIN[0]+rad<x<TERRAIN[1]-rad and TERRAIN[2]+rad<y<TERRAIN[3]-rad):continue
        # Canopies may cross the travel line: it must not become a visible clearing.
        if max(abs(x),abs(y))<=24576:continue
        if any(surface(x+dx,y+dy) in [0,3,4,6,7] for dx,dy in [(0,0),(rad,0),(-rad,0),(0,rad),(0,-rad)]):continue
        if any(segment_distance([x,y],a,b)<rad+road['width']/2+64
               for road in p['roads'] for a,b in zip(road['points'],road['points'][1:])):continue
        if any(math.dist([x,y],t['point'])<rad+1536 for t in p['travel']):continue
        if any(math.dist([x,y],d['position'][:2])<.72*(rad+d['visualRadius']) for d in records+decor['records']):continue
        slope=math.hypot(ground(x+32,y,h)-ground(x-32,y,h),ground(x,y+32,h)-ground(x,y-32,h))/64
        if slope>(.45 if category=='trees' else .7):continue
        records.append(dict(id=f'mm5:sw/apron/{r}/{c}',name=name,category=category,
            position=[x,y,round(ground(x,y,h),3)],visualRadius=rad,descriptorId=entry['id'],
            assetSource=entry['preview']['path'],source=surface.describe(x,y),sceneryOnly=True))
    result=dict(status='Scenery-only terrain buffer draft; native export pending',records=records,
        counts=dict(Counter(r['category'] for r in records)),
        policy='No NPCs, encounters, rewards, interactable props or arrival targets in the buffer.',
        placement='Source forest cells receive temperate trees; dry, desert and rock cells sparse rocks. Water and void stay clear. Full native visual radii, road clearance and slopes checked.')
    (LAND/'buffer_scenery.json').write_text(json.dumps(result,indent=2)+'\n')
    provenance=dict(playableBounds=PLAYABLE,terrainBounds=TERRAIN,axisOrder='xmin,xmax,ymin,ymax',
        bufferWidths=dict(west=8192,north=8192,east=7680,south=7680),
        masks=dict(domain='terrain_domain_mask.png',domainValues={'0':'unused stored row/column','1':'playable map crop','2':'scenery buffer'},
            crop='playable_crop_mask.png',cropMeaning='255 inside travel envelope; 0 elsewhere. Not a walkability mask.',
            sourceMaps='source_map_ids.png',sourceMapMeaning='Original maze number at each rendered quad centre; 0 outside original world or unused storage.'),
        sourceProjection='gx=floor((x+24576)/1536), gy=floor((y+24576)/1536); maze=1+4*floor(gx/16)+3-floor(gy/16)',
        neighbours=[dict(side='north',region='nw',title='Alamar / Necropolis',sourceMaps=[2,6],
                        neighbourCentreInThisMap=[0,49152],intent='Acid Pond narrows and closes; dirt, rock, desert and a small scorched fringe follow actual A2/B2 cells. Lava lies farther north.'),
                    dict(side='east',region='sc',title='Sprite Forest / Southern Tower',sourceMaps=[11,12],
                        neighbourCentreInThisMap=[49152,0],intent='Continue the river bends, dry ground and forest cells from C3/C4; trade road reaches the terrain edge.'),
                    dict(side='northeast corner',region='nc',sourceMaps=[10],neighbourCentreInThisMap=[49152,49152],intent='C2 desert continues around the corner.'),
                    dict(side='west / south',region=None,intent='Original outer cells are Xeen void. Continue that void, not an invented sea; water extension is used only if an original world-edge cell is water.')],
        overlapContract='When neighbours are generated, reuse these source cells and world-aligned heights/materials/scenery throughout overlapping terrain, including both buffers; matching only a travel-edge line is insufficient.',
        neighbourHeightStatus='Neighbouring native terrains do not exist yet; this heightfield and edge profiles are the handoff, not verified native seams.',
        minimapPolicy='Default region PNG/SVG and HTML show only the playable crop. Buffer review is a separate opt-in authoring page; concatenate playable crops for the world map.',
        renderedQuads=int(np.count_nonzero(mask)),playableQuads=int(np.count_nonzero(mask==1)),bufferQuads=len(cells))
    (LAND/'buffer.json').write_text(json.dumps(provenance,indent=2)+'\n')
    p['landscape']['buffer']='landscape/buffer.json'
    return result,mask


def placements(p,h,surface):
    cat=catalogue();placed=[];decisions=[];walls=next(f for f in p['features'] if f['id']=='town_wall')['polygon']
    roads=[(a,b,r['width']/2) for r in p['roads'] for a,b in zip(r['points'],r['points'][1:])]
    approaches=[(b['frontage']['points'][0],b['frontage']['points'][1],96) for b in p['buildings'] if 'frontage' in b]
    paths=[(a,b,96) for f in p['features'] if f['kind']=='path' for a,b in zip(f['points'],f['points'][1:])]
    arrivals=[p['defaultArrival']['point']]+[t['arrival'] for t in p['travel']]+[m['plannedPoint'] for m in p['mirrorArrivals']]
    arrivals += [b.get('door',b['center']) for b in p['buildings'] if b['id'] in ['skyrope','troll_a','troll_b','troll_c','sewer_out','mine','western','kalindra','tower']]
    obstacles=[f for f in p['features'] if f['kind'] in ['water','healing_fountain','gold_well','stat_barrel','chest','entrance','quest_item','bridge','challenge']]
    def radius(name):
        r=cat[name];pr=r['preview'];return max(r['radius'],pr['pixels'][0]*pr['scale']/2)
    def allowed(point,rad,category,ignore=None):
        x,y=point
        if not(-24000<x<24000 and -24000<y<24000):return 'boundary'
        if surface(x,y) in [0,3,4,7]:return 'water/void/lava'
        if any(surface(x+dx,y+dy) in [0,3,4,7] for dx,dy in [(rad,0),(-rad,0),(0,rad),(0,-rad)]):return 'shore crown'
        slope=math.hypot(ground(x+32,y,h)-ground(x-32,y,h),ground(x,y+32,h)-ground(x,y-32,h))/64
        if slope>(.7 if category=='rocks' else .45):return 'slope'
        if category in ['trees','props','interactive'] and any(
            math.dist(point,e['center'])<rad+384 for e in p['encounters'] if e['hostility']!='Scripted interior'):
            return 'encounter core'
        if category in ['props','interactive']:
            supports=[ground(x+dx,y+dy,h) for dx,dy in [(rad,0),(-rad,0),(0,rad),(0,-rad)]]
            if max(supports)-min(supports)>64:return 'prop foundation slope'
        margin=64 if category in ['trees','interactive'] else 24
        for b in p['buildings']:
            if box_distance(point,b['center'],b['envelope'])<rad+margin:return 'building'
        for a,b,w in roads+approaches+paths:
            if segment_distance(point,a,b)<rad+w+(64 if category=='trees' else 24):return 'road/approach'
        for a,b in zip(walls,walls[1:]+walls[:1]):
            if segment_distance(point,a,b)<rad+128+32:return 'wall'
        if any(math.dist(point,a)<(1536 if category=='trees' else 384)+rad for a in arrivals):return 'arrival'
        for f in obstacles:
            if f['id']==ignore:continue
            if box_distance(point,f['point'],f.get('extent',[256,256]))<rad+96:return 'interaction'
        for r in placed:
            spacing=.72*(rad+r['visualRadius']) if category==r['category']=='trees' else rad+r['visualRadius']+24
            if math.dist(point,r['position'][:2])<spacing:return 'other decoration'
        return None
    def put(identity,name,point,category,group,role,rad=None,**extra):
        r=cat.get(name);x,y=point
        record=dict(id='mm5:sw/decor/'+identity,name=name,position=[x,y,round(ground(x,y,h),3)],category=category,
            group=group,purpose=role,visualRadius=rad if rad is not None else radius(name),
            collisionRadius=r['radius'] if r else None,descriptorId=r['id'] if r else None,
            assetSource=r['preview']['path'] if r else 'new independently authored Garrote-style BModel required',**extra)
        rr=record['visualRadius']
        heights=[ground(x+dx,y+dy,h) for dx,dy in [(0,0),(rr,0),(-rr,0),(0,rr),(0,-rr)]]
        record['terrainSupportRange']=[round(min(heights),3),round(max(heights),3)]
        if not r:
            record['foundation']=dict(platformZ=math.ceil(max(heights)/32)*32,
                skirtBottomZ=math.floor(min(heights)/32)*32-32,
                rule='New BModel stone/timber base must reach through terrain to skirt bottom; fit visible platform to this height. Geometry not generated.')
        placed.append(record);return record
    # Named interaction anchors are resolved first; move only within their named court if clearance requires it.
    for f in [f for f in p['features'] if f['kind'] in ['healing_fountain','gold_well','stat_barrel']]:
        rad=f['extent'][0]/2;original=f['point'];candidates=[original]
        for dist in [96,192,288,384,480,576,672]:
            for angle in np.arange(0,math.tau,math.tau/16):candidates.append([round(original[0]+dist*math.cos(angle)),round(original[1]+dist*math.sin(angle))])
        point=next((q for q in candidates if not allowed(q,rad,'interactive',f['id'])),None)
        assert point is not None,('No clear interaction anchor',f['id'])
        f['point']=point;f['terrainHeight']=round(ground(*point,h),3)
        if point!=original:f['earlierPointProposal']=original
        name='dec03' if f['kind']=='stat_barrel' else 'mm5:prop/'+f['kind']
        put(f['id'],name,point,'interactive','town_interactions',f['purpose'],rad,interaction=f['interaction'],featureId=f['id'])
    # Preserve the nine original non-event benches as actual outdoor scenery placements.
    source_sites={tuple(s) for f in p['sourceSites'] for s in [[f['map'],f['x'],f['y']]]}
    props=[dict(identity='source_bench_'+str(o['sourceOffset']),owner=o['owner'],name='mm5:prop/bench',
        radius=176,sourceObject=o['id'],sourceCoordinates=o['source']) for o in p['sourceObjects']
        if o['source'][0]==29 and o['sprite']==4 and tuple(o['source']) not in source_sites]
    assert len(props)==9
    for i,owner in enumerate(['forge','forge','tavern','maps','puzzle','workyard']):
        props.append(dict(identity='working_crates_'+str(i),owner=owner,name='mm5:prop/crate_stack',radius=128))
    for prop in props:
        b=next((b for b in p['buildings'] if b['id']==prop['owner']),None)
        anchor=b['center'] if b else next(f for f in p['features'] if f['id']==prop['owner'])['point']
        rng=random.Random(prop['identity']);candidates=[]
        for attempt in range(2000):
            angle=rng.uniform(0,math.tau);distance=rng.uniform(300,1400)
            q=[round(anchor[0]+math.cos(angle)*distance),round(anchor[1]+math.sin(angle)*distance)]
            if not allowed(q,prop['radius'],'props'):candidates.append(q)
            if len(candidates)==20:break
        assert candidates,('No clear source prop location',prop['identity'])
        point=min(candidates,key=lambda q:math.dist(q,anchor))
        rec=put(prop['identity'],prop['name'],point,'props','working_courts',
            'Original non-event bench' if 'sourceObject' in prop else 'Plain service stock scenery; no loot or interaction',
            prop['radius'],owner=prop['owner'],sourceObject=prop.get('sourceObject'),sourceCoordinates=prop.get('sourceCoordinates'))
        if 'sourceObject' in prop:
            o=next(o for o in p['sourceObjects'] if o['id']==prop['sourceObject']);o['plannedPosition']=rec['position'];o['decoration']=rec['id']
    # Use smaller native tree13 crowns for the dense source orchard; don't shrink the large tree sprites arbitrarily.
    groups=[dict(g) for g in p['foliageGroups']]
    orchard=next(g for g in groups if g['id']=='public_orchard');orchard['palette']=['tree13']
    orchard['purpose']='55 distinct MM5 tree sites represented by small native tree13 crowns; individual source effects preserved.'
    # New bounded low planting pockets around the focal point and working streets; no map-wide random carpet.
    for i,(center,extent,count) in enumerate([([-4500,-1580],[800,600],12),([-6600,2100],[600,500],8),
        ([-4550,3650],[750,450],8),([-1850,-3900],[700,900],12),([2350,-2350],[650,600],8)]):
        groups.append(dict(id='infill_'+str(i),title='Town verge pocket '+str(i+1),center=center,extent=extent,
            palette=['plant17','plant19','plant27','rock01'],targetCount=count,purpose='Small contextual planting/stone accents between working premises'))
    # Place the mandatory source orchard first so later cosmetic tree groups cannot displace its identities.
    groups.sort(key=lambda g:g['id']!='public_orchard')
    for g in groups:
        rng=random.Random(int(hashlib.sha256(g['id'].encode()).hexdigest()[:8],16));count=0;reject=Counter()
        for attempt in range(max(4000,g['targetCount']*600)):
            if count==g['targetCount']:break
            name=rng.choice(g['palette']);category='trees' if name.startswith('tree') else 'rocks' if name.startswith('rock') else 'plants'
            point=[round((g['center'][k]+rng.uniform(-.5,.5)*g['extent'][k])/8)*8 for k in [0,1]]
            rad=radius(name);why=allowed(point,rad,category)
            if why:reject[why]+=1;continue
            put(g['id']+f'/{count:03d}',name,point,category,g['id'],g['purpose']);count+=1
        decisions.append(dict(id=g['id'],requested=g['targetCount'],placed=count,rejections=dict(reject),
            extent=g['extent'],center=g['center'],palette=g['palette'],purpose=g['purpose']))
    orchard_records=[r for r in placed if r['group']=='public_orchard']
    original_trees=[f for f in p['features'] if f.get('owner')=='public_orchard' and f['kind'] in ['tree','reward_tree','food_tree']]
    assert len(orchard_records)==len(original_trees)==55,('Source orchard must fit',len(orchard_records))
    for record,f in zip(orchard_records,original_trees):
        record['sourceFeature']=f['id'];record['sourceCoordinates']=f['sources'];record['sourceEffect']=f['kind']
        f.update(point=record['position'][:2],positionStatus='Individual grounded landscape placement',decoration=record['id'])
        for s in p['sourceSites']:
            if [s['map'],s['x'],s['y']] in f['sources']:s['plannedPoint']=f['point']
    for original in p['foliageGroups']:
        resolved=next(d for d in decisions if d['id']==original['id'])
        original['placedCount']=resolved['placed'];original['palette']=resolved['palette']
        original['initialSketchExclusion']=original.pop('exclusion',{})
        original['exclusion']={'basis':'visual radius plus category-specific buffers', 'specification':'landscape/decorations.json#placementRules'}
        original['resolvedExclusions']='landscape/decorations.json records the visual-crown, road, frontage, wall, water, interaction and encounter-core checks.'
    # Keep source non-interactive object/bed/puzzle identities in their existing records, not random props.
    result=dict(status='Grounded placement draft; not exported to runtime',records=placed,groups=decisions,
        placementRules=dict(buildingMargin='visual radius + 64 for trees/interactive props, +24 for other categories',
            roadMargin='visual radius + actual half-width +64 for trees, +24 otherwise; also checks primary approaches and orchard path',
            wallMargin='visual radius +128 half-thickness +32',arrival='visual radius +1536 for trees, +384 otherwise',
            interactionMargin='visual radius +96 beyond reserved interaction footprint',
            encounterCore='visual radius +384 around each outdoor encounter centre for trees, props and interactive anchors',
            maximumSlope='0.7 rocks; 0.45 other categories, sampled over 64 units',
            maximumCustomPropSupportVariation=64,
            revision='Replaces blanket sketch buffers with explicit category and native visual-footprint checks. Original sketch exclusions remain in layout.json for review.'),
        spacing='Visual radius uses full source frame width × native scale / 2; tree canopies may overlap by up to 28% of summed radii. Trunks, buildings and routes remain clear.',
        sources=[dict(path='assets_dev/engine/data_tables/decoration_data.txt',sha256=hashlib.sha256((ROOT/'assets_dev/engine/data_tables/decoration_data.txt').read_bytes()).hexdigest())],
        limits=['Exact sprite opaque silhouette, renderer-facing billboard effects and native mesh collision require visual blockout review.',
            'Fountain/well need newly authored geometry and event overlays; recorded interaction rules are not live.',
            'Interior beds, storehouse puzzle chests and source empty-chest/bench props stay in their premises records for geometry authoring.'])
    (LAND/'decorations.json').write_text(json.dumps(result,indent=2)+'\n')
    with (LAND/'decorations.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['id','asset','category','group','x','y','z','source_feature'])
        for r in placed:writer.writerow([r['id'],r['name'],r['category'],r['group'],*r['position'],r.get('sourceFeature','')])
    for category in ['trees','plants','rocks','props','interactive']:
        density=np.zeros((128,128),dtype=np.uint8)
        for r in placed:
            if r['category']==category:
                x,y,_=r['position'];density[math.floor(64-y/512),int(x//512+64)]+=1
        Image.fromarray(density).save(LAND/(category+'_density_u8.png'))
    p['landscape']=dict(terrain='landscape/terrain.json',decorations='landscape/decorations.json',review='landscape/index.html')
    return result


def verify(p,h,terrain,decor,classes,buffer,mask,surface):
    road_checks=[]
    for r in p['roads']:
        grades=[]
        for a,b in zip(r['points'],r['points'][1:]):
            steps=math.ceil(math.dist(a,b)/64)
            for i in range(steps):
                q=np.asarray(a)+(np.asarray(b)-a)*i/steps;z=np.asarray(a)+(np.asarray(b)-a)*(i+1)/steps
                grades.append(abs(ground(*q,h)-ground(*z,h))/math.dist(q,z))
        road_checks.append(dict(id=r['id'],maximumLongitudinalGrade=round(max(grades),4)))
    assert all(r['maximumLongitudinalGrade']<=.5 for r in road_checks),road_checks
    frontage_checks=[]
    for b in p['buildings']:
        if 'frontage' not in b:continue
        a,z=map(np.asarray,b['frontage']['points']);steps=math.ceil(math.dist(a,z)/32)
        values=[ground(*(a+(z-a)*i/steps),h) for i in range(steps+1)]
        grade=max(abs(x-y)/(math.dist(a,z)/steps) for x,y in zip(values,values[1:]))
        frontage_checks.append(dict(owner=b['id'],maximumGrade=round(grade,4)))
    assert all(r['maximumGrade']<=.5 for r in frontage_checks),frontage_checks
    for pad in terrain['pads']:
        assert all(int(h.ravel()[i])*32==pad['height'] for i in pad['supportVertices']),pad['owner']
        assert all(int(h.ravel()[p['index']])*32==p['height']
                   for p in pad.get('gradedSupportVertices',[])),pad['owner']
    bridge_reports=[]
    for bridge in [f for f in p['features'] if f['kind']=='bridge']:
        x,y=bridge['point'];w,d=bridge['extent']
        values=[ground(xx,yy,h) for xx in np.linspace(x-w/2,x+w/2,65) for yy in np.linspace(y-d/2,y+d/2,65)]
        bridge['terrainCheck']=dict(minimum=round(min(values),2),maximum=round(max(values),2),deckTop=math.ceil((max(values)+64)/32)*32)
        bridge_reports.append(dict(id=bridge['id'],**bridge['terrainCheck'],status='Full reserved deck footprint checked; final bank ramps and mesh still to author.'))
    deficits=[dict(id=g['id'],requested=g['requested'],placed=g['placed']) for g in decor['groups'] if g['requested']!=g['placed']]
    assert np.count_nonzero(mask==1)==96*96 and np.count_nonzero(mask==2)==127*127-96*96
    assert np.all(mask[127,:]==0) and np.all(mask[:,127]==0)
    assert np.all(mask[16:112,16:112]==1)
    source_ids=set();water_cells=Counter()
    for r in range(127):
        for c in range(127):
            x,y=(c-64)*512+256,(64-r)*512-256
            source=surface.describe(x,y);cls=int(classes[r,c])
            assert source['classification']==cls
            if mask[r,c]==2 and not source['outsideSourceWorld']:source_ids.add(source['map'])
            if cls in [3,4,7]:
                level={3:256,4:768,7:1024}[cls]
                assert np.all(h[r:r+2,c:c+2].astype(int)*32==level),('Non-flat fluid cell',r,c,cls)
                water_cells[CLASS_NAMES[cls]]+=1
    assert source_ids=={2,6,10,11,12},source_ids
    # Across each travel line, at least one actual water strip must remain connected.
    north_pond=int(np.count_nonzero((classes[15,:127]==4)&(classes[16,:127]==4)))
    east_river=int(np.count_nonzero((classes[:127,111]==3)&(classes[:127,112]==3)))
    assert north_pond>0 and east_river>0,(north_pond,east_river)
    assert all(max(abs(d['position'][0]),abs(d['position'][1]))<24576 for d in decor['records'])
    assert all(max(abs(d['position'][0]),abs(d['position'][1]))>24576 and d['sceneryOnly'] for d in buffer['records'])
    required_points=[b['center'] for b in p['buildings']]+[e['center'] for e in p['encounters']]
    required_points+=[t['arrival'] for t in p['travel']]+[p['defaultArrival']['point']]
    required_points+=[s['plannedPoint'] for s in p['sourceSites']]
    assert all(max(abs(x),abs(y))<24576 for x,y in required_points)
    assert any(road['points'][-1]==[32256,5376] for road in p['roads'])
    report=dict(passed=True,heightSamples=16384,quantization=32,flatPads=len(terrain['pads']),roads=road_checks,
        maximumRoadGrade=max(r['maximumLongitudinalGrade'] for r in road_checks),primaryFrontages=frontage_checks,sourceOrchardTrees=55,
        counts=dict(Counter(r['category'] for r in decor['records'])),groupShortfalls=deficits,bridges=bridge_reports,
        buffer=dict(renderedQuads=127*127,playableQuads=96*96,bufferQuads=int(np.count_nonzero(mask==2)),
            sampledNeighbourMaps=sorted(source_ids),sceneryCounts=buffer['counts'],
            northConnectedPondCells=north_pond,eastConnectedRiverCells=east_river,
            flatFluidQuads=dict(water_cells),requiredDecorationsOutsidePlayableBounds=0,
            neighbourNativeHeightSeams='Pending neighbouring terrain generation; original horizontal source continuity checked.'),
        scope='Native triangle grounding, full supporting pad vertices, road centerline grade and placement clearances. Native game/AI, tile transitions and new prop geometry remain untested.')
    (LAND/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def draw(p,h,classes,decor,report,buffer):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,LinearSegmentedColormap
    from matplotlib.patches import Rectangle,Circle,Polygon
    from validate_plan import strip
    records=decor['records'];terrain=read(LAND/'terrain.json')
    xx=(np.arange(128)-64)*512;yy=(64-np.arange(128))*512
    colors={'trees':'#225632','plants':'#87a342','rocks':'#72706c','interactive':'#f0c157','props':'#986d40'}
    land_heights=LinearSegmentedColormap.from_list('land_heights',plt.get_cmap('terrain')(np.linspace(.25,1,256)))
    files=[]
    for view in ['region','town','buffer']:
        town=view=='town';full=view=='buffer'
        bounds=(-9800,4500,-8500,9000) if town else (TERRAIN if full else PLAYABLE)
        for kind in ['height','decoration']:
            fig,ax=plt.subplots(figsize=(13,12));fig.patch.set_facecolor('#eff0e6');ax.set_facecolor('#eff0e6')
            if kind=='height':
                im=ax.imshow(h.astype(float)*32,extent=(-33024,32512,-32512,33024),origin='upper',cmap=land_heights,vmin=0,vmax=1800)
                ax.contour(xx,yy,h.astype(float)*32,levels=np.arange(128,2048,128),colors='#3b4639',linewidths=.45,alpha=.5)
                fig.colorbar(im,ax=ax,shrink=.65,pad=.015,label='Elevation in native units (32 per height byte)')
                fluids=np.ma.masked_where(~np.isin(classes[:127,:127],[0,3,4,7]),classes[:127,:127])
                ax.imshow(fluids,extent=TERRAIN,origin='upper',cmap=ListedColormap(CLASS_COLORS),
                    vmin=0,vmax=len(CLASS_NAMES)-1,interpolation='nearest',zorder=2)
            else:
                ax.imshow(classes[:127,:127],extent=TERRAIN,origin='upper',cmap=ListedColormap(CLASS_COLORS),
                    vmin=0,vmax=len(CLASS_NAMES)-1,interpolation='nearest')
            if not town:
                ax.annotate('Acid Pond\nwater Z = 768'+('\ncontinues into A2 / B2' if not full else ''),
                    (-700,23200),xytext=(-6500,28200) if full else (-7800,21300),fontsize=9,
                    arrowprops=dict(arrowstyle='->',color='#20536b'),color='#174b60',zorder=10,
                    bbox=dict(facecolor='#e9f7ef',alpha=.9,edgecolor='none',pad=3))
            if full:
                ax.add_patch(Rectangle((-24576,-24576),49152,49152,fill=False,
                    edgecolor='#812f40',lw=1.8,linestyle='--',zorder=9))
                for x,y,label in [(13000,30500,'NORTH BUFFER → Alamar / Necropolis'),
                    (28500,-2000,'EAST BUFFER\nSprite Forest /\nSouthern Tower'),
                    (-28300,-17000,'WEST\nVOID'),(0,-28900,'SOUTH BUFFER · Xeen void'),
                    (28000,27700,'C2 desert')]:
                    ax.text(x,y,label,ha='center',va='center',fontsize=7,color='#183c3e',zorder=10,
                        bbox=dict(facecolor='#f9f2dc',alpha=.85,edgecolor='none',pad=3))
            wall=next(f for f in p['features'] if f['id']=='town_wall')['polygon']
            q=np.array(wall+[wall[0]]);ax.plot(q[:,0],q[:,1],color='#62675b',lw=3)
            for road in p['roads']:
                for a,b in zip(road['points'],road['points'][1:]):
                    ax.add_patch(Polygon(strip(a,b,road['width']),facecolor='#d7bf8d',edgecolor='none',zorder=3))
                for point in road['points']:ax.add_patch(Circle(point,road['width']/2,facecolor='#d7bf8d',edgecolor='none',zorder=3))
            for feature in p['features']:
                if feature['kind'] not in ['water','bridge']:continue
                x,y=feature['point'];w,d=feature['extent']
                ax.add_patch(Rectangle((x-w/2,y-d/2),w,d,facecolor='#68a0b6' if feature['kind']=='water' else '#c2a06c',edgecolor='#526056',lw=.8,zorder=5))
            for b in p['buildings']:
                x,y=b['center'];w,d=b['envelope'];ax.add_patch(Rectangle((x-w/2,y-d/2),w,d,facecolor='#cdc4a8',edgecolor='#464a40',lw=.9,zorder=4))
                if bounds[0]<x<bounds[1] and bounds[2]<y<bounds[3]:
                    ax.text(x,y,b['label']+(f'\n{b.get("padHeightProposal",round(ground(x,y,h)))}' if kind=='height' else ''),fontsize=6 if not town else 8,ha='center',va='center',zorder=6)
            if kind=='decoration':
                for r in records+(buffer['records'] if full else []):
                    x,y,z=r['position'];cat=r['category']
                    if cat=='trees':ax.add_patch(Circle((x,y),r['visualRadius'],facecolor=colors[cat],edgecolor='#163c23',alpha=.7,lw=.35,zorder=5))
                    elif cat=='props':
                        w,d=(320,128) if r['name'].endswith('/bench') else (176,176)
                        ax.add_patch(Rectangle((x-w/2,y-d/2),w,d,facecolor=colors[cat],edgecolor='#5f4c36',lw=.5,zorder=6))
                    elif cat!='interactive':ax.scatter([x],[y],s=10,c=colors[cat],marker={'plants':'.','rocks':'^'}[cat],edgecolors='none',zorder=6)
                for category,color in colors.items():ax.scatter([],[],c=color,label=category,s=35)
                ax.legend(loc='lower left' if full else 'upper right',framealpha=.9)
            for f in p['features']:
                if f['kind'] not in ['healing_fountain','gold_well','stat_barrel','gate']:continue
                x,y=f['point'];label={'healing_fountain':'HP fountain','gold_well':'Secret well','gate':'West gate' if f['id']=='west_gate' else 'South gate'}.get(f['kind'],f['title'].split(':')[0])
                if f['kind'] in ['healing_fountain','gold_well']:
                    ax.add_patch(Circle((x,y),f['extent'][0]/2,facecolor='#6cabbc',edgecolor='#777568',lw=2,zorder=7))
                    ax.add_patch(Circle((x,y),32,facecolor='#d2cab1',edgecolor='none',zorder=8))
                elif f['kind']=='stat_barrel':ax.add_patch(Rectangle((x-64,y-64),128,128,facecolor='#aa753f',edgecolor='#4a3425',lw=.8,zorder=7))
                else:ax.scatter([x],[y],s=60,facecolor='#f5dfa7',edgecolor='#534e3b',zorder=7)
                if town:ax.annotate(label,(x,y),xytext=(8,8),textcoords='offset points',fontsize=8,zorder=8,bbox=dict(facecolor='#fff9de',alpha=.85,edgecolor='none',pad=1))
            ax.set(xlim=bounds[:2],ylim=bounds[2:],aspect='equal',xlabel='X native units',ylabel='Y native units / north ↑',
                title=('Castleview town' if town else ('Full terrain · dashed line = travel bounds' if full else 'Castleview–Kalindra · playable map crop'))+' — '+('heightmap' if kind=='height' else 'foliage / decorations'))
            fig.text(.08,.025,('Water colours override elevation tint: river 256 · Acid Pond 768 · dark rim = void. ' if kind=='height' else 'Source-based terrain materials; final native tile banks pending. ')+('Buffer is scenery only.' if full else 'Outer terrain buffer hidden.'),fontsize=9)
            fig.tight_layout(rect=(0,.04,1,1));name=view+'_'+kind
            fig.savefig(LAND/(name+'.png'),dpi=150);fig.savefig(LAND/(name+'.svg'));plt.close(fig);files.append(name)
    # Small native palette sheet; source frames are displayed unchanged, with their original native scale recorded.
    cat=catalogue();names=sorted({r['name'] for r in records if r['name'] in cat});sheet=Image.new('RGB',(1000,math.ceil(len(names)/5)*210+50),'#e9ebdf');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);draw.text((10,10),'Selected native sprite art — unchanged source frames, independently fitted previews',font=font,fill='black')
    for i,name in enumerate(names):
        entry=cat[name];im=Image.open(ROOT/entry['preview']['decoded_path']).convert('RGB');im.thumbnail((180,160))
        x=i%5*200;y=50+i//5*210;sheet.paste(im,(x,y));draw.text((x+4,y+163),name+' / scale '+str(entry['preview']['scale']),font=font,fill='black')
    sheet.save(LAND/'sprite_palette.png')
    def sections(names):
        return ''.join(f'<section id="{name}"><h2>{name.replace("_"," ").title()}</h2><a href="{name}.png"><img src="{name}.png"></a></section>' for name in names)
    body=sections([name for name in files if not name.startswith('buffer_')])
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>MM5 landscape review</title><style>body{font:16px system-ui;background:#eff0e6;color:#263b30;margin:24px}nav{position:sticky;top:0;background:#eff0e6;padding:12px;display:flex;gap:20px;flex-wrap:wrap}img{max-width:100%;width:1300px}a{color:#246783}p{max-width:1000px;line-height:1.5}</style><h1>Castleview–Kalindra: heightmap and decorations</h1><p>Actual native-resolution height samples and individually grounded scenery. Central HP fountain, secret charity well and six stat barrels are planned additions; their runtime events are not installed.</p><nav><a href="#town_height">Town height</a><a href="#town_decoration">Town decoration</a><a href="#region_height">Region height</a><a href="#region_decoration">Region decoration</a><a href="../LANDSCAPE.md">Design and checks</a><a href="../index.html">Interactive city plan</a><a href="decorations.csv">Placement CSV</a></nav>'''+body+'<h2>Selected native sprite palette</h2><img src="sprite_palette.png"></html>'
    note='<p>Default maps show the ±24,576 travel envelope, including its water and void, rather than the full terrain grid. The crop is not a walkability mask. <a href="buffer.html">Show full terrain and scenery buffer (authoring view)</a>. Water is shown explicitly on height previews: Acid Pond is an elevated water surface at 768 and continues north; the river is at 256.</p>'
    page=page.replace('<nav>',note+'<nav>',1)
    (LAND/'index.html').write_text(page)
    buffer_page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>MM5 full terrain buffer</title><style>body{font:16px system-ui;background:#eff0e6;color:#263b30;margin:24px}img{max-width:100%;width:1300px}p{max-width:1000px;line-height:1.5}a{color:#246783}</style><h1>Full terrain and scenery buffer — authoring view</h1><p><a href="index.html">Return to playable-crop maps</a> · <a href="buffer.json">Bounds, neighbours and overlap contract</a> · <a href="buffer_scenery.json">Buffer scenery placements</a></p><p>The dashed square is the travel boundary, not a wall. Terrain extends 8,192 units west/north and 7,680 east/south. No required content belongs in that apron. North uses A2/B2, east C3/C4, and the northeast corner C2. Water follows those source cells rather than stopping or repeating at the travel line. West/south continue Xeen's void.</p><p>Scenery-only trees and rocks follow original forest/dry-ground cells. This draft does not prove an invisible cutoff in the engine: normal player-height and flying views, tile transitions and neighbouring height/prop continuity still need native blockout review.</p>'''+sections([name for name in files if name.startswith('buffer_')])+'</html>'
    (LAND/'buffer.html').write_text(buffer_page)


def build():
    LAND.mkdir(exist_ok=True);p=read(OUT/'layout.json')
    # Re-running this stage is deterministic without duplicating its authored features.
    p['features']=[f for f in p['features'] if f['kind'] not in ['healing_fountain','stat_barrel'] and f['id']!='reger_crossing']
    features(p);surface=surface_sampler();h,classes,terrain=heightfield(p,surface)
    decor=placements(p,h,surface);buffer,mask=buffer_landscape(p,h,classes,surface,decor)
    report=verify(p,h,terrain,decor,classes,buffer,mask,surface);write('layout.json',p)
    write('source_objects.json',p['sourceObjects'])
    draw(p,h,classes,decor,report,buffer)
    print(json.dumps(report,indent=2))

if __name__=='__main__':build()
