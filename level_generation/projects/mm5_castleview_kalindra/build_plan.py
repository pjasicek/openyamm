"""Build a source-linked layout proposal, not runtime content or a complete event conversion."""
from collections import Counter
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'reference/mm4_5_world_of_xeen/unpacked'
sys.path.insert(0, str(ROOT / 'level_generation/projects/mm5_world_feasibility'))
from analyze import clean


def read(p):
    return json.loads(p.read_text())


def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def source_xy(n, x, y):
    return [-24576 + (x + (16 if n in [7,8] else 0) + .5) * 1536,
            -24576 + (y + (16 if n in [3,7] else 0) + .5) * 1536]


# Castleview is rotated 180 degrees to face the regional road/river to the south.
# Local urban coordinates are independent of the source grid; north is still +Y in final native coordinates.
def town_xy(x, y):
    return [2696 - x, 5892 - y]


# Logical premises may share one physical assembly. Quality describes construction, never proven personal wealth.
BUILDINGS = [
# id, title, local x/y, envelope width/depth, form, quality, facing, source NPC/service coordinates, purpose
('guild', "Ol’ Black Magic", 1450,9300,1280,1100,'L','maintained','E',[(3,27),(5,28)],'Guild spell service and Metla’s membership desk; shared institution.'),
('forge', 'Ogre Foundry',2800,7600,1536,1000,'hall','working','W',[(9,22)],'Single combined MM5 blacksmith, not invented separate weapon/armor shops; service yard and forge storage.'),
('training','Tog’s Training / swimming annex',2800,5600,1536,1000,'L','working','E',[(8,17),(7,19)],'Level training and Ordana’s separate lesson door share a building; practice water in the adjacent yard.'),
('jail','Castleview Jail',1000,6600,1088,1536,'hall','fortified','E',[(1,20)],'Jasper remains in a covered prison wing reached by the sewer route; freeing him is not a normal house visit.'),
('monks_n','First Drawkcab chapterhouse',4450,8000,1280,640,'long','plain','S',[(13,23),(16,23)],'Tinit and Bob share premises with two identifiable study stations; preserve dialogue sequence.'),
('monks_s','Drawkcab study house',4850,5450,1152,640,'long','plain','N',[(13,15),(16,15)],'Pip and Otto share a second house across the meditation court; preserve all four monks.'),
('bank','Milken Savings / accounts',7000,5550,1408,832,'long','maintained','W',[(21,16),(27,25)],'Bank service plus Rex’s accounting office share the block; no invented separate vault reward.'),
('tavern','Blacksmoke Tavern',6750,8900,1664,1280,'L','working','W',[(20,25),(18,20),(20,23)],'Inn service; Tanya and Gloria are recurring common-room contacts, not evidence of family or home ownership.'),
('lodging','Adventurers’ lodging',8250,7200,1152,768,'long','working','E',[(20,21),(20,22)],'Esteban and Bleys occupy separate rented rooms; tower-roof and elusive-treasure clues stay available.'),
('maps','Mapmakers’ court',9250,9200,1664,1088,'L','maintained','W',[(22,24),(30,23),(30,20)],'Three destinations in one joined workshop: Jethro’s household, Lydia’s lesson room, Miles’s examination room.'),
('mayor','Mayor’s office and editorial room',8300,10984,1664,1088,'L','civic','S',[(23,27),(16,30)],'Snarfblad and Majot share civic premises through separate doors; office hierarchy, not a private palace.'),
('workyard','Taskmaster’s hiring office',10100,10750,832,640,'compact','working','S',[(25,30)],'Jojosh pays for work; small office beside a working yard, not a quest mansion.'),
('joe','Joe’s map stall',6650,10600,512,512,'stall','makeshift','S',[(28,30)],'A separate sales destination near arrivals; fraud and out-to-lunch state remain separate from legitimate mapmakers.'),
('ranger','Goldur’s lodge',10500,7900,832,640,'compact','plain','W',[(29,27)],'Pathfinding teacher with an outdoor practice garden; independent from MM8 weapon mastery.'),
('herbalist','Zelda’s house and drying shed',9878,6100,1088,768,'L','plain','W',[(25,21)],'Herbalist’s herb plot and orb handover; no new alchemist retail service inferred.'),
('nadia','Nadia’s house',10200,4450,896,768,'compact','worn','W',[(27,19)],'Hoarded domestic storage and sewer grievance. Worn, crowded house is a design interpretation, not proof of poverty.'),
('diviners','Oorla’s house / Troyanna’s room',6840,3700,1280,832,'long','plain','N',[(17,10),(20,20)],'Two distinct dialogue contacts in shared rented premises. Oorla owns the orb guidance; retain the source Neena naming discrepancy in the census.'),
('king','Gremlin court',10200,2450,1536,1664,'court','fortified','W',[(29,13)],'Covered quest compound connected to sewer BLV; audience, staged guards, surrender/death and three disks remain inside.'),
('tower','Ellinger’s Tower',3600,3400,1536,1536,'octagon','arcane','E',[(12,10)],'Distinct locked BLV entrance and tower silhouette; key, traps and Energy Disk quest remain indoors.'),
('temple','Temple of Mok',5700,1000,1664,1280,'apse','civic','N',[(15,1),(18,22)],'Healing temple and Imble’s ordinary conversation share a venue; he is not silently promoted to proprietor.'),
('crafts','Tailor and cobbler row',7900,1450,1792,768,'long','working','N',[(16,3),(30,30)],'Gromlug and Sojo share a physical row with separate workshop doors; their original clues do not create new retail systems.'),
('workers','Workers’ shared house',8300,3000,1024,512,'long','worn','S',[(14,4),(16,5)],'Daron and Tolberti share lodging by the craft yard; source titles and opinions do not establish wealth or family ties.'),
('keeper','Keeper’s cottage and kennel',2100,4000,896,640,'L','working','W',[(9,18),(10,16)],'Sinbolas’s working yard; Raymond shares a room. Preserve separate dialogue identities.'),
('puzzle','Dyson’s public storehouse',1650,1800,2176,1792,'hall','working','E',[(8,5)],'Two roofed puzzle bays, each nine chests, plus Dyson’s desk. Chest toggles are a puzzle, not eighteen ordinary loot rolls.'),
]

