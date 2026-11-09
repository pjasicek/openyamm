"""Resolve landscape interactions, quest spaces and decoration groups for the layout proposal."""
from collections import Counter
import json
import hashlib
from pathlib import Path
from build_plan import ROOT, OUT, SOURCE, town_xy, source_xy, read, write
from analyze import clean


def build():
    p=read(OUT/'layout.json');bs={b['id']:b for b in p['buildings']}; features=[]
    def feature(fid,title,kind,point,purpose,sources=(),**extra):
        f=dict(id=fid,title=title,kind=kind,point=point,purpose=purpose,sources=list(sources),**extra)
        features.append(f);return f
    feature('pass_gate','Castleview south gate','gate',town_xy(5000,12000),
       'Main public entrance checks Castleview pass; Justine remains outside. Sewer provides the original alternative.',[[4,14,10],[29,15,31]])
    west_lane=next(r for r in p['roads'] if r['id']=='west_gate_lane')
    feature('west_gate','Castleview west gate toward Kalindra','gate',west_lane['points'][1],
       'New accessibility entrance between Nadia and Zelda, connecting the human quarter to the Kalindra-side road. Checks the same Castleview pass as the south gate; no additional pass item, fee or NPC. Justine remains outside the south gate.',
       [],evidence='new layout adaptation requested by user',accessRule='same Castleview pass condition as pass_gate',
       linkedRoad='west_gate_lane',opening=[512,768])
    feature('cross_world','Cross-world pyramid reserve','landmark',town_xy(11000,9900),
       'Preserve the recognizable original link as a closed monument for this MM5-only slice. No MM4 travel yet.',[[29,26,24]],extent=[512,512])
    feature('training_pool','Ordana’s practice pool','water',town_xy(2750,4736),
       'Small designed teaching basin, not an invented natural lake or a prerequisite that requires Swimming to reach the teacher.',
       [[29,7,19]],extent=[896,512],evidence='new functional addition')
    feature('water_well','Working well','prop',town_xy(6900,6550),
       'Domestic water for the bank/boarding quarter; proposed scenery, no new unlimited healing.',extent=[256,256],evidence='new functional addition')
    feature('meditation','Drawkcab meditation court','garden',town_xy(4600,6900),
       'Asymmetric dry garden between two shared chapterhouses. Four lesson stations remain distinct.',extent=[1152,700])
    feature('bench','Ben and Lyle’s benches','prop',town_xy(4800,1300),
       'Ben remains a public contact. Preserve the bench dedicated to Lyle as an inscription, not an invented additional NPC.',[[29,16,2]],extent=[640,256])
    feature('guild_court','Nool’s guild forecourt','prop',town_xy(2050,10300),
       'Public speech position and guild notice board; clear the approaching guild door.',[[29,4,28]])
    # Explicit source-to-destination bindings for every sewer entry and five ordinary town chests.
    sewer_positions={(2,29):(2250,10350),(12,30):(4200,10750),(1,13):(1150,5050),
                     (26,1):(9300,950),(30,18):(10900,5150)}
    chest_positions={(10,30):(3650,10500),(18,30):(7400,11000),(10,29):(3500,9950),
                     (11,29):(3900,9900),(20,11):(7750,4100)}
    sign_owners={'Jail':'jail',"Ol' Black Magic":'guild','Ogre Foundry':'forge',"Tog's Training":'training',
                 'Temple of Mok':'temple','Milken Savings':'bank','Blacksmoke Tavern':'tavern',"Lydia's Maps":'maps',
                 'Public Storage':'puzzle','Treasure room':'puzzle'}
    for s in p['sourceSites']:
        n,x,y=s['map'],s['x'],s['y'];src=[n,x,y];records=s['records'];key=(x,y)
        fid=f'source_{n}_{x}_{y}'
        if n==29:
            if key==(15,31):s.update(owner='pass_gate',plannedPoint=town_xy(5000,12000))
            if key in sewer_positions:
                f=feature(fid,'Sewer access '+str(key),'entrance',town_xy(*sewer_positions[key]),
                    'Retain this distinct sewer arrival and reciprocal route; it is not interchangeable with the outfall.',[src],transfers=s['transfers'])
                s.update(owner=fid,plannedPoint=f['point'],disposition='assigned sewer connector')
            elif key in chest_positions:
                f=feature(fid,'Town chest '+str(key),'chest',town_xy(*chest_positions[key]),
                    'One original ordinary chest, once-only loot. Source give-event bytes retained; rebalance rewards later.',[src],loot='source GiveMulti records; no invented contents')
                s.update(owner=fid,plannedPoint=f['point'],disposition='assigned ordinary chest')
            elif s['owner']=='puzzle' and y in [1,2,3] and (5<=x<=7 or 9<=x<=11):
                # Ordered topology is retained: two 3x3 arrays, not shuffled chests scattered through town.
                bay=0 if x>=9 else 1; col=x-(9 if bay==0 else 5);row=y-1
                q=town_xy(1000+bay*1000+col*256,1250+row*320)
                f=feature(fid,'Numbered puzzle chest' if bay==0 else 'Lettered puzzle chest','puzzle_chest',q,
                   'Preserve source index, initial open/closed state and linked toggle graph. Bay is inside the storehouse.',[src],owner='puzzle')
                s['plannedPoint']=q
            elif any(t in sign_owners for t in s['labels']):
                owner=next(sign_owners[t] for t in s['labels'] if t in sign_owners)
                s.update(owner=owner,plannedPoint=bs[owner]['center'],disposition='service/district sign; no extra building')
            elif s['owner']=='town_source_mechanics':
                calls=[e['parameters'][0] for e in records if e['opcode']==25 and e['parameters']]
                if calls:
                    helper=calls[0]
                    kind={50:'bed',55:'tree',56:'reward_tree',57:'reward_tree',58:'food_tree'}[helper]
                    disposition={50:'Bed/empty interior furnishing; retain in corresponding adapted residential precinct',
                        55:'Non-reward tree; distribute inside planned gardens with source identity retained',
                        56:'Reward-bearing tree; preserve distinct source give modes',57:'Reward-bearing tree; preserve distinct source give modes',
                        58:'Food tree; once/stateful source interaction, not generic foliage'}[helper]
                    s.update(owner='town_furnishings',disposition=disposition)
                    feature(fid,kind.replace('_',' ').title(),kind,s['plannedPoint'],disposition,[src],positionStatus='precinct allocation; final individual scatter deferred')
                elif any(e['opcode']==32 and e['parameters'][:2]==[0,1] for e in records):
                    s.update(owner='town_furnishings',disposition='Searchable bed with source reward; distinct from an empty bed')
                    feature(fid,'Searchable bed','bed',s['plannedPoint'],s['disposition'],[src],positionStatus='interior furnishing; no outdoor prop')
                else:
                    # The separate moving treasure in the SW source puzzle precinct.
                    assert x<=3 and y<=3, (x,y)
                    s.update(owner='puzzle',plannedPoint=bs['puzzle']['center'],disposition='Moving treasure challenge and its triggers; preserve cycle in a separate storehouse bay')
            if key==(15,31):s.update(owner='pass_gate',plannedPoint=town_xy(5000,12000))
            continue
        if (n,x,y)==(4,14,10):
            s.update(owner='pass_gate',plannedPoint=town_xy(5000,12000),disposition='expanded town gate; original exterior symbol replaced')
            continue
        if s['owner']!='countryside_source':continue
        point=s['plannedPoint']
        if any(e['opcode']==25 and e['parameters'][:2]==[60,60] for e in records):
            s.update(owner='acid_pond',disposition='Acid Pond hazard area; preserve shore and No Swimming warning')
        elif (n,x,y) in [(4,3,1),(4,8,4),(4,14,3),(8,1,4)]:
            s.update(owner=fid,disposition='Original Monga Melon quest pickup; no chest added')
            feature(fid,'Monga Melon patch','quest_item',point,'Original quest-food pickup, exposed to Electrapedes; no road spur.',[src])
        else:
            txt=' '.join(s['labels']);kind='interaction'
            if 'water is cool' in txt or 'Luck' in txt:kind='spring'
            elif 'ship' in txt:kind='wreck'
            elif 'note' in txt.lower() or 'captiv' in txt.lower():kind='clue'
            elif 'camp' in txt.lower():kind='camp'
            elif 'pray' in txt.lower():kind='shrine'
            elif 'Swimming' in txt:kind='warning'
            elif 'Beware' in txt or 'Tower' in txt:kind='sign'
            feature(fid,(s['labels'][0][:65] if s['labels'] else 'Source interaction'),kind,point,
                    txt or 'Original event interaction; full records retained.',[src])
            s['owner']=fid
    feature('moving_treasure','Elusive treasure bay','challenge',town_xy(1150,2350),
       'Third storehouse bay: retain the source moving-treasure cycle at cells 1..3,1..3 and its central reward trigger. This is separate from both nine-chest toggle puzzles.',[[29,2,2]],extent=[640,512])
    feature('acid_pond','Acid Pond','hazard',source_xy(7,0,14),
       'Original northern pond crosses A3/B3; keep harmful water separate from useful springs and Ordana’s pool.',
       [[3,14,14],[7,1,14]],extent=[6000,6500],evidence='original water and event footprint; extent is a planning envelope')
    feature('edge','World edge','boundary',[-22600,-22600],
       'The source black rim is the edge of Xeen, not a sea. Leave terrain/cliff apron; no invented coastal port.')
    feature('ramp_kalindra','Kalindra restoration forecourt','arrival',[-13696,-2304],
       'Reserve approach, return anchor and clear view of the phased castle. NPC court and throne rooms remain in the castle BLV.')
    feature('river_crossing','South meadow river crossing','bridge',[-17664,-13824],
       'Proposed narrow footbridge on an existing watercourse: allows MM6–8 parties to reach Reger and the southern melon patches. No road across the meadow.',
       [],extent=[512,4096],evidence='adaptation: current MM6–8 Swimming equivalence is unresolved; check exact bank geometry before native build')
    feature('town_wall','Irregular town enclosure','wall',town_xy(5400,6400),
       'South and west public gates share the Castleview-pass condition; sewer entrances remain distinct. Covered jail and Gremlin court prevent Fly from bypassing quest access.',
       polygon=[town_xy(*q) for q in [(0,700),(2800,0),(7200,0),(11200,1200),(11500,7900),(11200,11650),(6300,11800),(5000,12000),(3750,11000),(300,10500),(-200,8200)]] )
    # Authored encounter spaces: count/strength proposals, not a claim that original grid density translates directly.
    encounters=[
     ('north_barbarians','Northern patrol',[-12544,22272],[4608,1536],'Barbarian',3,'Patrol',[[3,5,15],[3,8,15],[3,9,15]],'Beyond the gemsmiths; leave a 1536-wide travel escape lane.'),
     ('grove_spiders','Dark Grove nests',[-512,12032],[3840,4096],'Arachnoid',4,'Hostile',[[3,12,7],[3,13,9],[3,15,7]],'Off the main road, screen nests with broken groves; separate rope landing by at least 1536.'),
     ('yog_guard','Sardaj audience perimeter',source_xy(7,6,12),[3072,3072],'Barbarian',4,'Conditional',[[7,6,12]],'Do not attack by default merely because creature class is Barbarian. Dialogue decides hostility.'),
     ('barbarian_camp','Burnable Barbarian camp',source_xy(7,13,10),[2560,2048],'Barbarian',4,'Hostile/stateful',[[7,13,10]],'Keep separate from Yog’s audience and Kramer; source destroy-camp state owns the reward.'),
     ('south_melons','Southern meadow Electrapedes',[-7936,-20736],[8192,4096],'Electrapede',5,'Hostile',[[4,3,1],[4,8,4],[4,14,3]],'Guards original quest-food territory; scattered grass and low rocks preserve sight lines.'),
     ('east_melons','Eastern melon Electrapedes',source_xy(8,1,4),[2048,2560],'Electrapede',2,'Hostile',[[8,1,4]],'Alternate original melon patch with a different approach; no dedicated loot road.'),
     ('troll_wood','Troll-hole woodland',source_xy(8,11,10),[6144,5120],'Medusa Sprite',5,'Hostile',[[8,11,10],[8,13,12]],'Three holes remain findable among forest clearings; avoid spawning on descent/return pads.'),
     ('town_west','Jail quarter skirmish',town_xy(850,8050),[700,800],'Goblin',3,'Hostile/quest',[[29,1,20]],'Contained side court before sewer/jail access; does not aggro through the guild service door.'),
     ('town_north','Storehouse approach skirmish',town_xy(850,3650),[1000,900],'Gremlin',3,'Hostile/quest',[[29,8,5]],'Town danger is retained near the puzzle precinct; leave service spine clear.'),
     ('royal_guards','Gremlin court guards',bs['king']['center'],[1000,1000],'Gremlin Guard',6,'Scripted interior',[[29,29,13]],'Two proposed waves of three inside the covered BLV annex; never pre-spawn off-map source reserves outdoors.'),
    ]
    p['encounters']=[dict(id=i,title=t,center=c,extent=e,sourceSpecies=s,proposedCount=n,hostility=h,sources=src,purpose=why,
       evidence='designed aggregate; original MOB population retained separately',minimumArrivalClearance=1536,
       refill='quest-owned groups remain defeated; wilderness refill policy deferred with regional balance')
       for i,t,c,e,s,n,h,src,why in encounters]
    groups=[
     ('town_gardens','Door-side gardens',town_xy(7700,6600),[2200,1300],['plant17','plant19','plant27'],24,'Herb/boarding court ground cover'),
     ('chapter_garden','Monks’ garden',town_xy(4750,6650),[900,650],['plant17','plant23'],12,'Low plants keep all four lesson stations visible'),
     ('herb_beds','Zelda’s herb beds',town_xy(10700,6100),[600,850],['plant19','plant27','plant32'],18,'Named working garden, no random healing effect'),
     ('temple_trees','Temple and bench trees',town_xy(3900,800),[1700,650],['tree10','tree11'],5,'Unequal canopy groups frame temple without covering doors'),
     ('town_edge','Town edge trees',[-8192,2560],[1280,6144],['tree10','tree12','tree13'],14,'Broken windbreak; leave jail and guild approaches open'),
     ('dark_grove','Dark Grove',[-4096,12032],[6656,8192],['tree11','tree12','tree13'],55,'Clustered cool canopy with rope clearing; no uniform ring'),
     ('south_wood','Troll-hole woodland',[17408,-16128],[12288,13312],['tree10','tree11','tree12','tree13'],100,'Dense irregular southern forest, explicit holes and return-pad exclusions'),
     ('north_scrub','Northern dry shelf',[14592,17920],[12800,7680],['rock01','rock02','rock05','rock20'],32,'Ravage Roaming rock/dirt treatment; no forest carpet'),
     ('meadow_plants','Southern meadow',[-9216,-20480],[17408,5120],['plant17','plant21','plant26'],45,'Low cover around melons and Electrapedes; keep broad quiet gaps'),
     ('river_banks','Riverbank accents',[0,-11008],[18432,2560],['rock01','rock05','plant27'],35,'Discontinuous bank accents; original river remains legible'),
     ('luna_garden','Luna’s sanctuary',bs['luna']['center'],[2304,1792],['tree10','plant19','plant32'],16,'Three altar sockets, animal-care clearing and shelter, no random loot chest'),
    ]
    p['foliageGroups']=[dict(id=i,title=t,center=c,extent=e,palette=a,targetCount=n,purpose=why,
       exclusion={'buildingEnvelope':320,'roadEdge':320,'doorCorridor':512,'arrival':1536,'water':True},
       scatter='bounded groups; validate sprite crowns and reject invalid points; never silently lower clearances') for i,t,c,e,a,n,why in groups]
    p['features']=features
    # Record intended physical form, material role and functional props by construction class.
    for b in p['buildings']:
        if b['district']!='Castleview':continue
        members=[c for c in p['census'] if c['building']==b['id'] and c['placement']!='public exterior contact']
        venues=sorted({c['venue'] for c in members}) or [b['id']]
        normal={'N':(0,1),'S':(0,-1),'E':(1,0),'W':(-1,0)}[b['doorFacing']]
        tangent=(-normal[1],normal[0]); b['venues']=[]
        for i,venue in enumerate(venues):
            offset=(i-(len(venues)-1)/2)*320
            point=[b['door'][0]+tangent[0]*offset,b['door'][1]+tangent[1]*offset]
            b['venues'].append(dict(id='mm5:castleview/venue/'+venue,
                occupants=[c['id'] for c in members if c['venue']==venue],door=point,facing=b['doorFacing'],
                doorSize=[128,256],kind='BLV entrance' if b['id'] in ['jail','king','tower'] else 'house dialogue/service destination'))
        b['padHeightProposal']=1152 if b['id'] in ['temple','tower'] else 640
        b['terrainIntent']='Local level foundation pad; street shelves 576..768; temple/tower approaches grade to1152, no vertical heightfield step.'
        b['props']=dict(guild=['membership desk','notice board'],forge=['ore bins','anvil','working yard'],
            training=['practice targets','pool access'],jail=['barred cells','bed'],monks_n=['two study stations','books'],
            monks_s=['two study stations','meditation garden'],bank=['ledger desk','accounting desk'],
            tavern=['common-room tables','two contact seats'],lodging=['two rented rooms'],maps=['three desk/door signs','map racks'],
            mayor=['public notices','editorial desk'],workyard=['hiring board','cart repair materials'],joe=['map display','out-to-lunch sign'],
            ranger=['woodcraft tools','small practice garden'],herbalist=['drying racks','herb beds'],nadia=['crowded personal storage'],
            diviners=['orb discussion table','two distinct speakers'],king=['throne','guard staging','three-disk reward owner'],
            tower=['keyed threshold','boots clue presentation'],temple=['healing service threshold','Imble contact'],
            crafts=['cobbler tools','tailor stock'],workers=['shared beds','sweep tools'],keeper=['kennel','work bench'],
            puzzle=['two nine-chest bays','moving-treasure bay','Dyson desk'])[b['id']]
    # Keep the source reward/food grove as a public orchard, rather than assigning dozens of trees to a cottage.
    orchard=feature('public_orchard','Public orchard terrace','garden',town_xy(5300,-900),
        'Original 30 ordinary, 13 reward-bearing and 12 food-tree sites are retained together in a public planted terrace. Each reward node keeps its own event identity; no additional generic reward trees.',
        [],extent=[10240,1792],evidence='adapted precinct for original tree interactions')
    p['foliageGroups'].append(dict(id='public_orchard',title='Public orchard terrace',center=orchard['point'],
        extent=orchard['extent'],palette=['tree10','tree11','tree12'],targetCount=55,
        purpose='Includes all 55 source tree interactions; do not add those again as a second scatter pass.',
        sourceComposition=dict(ordinary=30,reward=13,food=12),
        exclusion=dict(buildingEnvelope=320,roadEdge=320,doorCorridor=512,arrival=1536,water=True),
        scatter='Unequal orchard groups and walking gaps; individual accepted/rejected positions checked during native authoring'))
    wall=next(f for f in features if f['id']=='town_wall')
    wall['polygon']=[town_xy(*q) for q in [(0,700),(-200,-1700),(3600,-2000),(10900,-1700),(11200,1200),(11500,7900),(11200,11650),(6300,11800),(5000,12000),(3750,11000),(300,10500),(-200,8200)]]
    feature('orchard_walk','Orchard pedestrian access','path',town_xy(4100,300),
        'Walk around the temple flank to the public orchard; compacted pedestrian ground, not another cart road.',
        [],points=[town_xy(*q) for q in [(4300,2200),(4100,500),(4000,-900)]])
    bed_owners={(1,15):'jail',(1,16):'jail',(1,18):'jail',(1,22):'jail',
                (22,18):'lodging',(22,20):'lodging',(22,22):'lodging',
                (24,30):'mayor',(27,30):'workyard',(30,24):'maps',(30,21):'maps'}
    furnishing_counts={}
    for site in p['sourceSites']:
        if site['owner']!='town_furnishings':continue
        f=next(f for f in features if f['id']==f"source_{site['map']}_{site['x']}_{site['y']}")
        if f['kind']=='bed':
            owner=bed_owners[site['x'],site['y']];point=bs[owner]['center']
            rule='Interior bed in the corresponding prison, boarding, civic/caretaker or mapmaking premises; retain searchable/empty distinction.'
        else:
            owner='public_orchard';point=orchard['point'];rule='Public orchard node; retain its own source effect and saved state, separate from ordinary foliage.'
        f.update(owner=owner,point=point,placementRule=rule,
                 positionStatus='Assigned premises/precinct; individual room or orchard positions deferred')
        site.update(owner=owner,plannedPoint=point)
        furnishing_counts[owner]=furnishing_counts.get(owner,0)+1
    p['townFurnishingOwnership']=furnishing_counts
    p['construction']={
      'plain':{'walls':'Garrote modest masonry family','roof':'shared muted shingle family','props':['bench','small woodpile','garden tools']},
      'working':{'walls':'Garrote workshop/service proportions','roof':'same town roof family','props':['crates at loading side','workbench','trade-specific sign']},
      'worn':{'walls':'weathered version of the modest family','roof':'patched, intact silhouette','props':['reused storage','uneven fence']},
      'maintained':{'walls':'maintained masonry over dressed stone base','roof':'well-kept shared roof family','props':['clear sign','organized stock']},
      'civic':{'walls':'Garrote dressed masonry with original massing','roof':'small projecting wings / varied heights','props':['notice board','forecourt seats']},
      'fortified':{'walls':'stone compound / tower family','roof':'covered quest chambers','props':['guard position','barred opening']},
      'arcane':{'walls':'distinct stone tower or sanctuary silhouette','roof':'small tower roof / cap','props':['quest emblem','controlled entrance']},
      'royal':{'walls':'original castle assembly using MM6–8 material families','roof':'keep and subordinate wings','props':['phase-restoration presentation']},
      'makeshift':{'walls':'timber, canvas or a reused wagon','roof':'low canopy','props':['rolls','camp supplies']},
      'natural':{'walls':'terrain/BModel rock and foliage','roof':'none unless a shelter is specified','props':['rocks','species-appropriate resting place']},
    }
    # Attached interiors count as contacts inside those complexes, not extra town houses.
    inv=read(ROOT/'level_generation/projects/mm5_world_feasibility/inventory.json')
    interior_owners={30:'sewer_out',39:'mine',40:'troll_a',41:'kalindra',42:'kalindra',43:'kalindra',44:'kalindra',
                     53:'tower',54:'tower',55:'tower',56:'tower',57:'western',58:'western',59:'western',60:'western'}
    interior=[];extra_paths=set()
    for site in inv['sites']:
        n=site['map']
        if n not in interior_owners or not site['spatial'] or not(site['npcTitles'] or site['services']):continue
        tp=SOURCE/f'text/dark/aaze{n:04}.txt.json';ep=SOURCE/f'events/dark_initial_state/maze{n:04}.evt.json'
        extra_paths.update([tp,ep]);texts=read(tp)
        title=' / '.join(site['npcTitles'] or site['services'])
        role='retained interior contact / quest state'
        if site['services']:role='retained interior '+title+' service'
        elif title.startswith('Felix'):role='teacher: Direction Sense (1000 gold)'
        elif title.startswith('Errol'):role='teacher: Arms Master (free)'
        elif title.startswith('Gem the'):role='teacher: Danger Sense (free)'
        row=dict(id=f"mm5:source/{n}/{site['x']}/{site['y']}/interior",name=title,
                 source=[n,site['x'],site['y']],exteriorOwner=interior_owners[n],role=role,
                 dialogue=[dict(index=i,text=clean(texts[i])) for i in site['dialogueTextIndices']],
                 placement='Inside the retained BLV complex; no new outdoor house',services=site['services'])
        interior.append(row)
    p['attachedInteriorContacts']=interior
    for b in p['buildings']:b['interiorContacts']=[c for c in interior if c['exteriorOwner']==b['id']]
    write('interior_contacts.json',interior)
    provenance=read(OUT/'source_provenance.json')
    for n in [57,62]:extra_paths.add(SOURCE/f'text/dark/aaze{n:04}.txt.json')
    for path in sorted(extra_paths):
        provenance['sources'].append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    write('source_provenance.json',provenance)
    p['mirrorArrivals']=[]
    for entry in inv['mirrorDestinations']:
        if entry['destination'] not in [3,4,7,8]:continue
        point=source_xy(entry['destination'],entry['x'],entry['y'])
        if entry['word'].lower()=='castleview':point=p['defaultArrival']['point']
        p['mirrorArrivals'].append(dict(entry,plannedPoint=point,
            note='Named source teleport destination; does not imply a new physical mirror building. Apply the same arrival exclusions.'))
    # Visual MOB objects may exist without an EVT coordinate, including benches and already-open empty chests.
    objects=[]
    extra_benches={(14,3):'temple',(14,30):'pass_gate',(14,5):'workers',(16,4):'crafts',
                   (21,30):'mayor',(10,18):'training',(9,16):'keeper',(14,2):'temple',(20,28):'tavern'}
    open_chests={(29,6):'king',(18,6):'crafts',(9,20):'jail',(11,20):'jail',(10,25):'forge',(11,25):'forge'}
    for n in [3,4,7,8,29]:
        mob=read(SOURCE/f'maps/dark_initial_state/maze{n:04}.mob.json')
        for index,r in enumerate(mob['records']):
            if r['terminator']:break
            active=0<=r['x']<(32 if n==29 else 16) and 0<=r['y']<(32 if n==29 else 16)
            sprite=mob['spriteTables']['objects'][r['spriteTableIndex']]
            linked=next((s for s in p['sourceSites'] if (s['map'],s['x'],s['y'])==(n,r['x'],r['y'])),None)
            owner=linked['owner'] if linked else 'off-map reserve or neighboring preview' if not active else 'source landscape decoration'
            if n==29 and active and not linked:
                if sprite==4:owner=extra_benches[r['x'],r['y']]
                elif sprite==57:owner=open_chests[r['x'],r['y']]
                else:raise AssertionError(('Unassigned town visual object',r,sprite))
            obj=dict(id=f'mm5:source/{n}/object/{index}',source=[n,r['x'],r['y']],sprite=sprite,
                     initiallySpatial=active,owner=owner,sourceOffset=r['offset'],
                     meaning='already-open empty chest scenery; no second loot container' if n==29 and sprite==57 else
                             'bench (may also host an existing NPC)' if n==29 and sprite==4 else
                             'visual object of its linked source interaction' if linked else 'original non-event visual placement')
            objects.append(obj)
    p['sourceObjects']=objects
    write('source_objects.json',objects)
    write('layout.json',p)
    print('Feature ownership',Counter(s['owner'] for s in p['sourceSites']))

if __name__=='__main__':build()
