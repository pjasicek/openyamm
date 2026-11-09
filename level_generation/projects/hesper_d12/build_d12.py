"""Compile Crownspire, resolve published arrivals, and assemble its actors, loot and authored Lua for the stage."""
import json
import math
import shutil
import sys
from pathlib import Path

import yaml
from layout import ARRIVALS, PLAN, PROJECT, ROOT, ROOMS, checks, zone

sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build

semantic = json.loads((PROJECT / 'source/hes_d12.semantic.json').read_text())
assert semantic['completed_through'] == 'crown'
rows = {int(r[0]): r for r in (line.split('\t') for line in
        (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if r[0].isdigit()}
staged = {m['id']: m for m in yaml.safe_load((PROJECT.parent / 'hesper_stage/monsters.yml').read_text())['monsters']}

# Exactly the plan's pack order, including the separate conduit/turret markers.
packs = [(13,[10143])]*4 + [(14,[10144])]*4 + [
    (1,[10012]*4), (2,[10012]*6), (2,[10022]*2+[10041]*2), (2,[10057]*2),
    (3,[10022]*3), (3,[10012]*8), (4,[10012]*4+[10022]*2+[10041]),
    (5,[10022]*4+[10012]*2+[10041]), (6,[10041]*2+[10012]*2), (6,[10042]+[10012]*3),
    (6,[10057]*2), (6,[10022]*2), (7,[10041]*4+[10042]*2),
    (16,[10113]), (17,[10114]), (18,[10115]), (8,[10042]*2+[10041]*2), (8,[10022]*2),
    (15,[10042]*2), (10,[10145]), (12,[10042]*3), (21,[10012]*8+[10022]*2),
    (21,[10012]*3), (21,[10012]*3+[10022]*2), (20,[10012]*6), (8,[10042]*2+[10041]*2),
    (15,[10042]*2), (21,[10057]*2), (9,[10112]), (9,[10022]*2), (9,[10057]*4),
]
marks = [m for m in PLAN.marks if m['kind'] in ('monster','boss')]
assert len(packs)==len(marks)
actors=[]
tour=yaml.safe_load((PROJECT/'review_tour_01.yml').read_text())['shots']
decoration_rows={d['name']:d for d in yaml.safe_load((PROJECT.parent/'hesper_stage/decorations.yml').read_text())['decorations']}
placements=[]


def floor_z(rid,x,y):
    z=ROOMS[rid]['z']
    if rid=='stair': return min(768,max(0,math.floor((y-6272)/55)+1)*24)
    if rid=='court':
        radius=max(x*math.cos((k+.5)*math.pi/8)+(y-10056)*math.sin((k+.5)*math.pi/8)
                   for k in range(16))/math.cos(math.pi/16)
        if radius<1304: return 704
        if radius<1336: return 720
        if radius<1368: return 736
        if radius<1400: return 752
    if rid=='throne' and -800<=x<=800 and 17400<=y<=18600:
        return z+min(256,(math.floor((y-17400)/40)+1)*16)
    return z


def sector_at(x,y,z):
    if -1800<=x<=1800 and 8256<=y<=11856 and 703<=z<=2048:
        angle=math.atan2(y-10056,x)%(2*math.pi)
        index=next(i for i,end in enumerate((math.pi/2,math.pi,5*math.pi/4,7*math.pi/4,2*math.pi))
                   if angle<=end+1e-8)
        cell='court_ring' if math.hypot(x,y-10056)<1400 else 'court_'+str(index)
    else:
        matches=[(name,b) for name,b in semantic['room_bounds'].items()
                 if b[0]-1<=x<=b[2]+1 and b[1]-1<=y<=b[3]+1 and b[4]-1<=z<=b[5]+1]
        assert matches,(x,y,z)
        cell=min(matches,key=lambda pair:(pair[1][2]-pair[1][0])*(pair[1][3]-pair[1][1]))[0]
    return sorted(semantic['sectors']).index('room_'+cell)+1


def available(rid,x,y,radius):
    r=ROOMS[rid]; z=floor_z(rid,x,y)
    points=semantic['room_footprints'][rid]
    if not (min(p[0]for p in points)+radius+16<x<max(p[0]for p in points)-radius-16 and
            min(p[1]for p in points)+radius+16<y<max(p[1]for p in points)-radius-16): return False
    if rid=='court' and any(abs(floor_z(rid,x+radius*math.cos(k*math.pi/4),
                                                     y+radius*math.sin(k*math.pi/4))-z)>16 for k in range(8)):
        return False
    edges=list(zip(points,points[1:]+points[:1]))
    if rid=='corridor':
        # The dogleg is concave: test the polygon and actual wall segments, not every wall's half-plane.
        if sum((ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax for (ax,ay),(bx,by) in edges)%2==0:
            return False
        for (ax,ay),(bx,by) in edges:
            t=max(0,min(1,((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2)))
            if math.hypot(x-ax-t*(bx-ax),y-ay-t*(by-ay))<radius+16:return False
    else:
        for (ax,ay),(bx,by) in edges:
            if ((bx-ax)*(y-ay)-(by-ay)*(x-ax))/math.hypot(bx-ax,by-ay)<radius+16: return False
    for room,x0,y0,z0,x1,y1,z1 in semantic['obstacles']:
        if room==rid and z<z1-1 and x0-radius<x<x1+radius and y0-radius<y<y1+radius: return False
    # Keep the review camera out of bodies, including the two corrected trophy/lift poses.
    if any(abs(z-shot['position'][2])<300 and math.hypot(x-shot['position'][0],y-shot['position'][1])<radius+250
           for shot in tour): return False
    for name,dx,dy,dz in semantic['decoration_positions']:
        dr=decoration_rows[name].get('radius',0)
        if dr and abs(z-dz)<256 and math.hypot(x-dx,y-dy)<radius+dr+32: return False
    return all(math.hypot(x-a['position']['x'],y-a['position']['y'])>=max(400,radius+a['radius']+64)
               for a in actors if abs(z-a['position']['z'])<300)


def actor(monster,group,x,y,z,yaw):
    row=rows[monster]; size=staged[monster]
    immobile=group in range(1,9) or monster in (10057,10143,10144,10145) or group==20
    record={'actor_index':len(actors),'name':row[1],'npc_id':0,
            'attributes':0x10000 if group in (11,12,19) else 0,'hp':int(row[4]),
            'hostility_type':int(row[12]),'monster_info_id':monster,'monster_id':monster,
            'radius':size['radius'],'height':size['height'],'move_speed':0 if immobile else int(row[13]),
            'position':{'x':x,'y':y,'z':z},'initial_yaw_units':yaw,'immobile':immobile,
            'sprite_ids':[0]*4,'sector_id':sector_at(x,y,z),'current_action_animation':0,
            'carried_item_id':0,'group':group,'ally':0,'unique_name_index':0}
    actors.append(record)


assert available('corridor',3930,2620,129)
assert not available('corridor',3930,2250,129)

for pack_index,(mark,(group,monsters)) in enumerate(zip(marks,packs)):
    assert len(monsters)==mark['count'],mark
    room=next(r for r in PLAN.rooms if r['sectors'] and r['floor']==mark['floor'] and
              r['x']<=mark['x']<=r['x']+r['w'] and r['y']<=mark['y']<=r['y']+r['h'])
    if group==10: mark=dict(mark,y=18200)
    for monster in monsters:
        radius=staged[monster]['radius']
        candidates=((round(mark['x']+ring*160*math.cos(a*2*math.pi/(8+4*ring))),
                     round(mark['y']+ring*160*math.sin(a*2*math.pi/(8+4*ring))))
                    for ring in range(math.ceil(math.hypot(room['w'],room['h'])/160)+1)
                    for a in range(1 if ring==0 else 8+4*ring))
        x,y=next((x,y) for x,y in candidates if available(room['id'],x,y,radius))
        z=floor_z(room['id'],x,y)
        if group==14: z+=32
        yaw=0 if group in (4,5,16,20,21) else 1024 if group in (17,18) else 1536
        actor(monster,group,x,y,z,yaw)
        placements.append({'actor_index':len(actors)-1,'pack':pack_index,'room':room['id'],
                           'mark':[mark['x'],mark['y']],'position':[x,y,z]})
assert len(actors)==121
enthroned=next(a for a in actors if a['monster_id']==10145)
for monster,group in ((10120,11),(10146,19)):
    actor(monster,group,**enthroned['position'],yaw=1536)

# Resolve destinations only from their builders' published records. A later build wires D13 automatically.
exits={}
for name,project,record,key,mapfile in (
    ('gate','hesper_out4','out4_build.json','spire_gate','hes_out4.odm'),
    ('pad','hesper_out4','out4_build.json','pad_lift','hes_out4.odm'),
    ('service','hesper_d15','source/hes_d15.semantic.json','service_lift','hes_d15.blv'),
    ('shaft','hesper_d13','source/hes_d13.semantic.json','shaft_bottom','hes_d13.blv')):
    path=PROJECT.parent/project/record
    destination={'map':mapfile,'key':key,'ready':False}
    if path.exists():
        data=json.loads(path.read_text()); value=data.get('arrivals',data)[key]
        if isinstance(value,dict): position=value['position']; degrees=value['direction_degrees']
        else: position=value[:3]; degrees=value[3]
        destination.update(x=position[0],y=position[1],z=position[2],direction=round(degrees/360*2048)%2048,ready=True)
    exits[name]=destination

def lua_value(value):
    if isinstance(value,dict):return '{'+','.join(f'[{json.dumps(str(k))}]={lua_value(v)}' for k,v in value.items())+'}'
    if isinstance(value,list):return '{'+','.join(lua_value(v) for v in value)+'}'
    return json.dumps(value)

scripts={10112:'gatekeeper',10113:'ssekh',10114:'mraal',10115:'xith',10145:'hierarch_seated',
         10120:'hierarch',10146:'hierarch_falter'}
scripted=[{'index':a['actor_index'],'group':a['group'],'behavior':'hesper/'+(
    scripts[a['monster_id']] if a['monster_id'] in scripts else 'barracks_sleep' if a['group']==20 else
    'court_noble' if a['monster_id']==10042 else 'palace_guard')} for a in actors]
actor_ids={str(a['monster_id']):a['actor_index'] for a in actors if a['monster_id'] in scripts}
chests=[{'name':name,'gold':gold,'random':True} for name,gold in (
    ('Grafting Hall pod',9000),('Barracks locker',9000),('Gallery of Houses coffer',9000),
    ('Noble Galleries coffer',9000),('Core Halls locker',9000),('Sanctum coffer',13500))]
chests += [{'name':'Armoury: four Engrams','fixed':[11331]*4,'random':False,'gold':0},
           {'name':'Trophy East coffer','gold':13500,'random':True}]
placeholders={'D12_EXITS':lua_value(exits),'D12_ACTORS':lua_value(scripted),'D12_BOSSES':lua_value(actor_ids)}

# The Hierarch's throne (hes_noble_bosses_claude, integrator 2026-10-24): a permanent decoration at the enthroned
# Hierarch's spot with his facing, so it stays when 10145 is hidden at phase 2. Added to the compiler's source (a
# marker node cloned from an existing one, at map units / 128, moved there when already present, and its entity).
def add_throne(position, facing_degrees):
    import struct
    name='DECOR_hes_hierarch_throne_deco_0'
    geometry_path=PROJECT/'source/hes_d12.geometry.yml'; glb_path=PROJECT/'source/hes_d12.glb'
    geometry=json.loads(geometry_path.read_text())
    # decoration_ids.yml holds the table's row number; a map entity names the row's index (number - 1)
    deco_id=yaml.safe_load((PROJECT.parent/'hesper_stage/decoration_ids.yml').read_text())['ids']['hes_hierarch_throne_deco']-1
    raw=glb_path.read_bytes(); n=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+n]); binary=bytearray(raw[28+n:])
    target=[position[k]/128 for k in ('x','y','z')]
    existing=next((node for node in doc['nodes'] if node.get('name')==name),None)
    if existing is not None:
        # already added: move its marker to the position (rewritten in place, same vertex count)
        accessor=doc['accessors'][doc['meshes'][existing['mesh']]['primitives'][0]['attributes']['POSITION']]
        view=doc['bufferViews'][accessor['bufferView']]
        start=view.get('byteOffset',0)+accessor.get('byteOffset',0)
        points=[struct.unpack_from('<3f',binary,start+i*12) for i in range(accessor['count'])]
    else:
        template=next(node for node in doc['nodes'] if (node.get('name') or '').startswith('DECOR_hes_shelf_rack_'))
        mesh=json.loads(json.dumps(doc['meshes'][template['mesh']])); primitive=mesh['primitives'][0]
        accessor=doc['accessors'][primitive['attributes']['POSITION']]; view=doc['bufferViews'][accessor['bufferView']]
        start=view.get('byteOffset',0)+accessor.get('byteOffset',0)
        points=[struct.unpack_from('<3f',binary,start+i*view.get('byteStride',12)) for i in range(accessor['count'])]
    centre=[(min(p[k] for p in points)+max(p[k] for p in points))/2 for k in range(3)]
    moved=[[p[k]-centre[k]+target[k] for k in range(3)] for p in points]
    data=b''.join(struct.pack('<3f',*p) for p in moved)
    bounds={'min':[min(p[k] for p in moved) for k in range(3)],'max':[max(p[k] for p in moved) for k in range(3)]}
    if existing is not None:
        binary[start:start+len(data)]=data; accessor.update(bounds)
    else:
        binary+=b'\0'*(-len(binary)%4)
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)}); binary+=data
        doc['accessors'].append(dict(accessor,bufferView=len(doc['bufferViews'])-1,byteOffset=0,**bounds))
        primitive['attributes']['POSITION']=len(doc['accessors'])-1; mesh['name']=name
        doc['meshes'].append(mesh)
        doc['nodes'].append({'name':name,'mesh':len(doc['meshes'])-1,'extras':{'levelgen_kind':'decoration'}})
        doc['scenes'][0]['nodes'].append(len(doc['nodes'])-1)
    binary+=b'\0'*(-len(binary)%4); doc['buffers'][0]['byteLength']=len(binary)
    js=json.dumps(doc,separators=(',',':')).encode(); js+=b' '*(-len(js)%4)
    glb_path.write_bytes(struct.pack('<III',0x46546C67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4E4F534A)
                         +js+struct.pack('<II',len(binary),0x004E4942)+binary)
    entity={'id':'hes_hierarch_throne_deco_0','kind':'decoration','source_node':name,'decoration_list_id':deco_id,
            'event_id_primary':0,'event_id_secondary':0,'facing':facing_degrees}
    geometry['entities']=[e for e in geometry['entities'] if e.get('source_node')!=name]+[entity]
    # the compiler puts a decoration in the sector of the room that lists its node (as sector_at finds the room)
    x,y,z=position['x'],position['y'],position['z']
    matches=[(room,b) for room,b in semantic['room_bounds'].items()
             if b[0]-1<=x<=b[2]+1 and b[1]-1<=y<=b[3]+1 and b[4]-1<=z<=b[5]+1]
    cell=min(matches,key=lambda pair:(pair[1][2]-pair[1][0])*(pair[1][3]-pair[1][1]))[0]
    for room in geometry['rooms']:
        room['source_nodes']=[n for n in room['source_nodes'] if n!=name]
        if room['id']=='room_'+cell:
            room['source_nodes'].append(name)
    assert any(name in room['source_nodes'] for room in geometry['rooms']),cell
    geometry_path.write_text(json.dumps(geometry,indent=2)+'\n')