# Roles are grounded in source titles and dialogue; service proprietors without a known name remain unnamed.
ROLE_OVERRIDES = {
 'Ordana': 'teacher: Swimming (250 gold)', 'Goldur':'teacher: Pathfinder (1500 gold)',
 'Lydia':'teacher: Cartography (10 gold)', 'Miles':'challenge: Cartographer’s test; not a skill teacher',
 'Metla':'guild membership (50 gold)', 'Jojosh':'paid work (50 gold/week)',
 'Jasper':'prisoner / rescue target', 'Gettlewaithe':'conditional antagonist / negotiation quest',
 'Nadia':'necklace quest giver', 'Zelda':'orb quest handover', 'Mayor':'Gremlin quest giver',
 'Jethro':'rescue quest and genuine treasure map', 'Joe':'fraudulent treasure-map seller',
 'Madame':'orb guidance', 'Dyson':'chest-puzzle clue',
 'Pip':'Drawkcab lesson', 'Otto':'Drawkcab lesson', 'Bob':'Drawkcab lesson', 'Tinit':'Drawkcab lessons / award',
 'Justine':'Castleview pass seller (1000 gold)', 'Dreyfus':'Western Tower access quest / displaced priest',
 'Linus':'Ruby crafting (5 stones + 100 gems)', 'Simon':'Emerald crafting (5 stones + 200 gems)',
 'Toby':'Sapphire crafting (5 stones + 400 gems)', 'Hector':'Diamond crafting (5 stones + 1000 gems)',
 'Brother':'Drawkcab final challenge', 'Falista':'conditional rescued unicorn / magic restoration',
 'Luna':'three-statuette quest / animal healer', 'Yog':'conditional tribal negotiation / food reward',
 'Vespar':'staff-handle quest / Sandcaster pass', 'Kramer':'Ogre Pass caravan quest',
 'Nibbler':'Monga Melons / Bark key quest',
}

