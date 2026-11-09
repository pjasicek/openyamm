"""Author deterministic native MM8 decoration groups on Brackenford's final terrain.

Groups and exclusions express the design; seeded variation only fills those groups.
Existing MM8 sprite/descriptor identity is retained separately from stable authored IDs.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import random

from build_outdoor_content import terrain_height

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
SOURCE=PROJECT/'source'


def segment_distance(x,y,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)


def build(samples, tiles, semantics, content):
    reference=ROOT/'level_generation/evidence/mm8/out02_decorations.json'
    study=json.loads(reference.read_text())
    table_path=ROOT/'assets_dev/engine/data_tables/decoration_data.txt'
    expected=next(s['sha256'] for s in study['sources'] if s['path'].endswith('/decoration_data.txt'))
    assert hashlib.sha256(table_path.read_bytes()).hexdigest()==expected, 'Refresh decoration reference inventory'
    catalog={e['name']:e for e in study['records'] if e['visible'] and 'preview' in e}
    # Same-world cauldron and second pedestal art come from the inspected Alvar inventory.
    alvar=ROOT/'level_generation/evidence/mm8/out03_decorations.json'
    for entry in json.loads(alvar.read_text())['records']:
        if entry['visible'] and 'preview' in entry:catalog.setdefault(entry['name'],entry)
    plan=json.loads((PROJECT/'outdoor_plan.json').read_text())
    anchors=plan['native_scenery_landmarks']
    roads=[((c-64)*512+256,(64-r)*512-256) for road in semantics['roads'] for r,c in road['cells']]
    doors=[b['door_position'] for b in semantics['buildings']]
    actors=[a['position'] for a in content['actors']]
    landmarks=[p['position'] for p in content['landmarks']]
    arrivals=[a['xy'] for a in json.loads((PROJECT/'outdoor_plan.json').read_text())['arrivals']]
    perimeter=[(-20480,-10240),(0,-10240),(0,9216),(-20480,9216),(-20480,-10240)]
    groups=[]
    trees=['tree10','tree11','tree12','tree12','tree13']
    plants=['plant17','plant19','plant21','plant23','plant26','plant27','plant32']
    rocks=['rock01','rock02','rock05','rock16','rock17','rock20','rock22','rock25']
    for i,(x,y) in enumerate([(-15800,1000),(-17300,5300),(-9700,4600),(-4900,3700),
                              (-12800,-500),(-9500,-4200),(-7900,-7600),(-14900,-7000)]):
        groups.append(dict(id='town_garden_%02d'%i,center=[x,y],extent=[900,700],
                           count=15,palette=plants,category='plants',role='town garden'))
        groups.append(dict(id='town_tree_%02d'%i,center=[x,y],extent=[1400,1000],
                           count=3,palette=trees,category='trees',role='town accent'))
    for i,(x,y,w,d,count) in enumerate([(-11500,17800,8200,5200,70),(-22000,7000,1700,5500,25),
             (-12500,-18200,8500,5000,55),(-3500,-14500,2500,4500,25),(16500,10300,6000,6500,40),
             (21000,19500,2900,4200,30),(22200,-10500,1700,8500,30),(13200,-16000,6500,7200,45)]):
        groups.append(dict(id='grove_%02d'%i,center=[x,y],extent=[w,d],count=count,
                           palette=trees,category='trees',role='temperate countryside'))
        groups.append(dict(id='undergrowth_%02d'%i,center=[x,y],extent=[w,d],count=20,
                           palette=['plant17','plant19','plant27','plant31'],category='plants',role='grove edge'))
        groups.append(dict(id='rock_group_%02d'%i,center=[x,y],extent=[w,d],count=18,
                           palette=rocks,category='rocks',role='ground and slope accents'))
    # Driver's 1230 annotations: town interiors need authored garden/rock accents too.
    # Add these after the original groups so existing countryside seeds stay stable.
    for i,(x,y,w,d) in enumerate([
        (-11300,-3400,700,600),(-12300,-7100,700,550),(-8700,-7000,600,650),
        (-15200,-5900,600,550),(-16500,-700,600,500),(-11500,400,500,600),
        (-15100,-1100,600,550),(-12000,-1600,500,500),(-8300,1400,600,400),
        (-8300,-900,400,450),(-5950,-2300,500,500),(-16700,1900,500,550)]):
        for category,count,palette in [('plants',10,plants),('trees',2,trees),('rocks',2,rocks)]:
            groups.append(dict(id='infill_%02d_%s'%(i,category),center=[x,y],extent=[w,d],
                count=count,palette=palette,category=category,role='town infill garden and verge'))
    for category,count,palette in [('trees',8,['tree12','tree13']),('plants',16,plants),('rocks',5,rocks)]:
        groups.append(dict(id='pond_'+category,center=[-512,17920],extent=[2200,1800],count=count,
            palette=palette,category=category,role='quiet pond margin'))
    # A few contextual service/loot props, not another universal scatter layer.
    groups.extend([
        dict(id='east_cache_bones',center=[20700,2350],extent=[650,400],count=4,
             palette=['dec29'],category='props',role='ogre camp'),
        dict(id='south_cache_bones',center=[11500,-22200],extent=[500,500],count=4,
             palette=['dec29'],category='props',role='ogre camp'),
    ])
    # Fill previously empty town-side meadows and route shoulders, without another flower carpet.
    for identity,center,extent,count in [
        ('east_town_meadow',[-3200,6200],[3000,5400],42),
        ('south_town_meadow',[-11500,-10500],[6800,2700],30),
        ('bridge_east_verge',[10600,3800],[3300,3900],24),
        ('north_manor_shoulders',[-13500,10700],[6500,1800],18)]:
        for category,amount,palette in [('trees',count,trees),('rocks',max(5,count//3),rocks)]:
            groups.append(dict(id=identity+'_'+category,center=center,extent=extent,count=amount,
                palette=palette,category=category,role='meadow and route coverage'))
    for i,(x,y) in enumerate([(-12100,-3400),(-16700,-3500),(-5000,-2200)]):
        groups.append(dict(id='town_rough_pocket_'+str(i),center=[x,y],extent=[700,600],count=5,
            palette=['rock01','rock02','rock05','rock20','rock22'],category='rocks',role='rough town edge'))
        groups.append(dict(id='town_refuse_'+str(i),center=[x,y],extent=[700,600],count=2,
            palette=['dec23'],category='props',role='sparse refuse beside working/back plots'))
    records=[];native=[];decisions=[]

    def allowed(x,y,entry,category):
        if not (-23900<x<23900 and -23900<y<23900):return False
        c,r=math.floor(x/512+64),math.floor(64-y/512)
        if 126<=tiles[r*128+c]<162:return False
        z=terrain_height(x,y,samples)
        # Grounding uses the exact triangle; this broad slope guard samples both directions.
        dx=(terrain_height(x+32,y,samples)-terrain_height(x-32,y,samples))/64
        dy=(terrain_height(x,y+32,samples)-terrain_height(x,y-32,samples))/64
        if math.hypot(dx,dy)>(.6 if category=='rocks' else .45):return False
        radius=max(entry['radius'],32)
        margin=320 if category=='trees' else 128
        for b in semantics['buildings']:
            bx,by=b['xy'];w,d=b['target_footprint']
            if abs(x-bx)<w/2+radius+margin and abs(y-by)<d/2+radius+margin:return False
        if any(math.hypot(x-p[0],y-p[1])<640 for p in doors+landmarks+arrivals):return False
        if any(math.dist((x,y),a['xy'])<(1200 if a['id']=='hill_challenge' else 512) for a in anchors):return False
        if any(math.hypot(x-p['x'],y-p['y'])<radius+192 for p in actors):return False
        if any(math.hypot(x-p[0],y-p[1])<radius+(320 if category=='trees' else 220) for p in roads):return False
        if any(segment_distance(x,y,a,b)<radius+160 for a,b in zip(perimeter,perimeter[1:])):return False
        if 2500<x<8200 and -800<y<1300:return False
        if abs(x-15360)<3400 and abs(y-17920)<3400:return False
        if abs(x-15360)<2200 and abs(y+16640)<1900:return False
        for existing in records:
            ex,ey,_=existing['position']
            spacing=600 if category==existing['category']=='trees' else max(radius+existing['radius']+32,96)
            if math.hypot(x-ex,y-ey)<spacing:return False
        return True

    for group_index,group in enumerate(groups):
        rng=random.Random(73091+group_index*101)
        accepted=0
        for attempt in range(group['count']*100):
            if accepted>=group['count']:break
            x=round((group['center'][0]+rng.uniform(-1,1)*group['extent'][0])/16)*16
            y=round((group['center'][1]+rng.uniform(-1,1)*group['extent'][1])/16)*16
            name=rng.choice(group['palette']);entry=catalog[name]
            if not allowed(x,y,entry,group['category']):continue
            position=[x,y,terrain_height(x,y,samples)]
            index=len(native)+1 # Party start owns entity zero.
            semantic_id='decor_'+group['id']+'_%03d'%attempt
            record=dict(entry,index=index,position=position,semantic_id=semantic_id,
                        category=group['category'],role=group['role'],event=0,visible=True)
            # Reference spatial measurements describe Ravenshore, not this authored instance.
            for key in ['ground_z','ground_offset','grade','nearest_bmodel_xy']:
                record.pop(key,None)
            record['ground_z']=position[2]
            record['ground_offset']=0
            records.append(record)
            native.append(dict(entity_index=index,name=name,decoration_list_id=entry['id'],ai_attributes=0,
                position=dict(zip('xyz',position)),facing=0,event_id_primary=0,event_id_secondary=0,
                variable_primary=0,variable_secondary=0,special_trigger=0,initial_decoration_flag=0))
            accepted+=1
        decisions.append(dict(id=group['id'],requested=group['count'],placed=accepted))
    # Native interactive barrel family owns random +2 permanent stat rewards and persistent empty state.
    # These are authored anchors from the driver's four green dots, not a random scatter group.
    for barrel in json.loads((PROJECT/'outdoor_plan.json').read_text())['stat_barrels']:
        entry=catalog['dec03'];x,y=barrel['xy'];position=[x,y,terrain_height(x,y,samples)];index=len(native)+1
        record=dict(entry,index=index,position=position,semantic_id='stat_barrel_'+barrel['id'],category='props',
                    role='permanent stat barrel',event=0,visible=True,ground_z=position[2],ground_offset=0)
        records.append(record)
        native.append(dict(entity_index=index,name='dec03',decoration_list_id=entry['id'],ai_attributes=0,
            position=dict(zip('xyz',position)),facing=0,event_id_primary=0,event_id_secondary=0,
            variable_primary=0,variable_secondary=0,special_trigger=0,initial_decoration_flag=0))
    anchored=list(anchors)
    cx,cy=next(a['xy'] for a in anchors if a['id']=='hill_challenge')
    # An incomplete low-stone ring leaves a wide southern approach to the challenge.
    for i in range(18):
        if 11<=i<=15:continue
        angle=i*math.tau/18
        anchored.append(dict(id='challenge_stone_'+str(i),name='rock22',
            xy=[round(cx+880*math.cos(angle)),round(cy+720*math.sin(angle))],
            role='challenge stone setting with open approach',category='rocks'))
    for anchor in anchored:
        entry=catalog[anchor['name']];x,y=anchor['xy'];z=terrain_height(x,y,samples)
        assert not 126<=tiles[math.floor(64-y/512)*128+math.floor(x/512+64)]<162,anchor
        assert all(math.dist((x,y),p)>entry['radius']+256 for p in roads),anchor
        assert all(math.dist((x,y),(a['x'],a['y']))>entry['radius']+192 for a in actors),anchor
        assert all(math.dist((x,y),p[:2])>entry['radius']+256 for p in doors),anchor
        index=len(native)+1;position=[x,y,z]
        record=dict(entry,index=index,position=position,semantic_id=anchor['id'],category=anchor['category'],
            role=anchor['role'],event=0,visible=True,ground_z=z,ground_offset=0)
        for key in ['grade','nearest_bmodel_xy']:record.pop(key,None)
        records.append(record)
        native.append(dict(entity_index=index,name=entry['name'],decoration_list_id=entry['id'],ai_attributes=0,
            position=dict(zip('xyz',position)),facing=0,event_id_primary=0,event_id_secondary=0,
            variable_primary=0,variable_secondary=0,special_trigger=0,initial_decoration_flag=0))
    counts={category:sum(e['category']==category for e in records) for category in ['trees','plants','rocks','props','lights']}
    assert counts['trees']>=180 and counts['plants']>=100 and counts['rocks']>=40, counts
    result=dict(format_version=1,policy='Authored groups with deterministic variation and native clearance/grounding',
                counts=counts,groups=groups,placement_results=decisions,records=records,entities=native,
                reference=str(reference.relative_to(ROOT)),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                additional_reference=str(alvar.relative_to(ROOT)),additional_reference_sha256=hashlib.sha256(alvar.read_bytes()).hexdigest(),
                native_landmarks=anchors)
    (SOURCE/'lg01.decorations.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Native decoration source:',counts)
    return result


if __name__=='__main__':
    terrain=json.loads((SOURCE/'lg01.terrain.yml').read_text())
    build(bytes.fromhex(terrain['height_map_hex']),bytes.fromhex(terrain['tile_map_hex']),
          json.loads((SOURCE/'lg01.semantic.json').read_text()),json.loads((SOURCE/'lg01.content.json').read_text()))