# the Hierarch faces 1536 yaw units (270 degrees; an actor's 0 is +X); a decoration model's 0 faces +Y, so the
# throne takes 270 - 90
add_throne(enthroned['position'],180)
report=build(PROJECT,'hes_d12.blv',placeholders,'spire_gate',chests,actors)
scene_path=PROJECT/'runtime/hes_d12.scene.yml'
scene=json.loads(scene_path.read_text())
for index,chest in enumerate(scene['loot_containers']):
    chest['presentation']='colonial locker' if index in (1,4) else 'kreegan pod'
    if index!=6:
        # shortcut: native T6 rolls represent H3 until the Hesper H3 loot pool is installed by the integrator.
        chest['random_treasure_level']=6

item_rows={int(r[0]):r for r in (line.split('\t') for line in
           (ROOT/'output/hesper_stage/assets_editor_dev/worlds/hesper/data_tables/items.txt').read_text().splitlines())
           if r[0].isdigit()}
object_ids=[int(line.split('\t')[2]) for line in
            (ROOT/'assets_dev/engine/data_tables/object_list.txt').read_text(encoding='latin1').splitlines()[1:]]
supplies=[]
for x,y,z,last in ((400,8092,800,11301),(800,15350,2368,11303)):
    supplies += [(item,x-60+i*30,y,z,0) for i,item in enumerate([11300,11300,11302,11302,last])]