COUNTRY = [
('dreyfus','Dreyfus’s refuge',3,8,10,'shrine','plain','Temporary shelter below the usurped tower, not a new permanent grand temple.'),
('ruby','Linus’s ruby workshop',3,12,14,'workshop','working','Separate gemsmith workshop on the northern mine fringe; share a materials yard, not crafting costs.'),
('emerald','Simon’s emerald workshop',3,13,12,'workshop','working','Second workshop in the staggered gemsmith cluster.'),
('sapphire','Toby’s sapphire workshop',3,15,11,'workshop','working','Third workshop; retain individual recipes.'),
('diamond','Hector’s diamond workshop',7,1,12,'workshop','maintained','Separate fourth workshop east of the cluster; expensive recipes do not prove personal wealth.'),
('reger','Brother Reger’s hermitage',4,1,4,'hut','plain','Remote destination after the four urban lessons; deliberately off-road.'),
('falista','Falista’s sanctuary',4,7,1,'grove','natural','Creature sanctuary; no human residence fabricated. Initially empty until the rescue state.'),
('luna','Luna’s animal sanctuary',4,13,15,'hut','plain','Hut, animal-care clearing and three-place altar. Relocated north of the expanded town.'),
('justine','Justine’s gate-side shelter',4,15,12,'stall','makeshift','Outside the pass checkpoint; reachable before owning the pass.'),
('yog','Yog’s Sardaj camp',7,6,12,'camp','makeshift','Negotiable faction site; retain rejection/hostility/reconciliation conditions.'),
('vespar','Vespar’s retreat',7,7,1,'hut','maintained','Small secluded wizard dwelling near the eastern approach, no default spell-shop service.'),
('kramer','Kramer’s caravan yard',7,11,4,'caravan','working','Wagons, repair space and open loading yard on the trade road; not a new scheduled transport service.'),
('nibbler','Nibbler’s clearing',8,3,12,'grove','natural','Monkeydog shelter and later melon patch; initially no melon crop that bypasses his quest.'),
('kalindra','Castle Kalindra',4,5,14,'castle','royal','Restoration-dependent facade and BLV entrance. Named court occupants remain inside their original castle maps.'),
('western','Great Western Tower',3,4,9,'tower','fortified','Separate ground entrance and Skyroad roof arrival. Preserve Dreyfus’s roof-first access problem.'),
('mine','Gemstone Mine entrance',7,10,9,'cave','natural','Retain arrival into map39 pocket at25,0; no road spur automatically attached.'),
('troll_a','Troll Hole west',8,8,12,'hole','natural','Map40 arrival3,3; fall and voluntary descent are alternative triggers for the same pocket.'),
('troll_b','Troll Hole east',8,12,13,'hole','natural','Map40 arrival9,3; separate pocket; do not join tunnels without checking original connectivity.'),
('troll_c','Troll Hole south',8,11,6,'hole','natural','Map40 arrival15,3; off-road descent.'),
('sewer_out','Riverside sewer outfall',4,14,8,'drain','working','Outdoor entry into map30 at17,0; preserve alternative access to the town sewer system.'),
('skyrope','Dark Grove Skyroad rope',3,14,7,'rope','arcane','Climb transition to map91 at13,8; no full road, leave a clear landing and return pad.'),
]


