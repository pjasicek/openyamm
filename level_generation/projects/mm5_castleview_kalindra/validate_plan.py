"""Focused source-coverage and spatial checks for a planning artifact, not runtime tests."""
from collections import Counter,defaultdict
import json
import math
import sys
from pathlib import Path
from matplotlib.path import Path as PolygonPath
from build_plan import ROOT,OUT,SOURCE,read,write,source_xy
sys.path.insert(0,str(ROOT/'level_generation/scripts'))
from measure_settlement_density import gap,measure


def rect(b):
    x,y=b['center'];w,h=b['envelope']
    return [[x-w/2,y-h/2],[x+w/2,y-h/2],[x+w/2,y+h/2],[x-w/2,y+h/2]]


def strip(a,b,width):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);x,y=-dy/length*width/2,dx/length*width/2
    return [[a[0]+x,a[1]+y],[b[0]+x,b[1]+y],[b[0]-x,b[1]-y],[a[0]-x,a[1]-y]]


def build():
    p=read(OUT/'layout.json');town=[b for b in p['buildings'] if b['district']=='Castleview'];failures=[]
    ids=[c['id'] for c in p['census']];assert len(ids)==len(set(ids))==54
    source=[s for s in p['sourceSites'] if s['npcTitles'] or s['services']]
    assert len(source)==54
    assert {tuple(c['source']) for c in p['census']}=={(s['map'],s['x'],s['y']) for s in source}
    assert sum(f['kind']=='puzzle_chest' for f in p['features'])==18
    assert not any(s['owner'] in ['town_source_mechanics','countryside_source','town_furnishings'] for s in p['sourceSites'])
    for i,b in enumerate(town):
        for c in town[i+1:]:
            if gap(rect(b),rect(c))==0:failures.append(['building overlap',b['id'],c['id']])
        for road in p['roads']:
            for a,z in zip(road['points'],road['points'][1:]):
                if gap(rect(b),strip(a,z,road['width']))==0:
                    failures.append(['road/building overlap',b['id'],road['id']]);break
        f=b['frontage']
        # The pedestrian line must leave the selected face rather than crossing the building interior.
        nx,ny={'N':(0,1),'S':(0,-1),'E':(1,0),'W':(-1,0)}[b['doorFacing']]
        if (f['points'][1][0]-b['door'][0])*nx+(f['points'][1][1]-b['door'][1])*ny < -.01:
            failures.append(['frontage behind door',b['id']])
        for c in town:
            if b['id']!=c['id'] and gap(rect(c),strip(*f['points'],192))==0:
                failures.append(['frontage crosses another building',b['id'],c['id']])
    wall=next(f for f in p['features'] if f['id']=='town_wall')
    polygon=wall['polygon'];inside=PolygonPath(polygon)
    for b in town:
        if not all(inside.contains_points(rect(b))):failures.append(['building outside town wall',b['id']])
        for a,z in zip(polygon,polygon[1:]+polygon[:1]):
            if gap(rect(b),strip(a,z,wall['architecture']['thickness']))==0:
                failures.append(['curtain strip overlaps building',b['id']])
        if not b.get('architecture'):failures.append(['missing architectural mapping',b['id']])
    # Exact supplied source cells are used for geography checks; planned terrain ramps are not validated here.
    maps={n:read(SOURCE/f'maps/dark_initial_state/maze{n:04}.dat.json') for n in [3,4,7,8]}
    def terrain(point):
        x=int((point[0]+24576)//1536);y=int((point[1]+24576)//1536)
        if not(0<=x<32 and 0<=y<32):return 'outside'
        n=(7 if x>=16 else 3)+(0 if y>=16 else 1);d=maps[n];c=d['cells'][y%16][x%16]
        return d['surfaceTypes'][c['layers'][0]]&15
    for b in town:
        for point in rect(b)+[b['center']]:
            if terrain(point) in [0,8,15,'outside']:
                failures.append(['town envelope on source water/void',b['id'],point]);break
    for road in p['roads']:
        for a,b in zip(road['points'],road['points'][1:]):
            count=math.ceil(math.dist(a,b)/128)
            for i in range(count+1):
                q=[a[k]+(b[k]-a[k])*i/count for k in [0,1]]
                if terrain(q) in [0,8,15]:failures.append(['road center on source water/void',road['id'],q])
    pool=next(f for f in p['features'] if f['id']=='training_pool')
    pool_poly=rect(dict(center=pool['point'],envelope=pool['extent']))
    for b in town:
        if gap(pool_poly,rect(b))==0:failures.append(['teaching pool overlaps building',b['id']])
    metrics=measure([dict(polygon=rect(b),center=b['center'],floor_z=b['padHeightProposal']) for b in town])
    normal=defaultdict(list)
    for c in p['census']:
        if c['source'][0]==29 and c['id'].endswith('/npc') and c['placement']=='house/service dialogue':normal[c['venue']].append(c['id'])
    report={'passed':not failures,'failures':failures,'sourceNpcSites':48,'sourceServices':6,
       'sourceSpatialEventSites':len(p['sourceSites']),'sourceEventRecords':sum(len(s['records']) for s in p['sourceSites']),
       'attachedInteriorContacts':len(p['attachedInteriorContacts']),'attachedInteriorTeachers':sum(c['role'].startswith('teacher:') for c in p['attachedInteriorContacts']),
       'sourceVisualObjects':len(p['sourceObjects']),'wallEnclosedTownAssemblies':len(town),'curtainThicknessChecked':wall['architecture']['thickness'],'townAssemblies':len(town),'countryDestinations':len(p['buildings'])-len(town),
       'townRegularNpcVenues':len(normal),'townRegularNpcCount':sum(map(len,normal.values())),
       'townRegularNpcVenueHistogram':dict(Counter(map(len,normal.values()))),'townPublicNpcContacts':2,'townRestrictedNpcContacts':2,
       'puzzleChests':18,'ordinaryTownChests':sum(f['kind']=='chest' for f in p['features']),
       'townSewerConnectors':sum(f['kind']=='entrance' for f in p['features']),
       'sourceMonsterRecords':len(p['sourceMonsters']),'sourceInitiallySpatialMonsters':sum(m['initiallySpatial'] for m in p['sourceMonsters']),
       'metrics':metrics,'medianPrimaryDoorToRoadCenterline':sorted(b['frontage']['doorToCenterline'] for b in town)[len(town)//2],
       'limits':['Envelopes, road strips, primary frontages and 256-unit curtain clearance checked. Quantized terrain and decoration checks are in landscape/verification.json; no runtime collision test. Tower pads, gate passage, wall terrain footing and secondary approaches need native blockout checks.',
          'Source NPC occupancy is initial table state; dynamic MM8 quest moves are not simulated.',
          'Encounter volume counts, travel days, reward balance and MM5-skill equivalents are design decisions, not executable behavior.',
          'Orchard trees have individual grounded placements in landscape/decorations.json; interior room furnishings remain deferred.',
          'Secondary door positions are reserved on each facade; exact panel geometry and approach paving must be validated after authoring.']}
    write('verification.json',report)
    documents(p,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['limits','metrics']},indent=2))
    assert not failures, 'Fix layout conflicts before calling this proposal spatially checked.'