objects=[]
for item,x,y,z,gold in supplies:
    sprite=85 if gold else int(item_rows[item][11]); raw=bytearray(36)
    raw[0:4]=item.to_bytes(4,'little');raw[12:16]=gold.to_bytes(4,'little')
    objects.append({'sprite_object_index':len(objects),'sprite_id':sprite,'object_description_id':object_ids.index(sprite),
                    'position':{'x':x,'y':y,'z':z},'velocity':{'x':0,'y':0,'z':0},'yaw_angle':0,'sound_id':0,
                    'attributes':0,'sector_id':sector_at(x,y,z),'time_since_created':0,'temporary_lifetime':0,
                    'glow_radius_multiplier':0,'spell_id':0,'spell_level':0,'spell_skill':0,'field54':0,
                    'spell_caster_pid':0,'spell_target_pid':0,'lod_distance':0,'spell_caster_ability':0,
                    'initial_position':{'x':0,'y':0,'z':0},'raw_containing_item_hex':raw.hex().upper()})
scene['initial_state']['sprite_objects']=objects
scene_path.write_text(json.dumps(scene,indent=2)+'\n')
tree=PROJECT/'runtime/worlds/hesper'
shutil.copy2(scene_path,tree/'maps'/scene_path.name)
(tree/'behaviors').mkdir(exist_ok=True)
for path in (PROJECT/'source/behaviors').glob('*.lua'):shutil.copy2(path,tree/'behaviors'/path.name)
report.update(actors=len(actors),encounters=121,arrivals=ARRIVALS,exits=exits,
              actor_groups={str(g):[a['actor_index'] for a in actors if a['group']==g] for g in range(1,22)},
              bosses=actor_ids,placements=placements,checks=checks('final'))
assert report['sectors']==55 and report['doors']==26 and len(actors)==123
(PROJECT/'d12_build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