def build():
    inventory = read(ROOT/'level_generation/projects/mm5_world_feasibility/inventory.json')
    scope = [3,4,7,8,29]
    sites = [dict(s) for s in inventory['sites'] if s['map'] in scope and s['spatial']]
    all_events, texts, sources = {}, {}, []
    for n in scope:
        for kind, file in [('events',f'events/dark_initial_state/maze{n:04}.evt.json'),
                           ('text',f'text/dark/aaze{n:04}.txt.json')]:
            p=SOURCE/file; sources.append(p)
            (all_events if kind=='events' else texts)[n]=read(p)
    owners, buildings = {}, []
    for i, (bid,title,x,y,w,d,form,quality,facing,coords,purpose) in enumerate(BUILDINGS,1):
        center=town_xy(x,y)
        facing={'N':'S','S':'N','E':'W','W':'E'}[facing]
        normal={'N':(0,1),'S':(0,-1),'E':(1,0),'W':(-1,0)}[facing]
        door=[center[0]+normal[0]*w/2,center[1]+normal[1]*d/2]
        b={'id':bid,'semanticId':f'mm5:castleview/{bid}','label':f'T{i:02}', 'title':title,
           'center':center,'envelope':[w,d],'form':form,'quality':quality,'qualityEvidence':'design inference from function',
           'door':door,'doorFacing':facing,'doorSize':[128,256],'sources':[[29,*c] for c in coords],
           'purpose':purpose,'district':'Castleview','npcIds':[], 'serviceIds':[]}
        buildings.append(b)
        for c in coords: owners[(29,*c)]=bid
    for i,(bid,title,n,x,y,form,quality,purpose) in enumerate(COUNTRY,1):
        center=source_xy(n,x,y)
        if bid=='luna':center=[-6400,8704]
        if bid=='justine':center=[-768,-7300]
        if bid=='sewer_out':center=[-768,-10240]
        b={'id':bid,'semanticId':f'mm5:sw/{bid}','label':f'R{i:02}','title':title,'center':center,
           'envelope': [4096,3072] if form=='castle' else [1536,1536] if form=='tower' else [832,640],
           'form':form,'quality':quality,'qualityEvidence':'design inference from function',
           'sources':[[n,x,y]],'purpose':purpose,'district':'Countryside','npcIds':[],'serviceIds':[]}
        buildings.append(b); owners[n,x,y]=bid
    by_id={b['id']:b for b in buildings}
    # Public contacts have a place without acquiring a fictitious private house.
    outdoor_contacts={(29,4,28):('guild','Nool speaks at the guild forecourt; no dedicated house.'),
                      (29,16,2):('temple','Ben occupies a bench at the temple approach; no private house implied.')}
    for key,(bid,_) in outdoor_contacts.items():owners[key]=bid
    census=[]
    for s in sites:
        n,x,y=s['map'],s['x'],s['y']; key=(n,x,y)
        records=[e for e in all_events[n] if (e['x'],e['y'])==(x,y)]
        s['id']=f'mm5:source/{n}/{x}/{y}'
        s['records']=records
        s['dialogue']=[{'index':i,'text':clean(texts[n][i])} for i in s['dialogueTextIndices']]
        if s['npcTitles'] or s['services']:
            assert key in owners, key
            b=by_id[owners[key]]
            for title in s['npcTitles'] or s['services']:
                rid=f'mm5:source/{n}/{x}/{y}/'+('npc' if s['npcTitles'] else 'service')
                role=next((v for k,v in ROLE_OVERRIDES.items() if title.startswith(k)),
                          'original '+title+' service' if s['services'] else 'resident / information contact')
                venue=owners[key]
                if title.startswith('Rex'): venue+=':accounts'
                elif title.startswith('Majot'):venue+=':editorial'
                elif venue=='maps':venue+=':'+title.split()[0].lower()
                elif venue=='crafts':venue+=':'+title.split()[0].lower()
                elif title.startswith('Ordana'):venue+=':swimming'
                residency=outdoor_contacts.get(key,('', 'House/venue assignment is an adaptation, not a source family relationship.'))[1]
                c={'id':rid,'name':title,'source':[n,x,y],'role':role,'building':b['id'],
                   'venue':venue,'placement':'public exterior contact' if key in outdoor_contacts else
                   'restricted interior' if b['id'] in ['jail','king'] else 'house/service dialogue',
                   'quality':b['quality'],'assignmentReason':b['purpose'],'residencyEvidence':residency,
                   'dialogue':s['dialogue'],'sourceEventOffsets':[e['offset'] for e in records],
                   'portraitSourceIds':sorted({e['parameters'][2] for e in records if e['opcode']==5 and len(e['parameters'])>2}),
                   'runtimeId':None}
                census.append(c);b['npcIds' if s['npcTitles'] else 'serviceIds'].append(rid)
        # Every event coordinate is retained; unclassified mechanical triggers are not invented as houses.
        if key in owners:
            owner=owners[key];point=by_id[owner]['center']; disposition='assigned semantic destination'
        elif n==29:
            owner='town_source_mechanics'; point=town_xy(x/31*11000,y/31*11000)
            disposition='source overlay only: secondary trigger; resolve its owner below before native export'
        else:
            owner='countryside_source';point=source_xy(n,x,y);disposition='source-position landscape interaction'
        if n==29:
            if any(e['opcode']==32 and len(e['parameters'])>1 and 16<=e['parameters'][1]<=34 for e in records):
                owner='puzzle';point=by_id[owner]['center'];disposition='18 puzzle chest cells retained in two ordered bays'
            elif any(e['opcode']==17 and e['parameters']==[12] for e in records):
                owner='cross_world'; disposition='preserved landmark, inactive MM4 transition in this MM5-only scope'
            elif any(e['opcode']==24 and e['parameters'][:2]==[40,40] for e in records):
                owner='sewer_network';disposition='sewer access; preserve source arrival and return pair'
        s.update(owner=owner,plannedPoint=point,disposition=disposition)
    # Original monster placements stay separate from designed encounter volumes and deferred spawn reserves.
    binary=SOURCE/'raw/dark/dark.mon'; sources.append(binary); raw=binary.read_bytes(); assert len(raw)%60==0
    names=[raw[i:i+16].split(b'\0')[0].decode('cp437') for i in range(0,len(raw),60)]
    placements=[]
    for n in scope:
        p=SOURCE/f'maps/dark_initial_state/maze{n:04}.mob.json';sources.append(p); mob=read(p)
        section=0
        for i,r in enumerate(mob['records']):
            if r['terminator']:
                section+=1;continue
            if section!=1:continue
            index=r['spriteTableIndex']; monster=mob['spriteTables']['monsters'][index]
            active=0<=r['x']<(32 if n==29 else 16) and 0<=r['y']<(32 if n==29 else 16)
            placements.append({'id':f'mm5:source/{n}/monster/{i}','map':n,'sourceXY':[r['x'],r['y']],
               'monster':monster,'name':names[monster],'initiallySpatial':active,'sourceOffset':r['offset'],
               'point':town_xy(r['x']/31*11000,r['y']/31*11000) if n==29 else source_xy(n,r['x'],r['y']),
               'disposition':'source encounter reference; aggregate into authored encounters' if active else
               'off-map reserve; never scatter automatically'})
    roads=[
      {'id':'trade_road','width':768,'purpose':'Western Tower / Kalindra / Castleview / eastern regional trade spine',
       'points':[[-17664,14592],[-12544,14592],[-9216,13056],[-9216,7168],[-11008,3072],[-11776,-2304],[-9984,-6144],[-5632,-7680],[-2304,-7680],[7168,-6144],[7168,768],[13056,768],[13056,5376],[24576,5376],[32256,5376]]},
      {'id':'castle_approach','width':768,'purpose':'Castle restoration and court traffic','points':[[-11776,-2304],[-14080,-2304],[-16128,-2304]]},
      {'id':'gate_approach','width':768,'purpose':'Public pass checkpoint; default arrival outside town','points':[[-2304,-7680],town_xy(5000,12000)]},
    ]
    town_roads=[('main_street',512,[(5000,12000),(5000,9500),(5500,8700),(5750,7500),(5800,6300),(5850,4550),(5900,3000),(5800,2000)]),
      ('west_loop',384,[(5000,9500),(2800,9500),(2450,8700),(1750,8200),(1750,6500),(3900,6500),(4150,6850),(5800,7100)]),
      ('human_quarter',384,[(5000,9500),(5800,9800),(7650,9850),(8000,9700),(8000,8400),(9150,8200),(9150,7250),(8850,5200),(7700,4700),(5850,4550)]),
      ('temple_lane',384,[(5900,3000),(6400,2350),(8600,2350),(9200,2350),(9200,3350),(8850,5200)]),
      ('store_lane',384,[(3900,6500),(4000,5800),(4000,4850),(4650,4550),(4650,2200),(5800,2000)]),
      ('store_court',384,[(4650,2200),(3100,2200)]),
      ('keeper_lane',384,[(1750,6500),(1788,5750),(1550,5000),(1250,4000)]),
      ('hiring_court',384,[(7650,9850),(8000,10050),(10300,10050)])]
    for rid,width,pts in town_roads:roads.append({'id':rid,'width':width,'purpose':'Shared urban frontage and circulation','points':[town_xy(*p) for p in pts]})
    # A second public gate links the human quarter to the Kalindra-side trade road.
    # At Y=692, these intersections lie exactly on the existing sloping wall and road segments.
    west_gate=[2696-(11200+(5200-1200)*300/6700),692]
    roads.append({'id':'west_gate_lane','width':384,
        'purpose':'Second pass-controlled entrance: human quarter to the Kalindra-side trade road',
        'points':[town_xy(8850,5200),west_gate,[-11008+(692-3072)*(-768)/(-5376),692]]})
    # Explicit frontage connectors are short pedestrian approaches, not a road spur to every countryside POI.
    def nearest(point,poly):
        best=None
        for a,b in zip(poly,poly[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
            t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/den)) if den else 0
            q=[a[0]+t*dx,a[1]+t*dy];d=math.dist(point,q)
            if best is None or d<best[0]:best=(d,q)
        return best
    for b in buildings:
        if b['district']!='Castleview':continue
        d,r,q=min((nearest(b['door'],r['points'])[0],r['id'],nearest(b['door'],r['points'])[1]) for r in roads[3:])
        b['frontage']={'road':r,'doorToCenterline':round(d),'points':[b['door'],q],
                       'purpose':'Short threshold / shared court access','width':192}
    plan={'version':1,'status':'Reviewable layout proposal; no native geometry, live tables or gameplay scripts generated',
      'world':'mm5','region':'sw','sourceMaps':scope,'nativeUnits':True,'travelBounds':[-24576,24576,-24576,24576],
      'terrainGrid':[128,128,512],'townTransform':'[2696-localX,5892-localY], a 180-degree rotation; local plan is not a runtime coordinate system',
      'buildings':buildings,'census':census,'roads':roads,
      'defaultArrival':{'point':[-2304,-7040],'facing':'north','purpose':'Outside south pass gate, facing Castleview'},
      'travel':[{'id':'sw_sc','point':[24576,5376],'arrival':[23040,5376],'kind':'road','days':None},
                {'id':'sw_nw','point':[-11520,24576],'arrival':[-11520,23040],'kind':'off-road','days':None}],
      'sourceSites':sites,'sourceMonsters':placements}
    write('layout.json',plan)
    write('source_provenance.json',{'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],
      'formatReferences':['https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/map.cpp',
                          'https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/scripts.cpp'],
      'note':'60-byte dark.mon record size and event modes inspected in the behavior references; code is original.'})
    with (OUT/'residents.csv').open('w',newline='') as f:
        fields=['id','name','source','role','building','venue','placement','quality','assignmentReason']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:c[k] for k in fields} for c in census)
    print('Census',len(census),'NPC',sum(bool(s['npcTitles']) for s in sites),'services',sum(bool(s['services']) for s in sites))
    print('Monsters',Counter((p['map'],p['name'],p['initiallySpatial']) for p in placements))

if __name__=='__main__':build()