def documents(p,report):
    lines=['# Castleview–Kalindra resident and premises census','',
       'All 48 original NPC sites and six standard services are assigned. Titles and source dialogue are evidence; shared households, architectural quality and street positions are proposed adaptations.',
       '', 'Do not infer ancestry, household relationships, social rank or wealth from a portrait, a comic epithet, or a donor asset named rich/poor. A workshop title does not automatically create a shop gameplay service.',
       '', '## Physical town assemblies','',
       '| Map label | Assembly | Assigned NPCs / services | Separate destinations | Form / envelope | Construction |',
       '| --- | --- | --- | --- | --- | --- |']
    for b in p['buildings']:
        if b['district']!='Castleview':continue
        people=[c['name'] for c in p['census'] if c['building']==b['id']]
        lines.append(f'| {b["label"]} | {b["title"]} | {"; ".join(people) or "Ellinger remains inside tower BLV"} | {len(b["venues"])} | {b["form"]}; {b["envelope"][0]} × {b["envelope"][1]} | {b["quality"]} |')
    lines+=['','## Every source NPC and service','','Coordinates below are original MM5 map,x,y. Native proposed coordinates and byte-offset evidence are in layout.json.','','| Source | Person / service | Function | Assembly / venue |','| --- | --- | --- | --- |']
    for c in p['census']:
        lines.append(f'| {",".join(map(str,c["source"]))} | {c["name"]} | {c["role"]} | {c["building"]} / {c["venue"]}; {c["placement"]} |')
    lines+=['','## State and semantic distinctions','',
       '- Metla sells guild membership; Ordana, Goldur and Lydia are the three actual urban skill teachers. Miles tests an already qualified cartographer. No Master/Grandmaster teachers have been invented.',
       '- Tog’s Training remains the level-training service. The source does not identify a named dialogue NPC for each of the six service proprietors, so this census does not fabricate six people.',
       '- Jethro, Lydia and Miles share a physical mapmaking court but retain separate doors/destinations. Joe stays outside that professional group as a distinct fraudulent-map seller.',
       '- Two Drawkcab houses hold two monks each; this shortens walking distance without collapsing the four-step dialogue sequence.',
       '- Jasper is still a prisoner, Gettlewaithe still owns a conditional hostile court. Both are covered BLV annexes reached through the sewer graph, not ordinary unlocked houses.',
       '- Tanya/Gloria and Esteban/Bleys are proposed inn/boarding contacts. Sharing premises is not evidence that they are relatives or permanent household members.',
       '- The source Troyanna dialogue points to Neena, while the relevant Castleview NPC is Madame Oorla. Keep this recorded as a source inconsistency; do not create an unverified additional resident.',
       '- Luna’s first lead is the **Great Southern Tower**. Its sales record (map62 text1) leads to the actual statues at the Western Tower, Lakeside and Necropolis; map57 text3 labels a statuette. Do not confuse the initial lead with the retrieval site.',
       '- Kalindra’s court and Ellinger are retained in their castle/tower interiors. This outdoor census does not move their indoor population into town houses.',
       '- External dependency characters, including the Ogre Pass factions and Bark contacts, retain their original regional/interior locations; they are not added to Castleview to make every quest local.']
    lines+=['','## Contacts retained inside attached dungeons and castles','',
        'These 23 source contacts/services stay behind existing exterior entrances. They do not add outdoor buildings or count toward the 54 outdoor/town census entries. There are three additional original skill teachers here.',
        '', '| Source | Contact / service | Function | Exterior destination |', '| --- | --- | --- | --- |']
    for c in p['attachedInteriorContacts']:
        lines.append(f'| {",".join(map(str,c["source"]))} | {c["name"]} | {c["role"]} | {c["exteriorOwner"]} |')
    (OUT/'RESIDENTS.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':build()
