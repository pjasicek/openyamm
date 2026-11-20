"""Author the actual Greywatch source scene through Blender MCP.

The source is intentionally reproducible. Gameplay population and runtime assembly live outside Blender;
semantic objects and their custom properties preserve the link between geometry and those records.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path('/home/pjasicek/github/OpenYAMM')
PROJECT = ROOT / 'level_generation/projects/brackenford_greywatch'
OUTPUT = PROJECT / 'source'
OUTPUT.mkdir(exist_ok=True)
PLAN = json.loads((PROJECT / 'indoor_plan.json').read_text())
SCALE = 128
previous_scene = bpy.data.scenes.get('Greywatch Vault authoring')
scene = bpy.data.scenes.new('Greywatch Vault authoring')
bpy.context.window.scene = scene
if previous_scene is not None:
    for obj in list(previous_scene.objects):
        if obj.get('levelgen_kind'):
            bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.scenes.remove(previous_scene)
scene.name = 'Greywatch Vault authoring'
scene['levelgen_project'] = 'brackenford_greywatch'
metadata = {'format_version':2, 'kind':'indoor_geometry', 'map_file':'lg02.blv',
    'source':{'authoring_file':'lg02.blend','asset_path':'lg02.glb','coordinate_system':'blender_z_up',
              'unit_scale':SCALE,'import':{'source_format':'glb','reserve_sector_zero':True,
                'merge_coplanar_faces':True,'generate_bsp':True,'generate_outlines':True}},
    'materials':[], 'rooms':[], 'portals':[], 'surfaces':[], 'mechanisms':[], 'entities':[], 'lights':[], 'spawns':[]}
texture_paths = {p.stem.lower():p for p in (ROOT / 'assets_dev/worlds/mm8/textures').iterdir()
                 if p.suffix.lower() == '.bmp'}
materials = {}
dimensions = {}
palette = ['GSton1WL','GStn1BOT','GStn1TP1','GSton1FL','TFB11','GCav1flr','GCav1wal',
           'gt002a','gt002b','gt002g','gt003a','solid01','T1butt']
for key in palette:
    image = bpy.data.images.load(str(texture_paths[key.lower()]), check_existing=True)
    image.pack()
    material = bpy.data.materials.get('LG_'+key) or bpy.data.materials.new('LG_'+key)
    material.use_nodes = True
    texture = next((n for n in material.node_tree.nodes if n.type=='TEX_IMAGE'),None)
    if texture is None:
        texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Closest'
    material.node_tree.links.new(texture.outputs['Color'],
                                  material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    materials[key] = material
    dimensions[key] = tuple(image.size)
    metadata['materials'].append({'id':key,'source_material':material.name,'texture':key,
                                  'texture_width':image.size[0],'texture_height':image.size[1]})


def mesh(name, panels, kind, **properties):
    vertices, polygons, uvs, keys = [], [], [], []
    for coords, key, inward in panels:
        points = [Vector(p) for p in coords]
        normal = (points[1]-points[0]).cross(points[2]-points[0])
        if normal.length < .001:
            continue
        if normal.dot(Vector(inward)) < 0:
            points.reverse()
        offset = len(vertices)
        vertices.extend(tuple(p/SCALE) for p in points)
        polygons.append(tuple(range(offset, len(vertices))))
        drop = max(range(3),key=lambda i:abs(normal[i]))
        tangents = [i for i in range(3) if i != drop]
        width,height = dimensions[key]
        if key=='T1butt':
            assert len(points)==4
            uvs.extend([(0,0),(1,0),(1,1),(0,1)])
        else:
            uvs.extend((p[tangents[0]]/(width*2),p[tangents[1]]/(height*2)) for p in points)
        keys.append(key)
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], polygons)
    data.update()
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj['levelgen_kind'] = kind
    for key,value in properties.items():
        obj[key] = value
    for material in materials.values():
        data.materials.append(material)
    for polygon,key in zip(data.polygons,keys):
        polygon.material_index = palette.index(key)
    uv_layer = data.uv_layers.new()
    for loop,uv in zip(uv_layer.data,uvs):
        loop.uv = uv
    return obj


def own(room, obj):
    next(r for r in metadata['rooms'] if r['id']=='room_'+room)['source_nodes'].append(obj.name)


def panel_rect(axis, fixed, a, b, bottom, top, key, inward):
    if b <= a or top <= bottom:
        return []
    coords = [(fixed,a,bottom),(fixed,b,bottom),(fixed,b,top),(fixed,a,top)] if axis == 'x' else [
              (a,fixed,bottom),(b,fixed,bottom),(b,fixed,top),(a,fixed,top)]
    return [(coords,key,inward)]


def box_panels(lo, hi, wall='GSton1WL', top='GSton1FL'):
    x0,y0,z0=lo; x1,y1,z1=hi
    return [([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],top,(0,0,-1)),
            ([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],top,(0,0,1)),
            *panel_rect('x',x0,y0,y1,z0,z1,wall,(-1,0,0)),
            *panel_rect('x',x1,y0,y1,z0,z1,wall,(1,0,0)),
            *panel_rect('y',y0,x0,x1,z0,z1,wall,(0,-1,0)),
            *panel_rect('y',y1,x0,x1,z0,z1,wall,(0,1,0))]


rooms = {r['id']:dict(r, openings={}) for r in PLAN['rooms']}
rooms['cave_arrival']['openings']['s'] = 384
# Preserve twelve 32-unit risers with at least a 96-unit tread on the first flight.
rooms['stair_gallery']['center'][0] = 3328
rooms['vault_bend'] = {'id':'vault_bend','center':[9216,6144,768],'size':[512,512],
                       'shape':'rectangle','openings':{},'hostile_budget':0}
connections = []
for link in PLAN['connections']:
    if link['a']=='upper_landing' and link['b']=='vault':
        connections.extend([dict(a='upper_landing',b='vault_bend',kind='passage'),
                            dict(a='vault_bend',b='vault',kind='passage')])
    else:
        connections.append(link)


def endpoint(room, side):
    x,y,z = room['center']; w,h = room['size']
    return {'n':(x,y+h/2,z),'s':(x,y-h/2,z),'e':(x+w/2,y,z),'w':(x-w/2,y,z)}[side]


for link in connections:
    a,b = rooms[link['a']],rooms[link['b']]
    dx=b['center'][0]-a['center'][0]; dy=b['center'][1]-a['center'][1]
    assert dx==0 or dy==0, link
    side_a = ('e' if dx>0 else 'w') if dx else ('n' if dy>0 else 's')
    side_b = {'e':'w','w':'e','n':'s','s':'n'}[side_a]
    a['openings'][side_a] = 512
    b['openings'][side_b] = 512
    link.update(start=endpoint(a,side_a), end=endpoint(b,side_b), side_a=side_a, side_b=side_b,
                id='link_'+link['a']+'_'+link['b'])


plates = [dict(name='gallery_plate',room='stair_gallery',cx=3328,cy=3072,z=384,event=301,flags=['secret']),
          dict(name='armory_plate',room='link_watch_hall_armory',cx=-1536,cy=3072,z=768,event=302,flags=[])]


def add_room(identifier, panels):
    # A plate must own its floor patch. An overlay above a continuous floor is not reliable support geometry.
    for plate in (p for p in plates if p['room'] == identifier):
        hx0,hx1 = plate['cx']-128,plate['cx']+128
        hy0,hy1 = plate['cy']-192,plate['cy']+192
        cut_panels = []
        cuts = 0
        for coords,key,normal in panels:
            xs=[p[0] for p in coords]; ys=[p[1] for p in coords]
            x0,x1,y0,y1 = min(xs),max(xs),min(ys),max(ys)
            if (normal == (0,0,1) and all(p[2] == plate['z'] for p in coords)
                    and x0 <= hx0 < hx1 <= x1 and y0 <= hy0 < hy1 <= y1):
                assert len(coords) == 4 and len(set(xs)) == len(set(ys)) == 2
                for ax,bx,ay,by in [(x0,hx0,y0,y1),(hx1,x1,y0,y1),
                                   (hx0,hx1,y0,hy0),(hx0,hx1,hy1,y1)]:
                    if ax < bx and ay < by:
                        cut_panels.append(([(ax,ay,plate['z']),(bx,ay,plate['z']),
                                            (bx,by,plate['z']),(ax,by,plate['z'])],key,normal))
                cuts += 1
            else:
                cut_panels.append((coords,key,normal))
        assert cuts == 1, (identifier,plate['name'],cuts)
        panels = cut_panels
    obj = mesh('ROOM_'+identifier,panels,'room',semantic_id=identifier)
    # Native Naga Vault and Ilsingore's Cave both use 22; 0 would leave every room fully lit.
    obj['min_ambient_light_level'] = 22
    metadata['rooms'].append({'id':'room_'+identifier,'source_nodes':[obj.name],
                              'min_ambient_light_level':22})
    return obj


for identifier,room in rooms.items():
    x,y,z = room['center']; w,h=room['size']; x0=x-w/2; x1=x+w/2; y0=y-h/2; y1=y+h/2
    cave = identifier=='cave_arrival'
    chamfer = 0 if room['shape']=='rectangle' else 256
    polygon = [(x0+chamfer,y0),(x1-chamfer,y0),(x1,y0+chamfer),(x1,y1-chamfer),
               (x1-chamfer,y1),(x0+chamfer,y1),(x0,y1-chamfer),(x0,y0+chamfer)] if chamfer else [
                (x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    floor = 'GCav1flr' if cave else 'GSton1FL'
    wall = 'GCav1wal' if cave else 'GSton1WL'
    panels = [([(px,py,z) for px,py in polygon],floor,(0,0,1)),
              ([(px,py,z+768) for px,py in polygon],wall if cave else 'TFB11',(0,0,-1))]
    for i,(ax,ay) in enumerate(polygon):
        bx,by = polygon[(i+1)%len(polygon)]
        inward = (-(by-ay),bx-ax,0)
        side = 's' if ay==by==y0 else 'n' if ay==by==y1 else 'w' if ax==bx==x0 else 'e' if ax==bx==x1 else None
        width = room['openings'].get(side)
        if width:
            axis = 'x' if side in ('e','w') else 'y'
            fixed = ax if axis=='x' else ay
            low,high = sorted((ay,by) if axis=='x' else (ax,bx))
            mid = y if axis=='x' else x
            panels += panel_rect(axis,fixed,low,mid-width/2,z,z+768,wall,inward)
            panels += panel_rect(axis,fixed,mid+width/2,high,z,z+768,wall,inward)
            panels += panel_rect(axis,fixed,mid-width/2,mid+width/2,z+512,z+768,wall,inward)
        elif cave:
            # The wall swells inward at mid-height and meets the unchanged floor/ceiling rims.
            rings = [(0,1),(320,.91),(768,1)]
            for (za,sa),(zb,sb) in zip(rings,rings[1:]):
                p=[(round(x+(ax-x)*sa),round(y+(ay-y)*sa),z+za),
                   (round(x+(bx-x)*sa),round(y+(by-y)*sa),z+za),
                   (round(x+(bx-x)*sb),round(y+(by-y)*sb),z+zb),
                   (round(x+(ax-x)*sb),round(y+(ay-y)*sb),z+zb)]
                panels += [(p[:3],wall,inward),([p[0],p[2],p[3]],wall,inward)]
        else:
            for bottom,top,key in [(0,128,'GStn1BOT'),(128,640,wall),(640,768,'GStn1TP1')]:
                panels.append(([(ax,ay,z+bottom),(bx,by,z+bottom),(bx,by,z+top),(ax,ay,z+top)],key,inward))
    add_room(identifier,panels)


def world(link, t, lateral, height):
    a=Vector(link['start']); b=Vector(link['end']); direction=(b-a); direction.z=0; direction.normalize()
    point=a+direction*t+Vector((-direction.y,direction.x,0))*lateral
    return (round(point.x),round(point.y),round(height))


for link in connections:
    a,b=link['start'],link['end']; length=math.hypot(b[0]-a[0],b[1]-a[1]); z0=a[2];z1=b[2]
    ceiling=max(z0,z1)+512; base=min(z0,z1)
    sections=[]
    if link['kind']=='button_gate_and_lift':
        sections=[(0,448,z0),(448,960,z0-64),(960,length,z1)]
    else:
        steps=max(1,round(abs(z1-z0)/32))
        assert steps==1 or length/steps>=96, (link['id'],length,steps)
        for i in range(steps):
            # A rising flight starts with the first riser; a descending flight ends with the last one.
            level=z0+(z1-z0)*(i+1)/steps if z1>=z0 else z0+(z1-z0)*i/steps
            sections.append((length*i/steps,length*(i+1)/steps,level))
    panels=[([world(link,0,-256,ceiling),world(link,length,-256,ceiling),
              world(link,length,256,ceiling),world(link,0,256,ceiling)],'TFB11',(0,0,-1))]
    direction=Vector((b[0]-a[0],b[1]-a[1],0)).normalized(); left=Vector((-direction.y,direction.x,0))
    bottom=min(level for _,_,level in sections)
    for side in [-256,256]:
        panels.append(([world(link,0,side,bottom),world(link,length,side,bottom),
                        world(link,length,side,ceiling),world(link,0,side,ceiling)],'GSton1WL',tuple(-left if side>0 else left)))
    for t0,t1,level in sections:
        panels.append(([world(link,t0,-256,level),world(link,t1,-256,level),
                        world(link,t1,256,level),world(link,t0,256,level)],'GSton1FL',(0,0,1)))
    transitions=[(0,z0,sections[0][2]),(length,sections[-1][2],z1)]
    transitions += [(sections[i][1],sections[i][2],sections[i+1][2]) for i in range(len(sections)-1)]
    for t,za,zb in transitions:
        if za!=zb:
            panels.append(([world(link,t,-256,min(za,zb)),world(link,t,256,min(za,zb)),
                            world(link,t,256,max(za,zb)),world(link,t,-256,max(za,zb))],
                           'GStn1BOT',tuple(-direction if zb>za else direction)))
    for t,z,inward in [(0,z0,direction),(length,z1,-direction)]:
        if z+512<ceiling:
            panels.append(([world(link,t,-256,z+512),world(link,t,256,z+512),
                            world(link,t,256,ceiling),world(link,t,-256,ceiling)],'GSton1WL',tuple(inward)))
        if bottom<z:
            panels.append(([world(link,t,-256,bottom),world(link,t,256,bottom),
                            world(link,t,256,z),world(link,t,-256,z)],'GSton1WL',tuple(inward)))
    add_room(link['id'],panels)
    for suffix,t,room,z,normal in [('a',0,link['a'],z0,tuple(direction)),
                                  ('b',length,link['b'],z1,tuple(-direction))]:
        name='PORTAL_'+link['id']+'_'+suffix
        mesh(name,[([world(link,t,-256,z),world(link,t,256,z),world(link,t,256,z+512),
                     world(link,t,-256,z+512)],'solid01',normal)],'portal')
        metadata['portals'].append({'id':link['id']+'_'+suffix,'source_node':name,
                                    'front_room':'room_'+link['id'],'back_room':'room_'+room})


def mechanism(name,room,lo,hi,door_id,axis,distance,event=None,secret=False):
    obj=mesh('MECH_'+name,box_panels(lo,hi),'mechanism',semantic_id=name,door_id=door_id)
    own(room,obj)
    metadata['mechanisms'].append({'id':name,'kind':'linear','source_nodes':[obj.name],
      'door':{'door_id':door_id,'initial_state':'closed','source_pose':'closed',
              'direction':[-component for component in axis],'move_length':distance,
                 'open_speed':128,'close_speed':128}})
    if event is not None:
        metadata['surfaces'].append({'id':name,'source_node':obj.name,
          'flags':['texture_move_by_door']+(['secret'] if secret else []),
          'trigger':{'event_id':event,'type':'click'}})
    return obj


mechanism('watch_left','link_castle_arrival_watch_hall',(-256,1256,768),(0,1320,1280),1,[-1,0,0],256,101)
mechanism('watch_right','link_castle_arrival_watch_hall',(0,1256,768),(256,1320,1280),2,[1,0,0],256,101)
mechanism('lift_gate','link_records_upper_landing',(5376,4224,384),(5888,4288,896),3,[0,0,1],512)
mechanism('secret_wall','link_barracks_secret',(8448,3968,384),(8960,4032,896),4,[0,0,1],512,103,True)
mechanism('shortcut','link_lower_passage_castle_arrival',(1040,-256,768),(1104,256,1280),5,[0,0,1],512,104)
mechanism('lift_platform','link_records_upper_landing',(5376,4544,320),(5888,5056,384),6,[0,0,1],384)
# Ordinary closed doors split the records fight from the barracks and cave patrols.
# Keep the first six mechanism IDs stable; these can be operated from either approach.
mechanism('records_south_door','records',(5376,2056,384),(5888,2120,896),7,[0,0,1],512,107)
mechanism('barracks_door','link_records_barracks',(6976,2816,384),(7040,3328,896),8,[0,0,1],512,108)


def trigger(name,room,panels,event,kind='click',flags=()):
    obj=mesh('TRIGGER_'+name,panels,'trigger',event_id=event,activation=kind)
    own(room,obj)
    metadata['surfaces'].append({'id':name,'source_node':obj.name,'flags':list(flags),
                                  'trigger':{'event_id':event,'type':kind}})
    return obj


trigger('castle_exit','castle_arrival',panel_rect('y',-1023,-192,192,768,1280,'gt002b',(0,1,0)),1)
trigger('cave_exit','cave_arrival',panel_rect('y',-3839,5440,5824,0,512,'solid01',(0,1,0)),2)
# Retraction hides moving faces inside masonry; fixed controls remain reachable in both states.
trigger('watch_south_control','link_castle_arrival_watch_hall',
        panel_rect('x',-255,1088,1216,864,992,'T1butt',(1,0,0)),101)
trigger('watch_north_control','link_castle_arrival_watch_hall',
        panel_rect('x',-255,1408,1536,864,992,'T1butt',(1,0,0)),101)
trigger('secret_inside_control','secret',
        panel_rect('y',4737,9024,9152,480,608,'T1butt',(0,1,0)),103)
trigger('shortcut_castle_control','castle_arrival',
        panel_rect('x',1023,320,448,864,992,'T1butt',(-1,0,0)),104)
trigger('shortcut_passage_control','link_lower_passage_castle_arrival',
        panel_rect('y',255,1152,1280,832,992,'T1butt',(0,-1,0)),104)
trigger('lift_gate_button','records',panel_rect('x',6655,3520,3648,480,608,'T1butt',(-1,0,0)),102)
trigger('lift_lower_button','link_records_upper_landing',
        panel_rect('x',5377,4416,4544,480,608,'T1butt',(1,0,0)),105)
trigger('lift_upper_button','link_records_upper_landing',
        panel_rect('x',5377,5120,5248,864,992,'T1butt',(1,0,0)),106)
# Native pressure-plate activation observes the support floor. Keeping this on the complete
# platform mesh makes its floor and event move with the same native door vertex set.
metadata['surfaces'].append({'id':'lift_boarding_plate','source_node':'MECH_lift_platform',
    'flags':['texture_move_by_door'],'trigger':{'event_id':105,'type':'pressure_plate'}})
trigger('records_south_inside_control','records',
        panel_rect('y',2049,5952,6080,480,608,'T1butt',(0,1,0)),107)
trigger('records_south_passage_control','link_records_lower_passage',
        panel_rect('x',5377,1888,2016,480,608,'T1butt',(1,0,0)),107)
trigger('barracks_west_control','link_records_barracks',
        panel_rect('y',2817,6784,6912,480,608,'T1butt',(0,1,0)),108)
trigger('barracks_east_control','link_records_barracks',
        panel_rect('y',2817,7104,7232,480,608,'T1butt',(0,1,0)),108)
for name,room,cx,cy,z,event in [('armory','armory',-3328,3328,768,201),
                              ('secret','secret',8704,5504,384,202),
                              ('barracks','barracks',9216,3200,384,203),
                              ('vault','vault',9728,7936,768,204)]:
    trigger(name+'_chest',room,box_panels((cx-80,cy-56,z),(cx+80,cy+56,z+96),'gt002b','gt002g'),event)
for plate in plates:
    cx,cy,z = plate['cx'],plate['cy'],plate['z']
    trigger(plate['name'],plate['room'],[([(cx-128,cy-192,z),(cx+128,cy-192,z),(cx+128,cy+192,z),
                        (cx-128,cy+192,z)],'GStn1BOT',(0,0,1))],plate['event'],'pressure_plate',plate['flags'])


def furnishing(name,room,parts):
    panels=[]
    for lo,hi in parts:
        panels.extend(box_panels(lo,hi,'gt003a','gt002a'))
    obj=mesh('STATIC_'+name,panels,'furnishing',semantic_id=name)
    own(room,obj)


def table(name,room,x,y,z,width,depth,height):
    parts=[((x-width/2,y-depth/2,z+height-24),(x+width/2,y+depth/2,z+height))]
    for dx in [-width/2+24,width/2-24]:
        for dy in [-depth/2+24,depth/2-24]:
            parts.append(((x+dx-16,y+dy-16,z),(x+dx+16,y+dy+16,z+height-24)))
    furnishing(name,room,parts)


table('arrival_bench_west','castle_arrival',-800,0,768,160,640,96)
table('arrival_bench_east','castle_arrival',800,-400,768,160,384,96)
table('records_desk','records',4944,3680,384,320,512,160)
table('barracks_mess_west','barracks',8160,2448,384,512,224,160)
table('barracks_mess_east','barracks',9120,2448,384,512,224,160)
furnishing('armory_storage_rack','armory',[
    ((-3888,2560,768),(-3824,2592,1152)),((-3888,3200,768),(-3824,3232,1152)),
    ((-3888,2560,896),(-3752,3232,920)),((-3888,2560,1128),(-3752,3232,1152))])


def marker(name,position,kind,**properties):
    obj=bpy.data.objects.new(name,None)
    obj.empty_display_type='ARROWS'; obj.empty_display_size=1
    obj.location=Vector(position)/SCALE
    scene.collection.objects.link(obj)
    obj['levelgen_kind']=kind
    for key,value in properties.items():
        obj[key]=value
    return obj


marker('PARTY_START_default',(0,-512,768),'party_start',arrival='castle',facing_degrees=90)
marker('ARRIVAL_castle',(0,-512,768),'arrival',facing_degrees=90)
marker('ARRIVAL_cave',(5632,-3200,0),'arrival',facing_degrees=90)
for room in rooms.values():
    x,y,z=room['center']
    for index in range(room['hostile_budget']):
        variant = 195 if index==0 or room['id']=='vault' else 193 if room['id']=='armory' else 194
        actor_id = room['actor_ids'][index] if 'actor_ids' in room else 'ACTOR_'+room['id']+'_'+str(index)
        marker(actor_id,(x+(index%3-1)*384,y+(index//3*512-256),z),
               'fixed_actor',room=room['id'],monster_id=variant)
for room in rooms.values():
    if room['id']=='vault_bend':
        continue
    x,y,z=room['center']
    for side in [-1,1]:
        wall_clearance=192 if room['id']=='cave_arrival' else 64
        px=x+side*(room['size'][0]/2-wall_clearance)
        py=y+min(384,room['size'][1]/2-320); pz=z+384
        decoration_name='DECOR_torch_'+room['id']+('_west' if side<0 else '_east')
        torch_z=z+192
        torch=mesh(decoration_name,
                   [([(px-1,py-1,torch_z),(px+1,py-1,torch_z),
                      (px+1,py+1,torch_z),(px-1,py+1,torch_z)],'solid01',(0,0,1))],
                   'decoration_marker',decoration_list_id=298,source_decoration='dec56')
        own(room['id'],torch)
        metadata['entities'].append({'id':decoration_name[6:],'kind':'decoration',
                                    'source_node':decoration_name,'decoration_list_id':298})
        name='LIGHT_'+room['id']+('_west' if side<0 else '_east')
        obj=mesh(name,[([(px-1,py-1,pz),(px+1,py-1,pz),(px+1,py+1,pz),(px-1,py+1,pz)],
                        'solid01',(0,0,1))],'light_marker',radius=640,brightness=31)
        own(room['id'],obj)
        metadata['lights'].append({'id':name[6:],'source_node':name,'color':[192,176,144],
                                   'radius':640,'brightness':31,'type':'point'})

# Native sparse supplies and cave debris retain source art and collision descriptors.
catalog={}
for reference in ['d18','out02']:
    study=json.loads((ROOT/'level_generation/evidence/mm8'/(reference+'_decorations.json')).read_text())
    for entry in study['records']:
        if entry['visible']:catalog.setdefault(entry['name'],entry)
props=[
    ('watch_supply_1','watch_hall','dec03',[-832,3520,768]),
    ('watch_supply_2','watch_hall','dec03',[-832,3664,768]),
    ('armory_supply_1','armory','dec03',[-3712,3472,768]),
    ('armory_supply_2','armory','dec03',[-3584,3472,768]),
    ('barracks_supply_1','barracks','dec03',[9456,3520,384]),
    ('barracks_supply_2','barracks','dec03',[9456,3664,384]),
    ('secret_supply_1','secret','dec03',[8064,5152,384]),
    ('secret_supply_2','secret','dec03',[8064,5296,384]),
    ('cave_bones_1','cave_arrival','dec29',[4848,-2480,0]),
    ('cave_bones_2','cave_arrival','dec29',[6432,-3376,0]),
    ('cave_rock_1','cave_arrival','rock01',[4752,-2816,0]),
    ('cave_rock_2','cave_arrival','rock05',[6544,-2608,0]),
]
for name,room,key,position in props:
    x,y,z=position
    obj=mesh('DECOR_'+name,[([(x-1,y-1,z),(x+1,y-1,z),(x+1,y+1,z),(x-1,y+1,z)],'solid01',(0,0,1))],
             'decoration_marker',decoration_list_id=catalog[key]['id'],source_decoration=key)
    own(room,obj)
    metadata['entities'].append({'id':name,'kind':'decoration','source_node':obj.name,
                                'decoration_list_id':catalog[key]['id']})
decoration_records=[]
for index,entity in enumerate(metadata['entities']):
    obj=scene.objects[entity['source_node']]
    record=dict(catalog[obj['source_decoration']],index=index,semantic_id=entity['id'])
    for key in ['ground_z','ground_offset','grade','nearest_bmodel_xy']:
        record.pop(key,None)
    record['position']=[round(sum(v.co[a] for v in obj.data.vertices)*SCALE/len(obj.data.vertices)) for a in range(3)]
    decoration_records.append(record)
(OUTPUT/'lg02.decorations.json').write_text(json.dumps({'records':decoration_records},indent=2)+'\n')

# Export before adding preview billboards: native markers own entities, never billboard collision meshes.
bpy.ops.export_scene.gltf(filepath=str(OUTPUT/'lg02.glb'),export_format='GLB',use_active_scene=True,
                         export_yup=False,export_cameras=False,export_lights=False,export_apply=True,export_extras=True)
(OUTPUT/'lg02.geometry.yml').write_text(json.dumps(metadata,indent=2)+'\n')
starts=[]
arrivals={}
actors=[]
for obj in scene.objects:
    if obj.get('levelgen_kind') in ('party_start','arrival'):
        position=[round(v*SCALE) for v in obj.location]
        if obj['levelgen_kind']=='party_start':
            starts.append({'start_index':0,'source_name':'StartPoint0','position':position,
                           'direction_degrees':obj['facing_degrees']})
        else:
            arrivals[obj.name[8:]]={'position':position,'direction_degrees':obj['facing_degrees']}
    elif obj.get('levelgen_kind')=='fixed_actor':
        actors.append({'id':obj.name,'position':[round(v*SCALE) for v in obj.location],
                       'room':obj['room'],'monster_id':obj['monster_id']})
source_scene=json.loads((PROJECT/'calibration/calibration.scene.yml').read_text())
source_scene['source']['geometry_file']='lg02.blv'
source_scene['party_start_points']=starts
source_scene['environment']['ceiling']=1536
(OUTPUT/'lg02.scene.yml').write_text(json.dumps(source_scene,indent=2)+'\n')
(OUTPUT/'lg02.semantic.json').write_text(json.dumps({'map':'lg02.blv','arrivals':arrivals,'fixed_actors':actors,
    'rooms':rooms,'connections':connections,'plates':plates,'events':PLAN['events'],
    'status':'geometry authored; gameplay assembly pending'},
    indent=2)+'\n')
sys.path.insert(0,str(ROOT/'level_generation/scripts'))
from blender_native_decorations import add_billboards
add_billboards(scene,decoration_records,ROOT,pack_images=True)
bpy.data.libraries.write(str(OUTPUT/'lg02.blend'),{scene},fake_user=True,compress=True)
print(json.dumps({'objects':len(scene.objects),'sectors':len(metadata['rooms'])+1,
                  'portals':len(metadata['portals']),'mechanisms':len(metadata['mechanisms']),'output':str(OUTPUT)}))
