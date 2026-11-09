"""Run through Blender MCP. Author original native-grid terrain and source-backed BModels.

This is the geometry stage; service registrations/population and final review are separate gates.
Native terrain is exported from the Blender vertex grid, never included in a BModel.
"""
import csv
import heapq
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
import numpy as np

PROJECT = Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
ROOT = PROJECT.parents[2]
SOURCE = PROJECT / 'source'
MODELS = SOURCE / 'lg01_models'
MODELS.mkdir(exist_ok=True)
PLAN = json.loads((PROJECT / 'outdoor_plan.json').read_text())
SCALE = 128
BRIDGE_Z = PLAN['terrain']['bridge']['deck_z']
old = bpy.data.scenes.get('Brackenford calibrated authoring')
scene = bpy.data.scenes.new('Brackenford calibrated authoring')
bpy.context.window.scene = scene
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.scenes.remove(old)
scene.name = 'Brackenford calibrated authoring'
scene['levelgen_project'] = 'brackenford_greywatch'
scene['native_units_per_blender_unit'] = SCALE
textures = {}
for folder in [ROOT/'assets_dev/worlds/mm8/textures', ROOT/'assets_dev/engine/terrain',
               ROOT/'assets_dev/engine/textures']:
    for path in folder.glob('*'):
        if path.suffix.lower() in ['.bmp', '.png']:
            textures.setdefault(path.stem.lower(), path)
materials = {}
sizes = {}


def material(key):
    key = key.lower()
    if key not in materials:
        image = bpy.data.images.load(str(textures[key]), check_existing=True)
        image.pack()
        mat = bpy.data.materials.get('BF_' + key) or bpy.data.materials.new('BF_' + key)
        mat.use_nodes = True
        node = next((n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE'), None)
        if node is None:
            node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        node.interpolation = 'Closest'
        mat.node_tree.links.new(node.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
        materials[key] = mat
        sizes[key] = tuple(image.size)
    return materials[key]


def xy(row, column):
    return (column - 64) * 512, (64 - row) * 512


def cell(x, y):
    return round(63.5-y/512), round(x/512+63.5)


def cell_xy(rc):
    row, column = rc
    return (column-64)*512+256, (64-row)*512-256


Y, X = np.mgrid[0:128, 0:128]
X = (X-64)*512.0
Y = (64-Y)*512.0
height = (896 + 320*np.sin(X/5700) + 288*np.cos(Y/7400)
          + 160*np.sin((X+Y)/3100) + 128*np.sin((X-2*Y)/4300))
height += 2300*np.clip((np.maximum(abs(X),abs(Y))-22000)/10000, 0, 1)**2
height += 1100*np.exp(-((X-15600)/7000)**2-((Y-18000)/5500)**2)
height += 1250*np.exp(-((X-18000)/5200)**2-((Y+13900)/5200)**2)
# Broad authored landforms screen successive destinations; small noise is only secondary relief.
height += 2100*np.exp(-((X+8500)/11500)**2-((Y-13300)/3100)**2)
height += 1850*np.exp(-((X-14600)/2400)**2-((Y-300)/3300)**2)
height += 1800*np.exp(-((X-11200)/2500)**2-((Y+10400)/4700)**2)
height += 1550*np.exp(-((X+23500)/2500)**2-((Y-2800)/2300)**2)
height += 1700*np.exp(-((X+23200)/2600)**2-((Y+5800)/2200)**2)
height += 1800*np.exp(-((X+23500)/3100)**2-((Y-22000)/6500)**2)
height += 1850*np.exp(-((X+12700)/4200)**2-((Y-24500)/5500)**2)


def pad(cx, cy, half_x, half_y, z, feather=1024):
    distance = np.maximum(np.maximum(abs(X-cx)-half_x, abs(Y-cy)-half_y), 0)
    weight = np.clip(1-distance/feather, 0, 1)
    weight = weight*weight*(3-2*weight)
    height[:] = height*(1-weight)+z*weight


# The town rises through broad shelves instead of sharing one flat pad.
town_progress=np.clip(Y/8192,0,1)
town_surface=576+384*town_progress*town_progress*(3-2*town_progress)
# Compact settlement pad leaves natural flanks closer to the last street.
height += 1050*np.exp(-((X+11200)/6500)**2-((Y-6500)/1500)**2)
height += 850*np.exp(-((X+11200)/6200)**2-((Y+8500)/1500)**2)
pad(-11264, -1024, 5632, 4608, town_surface, 1600)
for building in PLAN['buildings']:
    x, y = building['xy']
    progress=max(0,min(1,y/8192))
    z = building.get('elevation',round((576+192*progress*progress*(3-2*progress))/32)*32)
    building['floor_z'] = z
    w, d = building['target_footprint']
    pad(x, y, w/2+256, d/2+384, z, 1536 if building.get('elevation') else 768)
pad(-14336,7936,3072,1536,1536,1792)
pad(15360, 17920, 3072, 3072, 1536, 2048)
pad(15360, -17408, 2048, 1024, 1280, 1536)
pad(-23040, -1536, 3072, 1024, 576, 2500)
pad(-18432, 24400, 1024, 1800, 960, 2200)
# The native hillside meets the rear of the shallow cave facade, while its approach stays clear.
cave_rise=np.clip((Y+17024)/1500,0,1)
cave_rise=cave_rise*cave_rise*(3-2*cave_rise)
height += 1500*np.exp(-((X-15360)/2400)**2-((Y+14000)/4000)**2)*cave_rise
# Native terrain flanks enclose a shallow cleft; the event mouth and arrival floor remain exposed.
cleft_flanks=np.clip((abs(X-15360)-384)/768,0,1)
height += 1056*np.exp(-((X-15360)/2000)**2-((Y+16800)/1250)**2)*cleft_flanks

# Water stays at a single native height. A dirt bank separates water from grass.
river_points = sorted(PLAN['terrain']['river_centerline'], key=lambda point: point[1])
river_x = np.interp(Y, [p[1] for p in river_points], [p[0] for p in river_points])
river_distance = abs(X-river_x)
river_weight = np.clip((river_distance-600)/2200, 0, 1)
height = 256 + (height-256)*river_weight
water_corners = river_distance <= 650
height[water_corners] = 256
# The bridge lands on flat banks; terrain stays below the deck in the wet channel.
for bx in [2816, 7936]:
    pad(bx, 256, 256, 1024, BRIDGE_Z, 1536)
height[water_corners] = 256
# Small isolated pond below the northern ridge, at its own native water elevation.
pond_banks=np.zeros_like(water_corners)
for pond in PLAN['terrain'].get('ponds',[]):
    px,py=pond['xy'];rx,ry=pond['radii']
    angle=np.arctan2((Y-py)/ry,(X-px)/rx)
    distance=np.hypot((X-px)/rx,(Y-py)/ry)/(1+.12*np.sin(3*angle)+.07*np.cos(5*angle))
    pond_water=distance<=1
    blend=np.clip((distance-1)/.8,0,1)
    height=pond['water_z']+(height-pond['water_z'])*blend
    height[pond_water]=pond['water_z']
    water_corners|=pond_water
    pond_banks|=distance<1.4
# Grade the actual uphill approach, rather than letting a road texture cross the plateau shoulder.
for a,b in [((-14592,3328,640),(-14592,6528,1536)),((-12288,3328,640),(-12288,2304,832)),
            ((-12288,2304,832),(-13056,1792,1088))]:
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/(dx*dx+dy*dy),0,1)
    distance=np.hypot(X-(a[0]+t*dx),Y-(a[1]+t*dy))
    weight=np.clip((768-distance)/512,0,1)
    height=height*(1-weight)+(a[2]+t*(b[2]-a[2]))*weight
# Fit full-width graded approaches and the complete span to one bridge profile.
# A pair of bank-center pads alone leaves intervening terrain above the deck.
for a,b in [((0,256,896),(3072,256,BRIDGE_Z)),
            ((7680,256,BRIDGE_Z),(10240,256,1536)),
            ((10240,256,1536),(12544,3840,1856))]:
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/(dx*dx+dy*dy),0,1)
    distance=np.hypot(X-(a[0]+t*dx),Y-(a[1]+t*dy))
    weight=np.clip((1792-distance)/768,0,1)
    height=height*(1-weight)+(a[2]+t*(b[2]-a[2]))*weight
# Stone abutments meet broad flat landings before the graded approaches continue.
pad(2560,256,512,1024,BRIDGE_Z,1024)
pad(8192,256,512,1024,BRIDGE_Z,1536)
# All four deck corners, intermediate grid vertices and rail feet clear the ground.
span=(X>=3072)&(X<=7680)&(Y>=-512)&(Y<=1024)
height[span]=np.minimum(height[span],BRIDGE_Z-64)
height[water_corners & (river_distance<=650)]=256
# Travel bounds end play, not scenery. Shape a continuing road cut in the outer terrain apron.
for route in PLAN['regional_exit_scenery']:
    distance=np.full(X.shape,np.inf)
    points=[cell_xy(rc) for rc in route['cells']]
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1]
        t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/(dx*dx+dy*dy),0,1)
        distance=np.minimum(distance,np.hypot(X-a[0]-t*dx,Y-a[1]-t*dy))
    outward=-X if route['id']=='west' else Y
    gate=np.clip((outward-24576)/2048,0,1)
    gate=gate*gate*(3-2*gate)
    floor=route['floor_z']+(route['edge_floor_z']-route['floor_z'])*np.clip((outward-25344)/7424,0,1)
    shoulder=np.clip((distance-640)/1536,0,1)
    shoulder=shoulder*shoulder*(3-2*shoulder)
    cut=floor+3200*shoulder
    influence=gate*np.clip((4096-distance)/1024,0,1)
    height=height*(1-influence)+cut*influence
height = np.clip(np.rint(height/32), 0, 255).astype(np.uint8)

blocked = set()
for building in PLAN['buildings']:
    x, y = building['xy']; w, d = building['local_footprint']
    angle=math.radians(building['rotation_degrees']);co,si=math.cos(angle),math.sin(angle)
    for row in range(128):
        for column in range(128):
            px, py = cell_xy((row, column))
            dx,dy=px-x,py-y
            if abs(co*dx+si*dy) < w/2+160 and abs(-si*dx+co*dy) < d/2+160:
                blocked.add((row, column))
roads = set()
road_paths = []


def road(start, end, name):
    start, end = cell(*start), cell(*end)
    queue = [(0, start)]
    costs = {start: 0}; previous = {}
    while queue:
        _, current = heapq.heappop(queue)
        if current == end:
            break
        for dr, dc in [(-1,0), (0,1), (1,0), (0,-1)]:
            target = (current[0]+dr, current[1]+dc)
            if not (1 <= target[0] < 126 and 1 <= target[1] < 126):
                continue
            if target in blocked and target != end:
                continue
            px, py = cell_xy(target)
            wet = abs(px-float(np.interp(py, [p[1] for p in river_points], [p[0] for p in river_points]))) < 1700
            if wet and abs(py-256) > 1:
                continue
            step = .65 if target in roads else 1
            step += abs(int(height[target])-int(height[current]))/8
            value = costs[current]+step
            if value < costs.get(target, 1e9):
                costs[target] = value; previous[target] = current
                distance = .65*(abs(target[0]-end[0])+abs(target[1]-end[1]))
                heapq.heappush(queue, (value+distance, target))
    assert end in costs, (name, start, end)
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    roads.update(path)
    road_paths.append({'id': name, 'cells': list(reversed(path))})


main_points = PLAN['roads']['main']
for i, (a, b) in enumerate(zip(main_points, main_points[1:])):
    road(a,b,'main_'+str(i))
for spine in PLAN['roads']['street_spines']:
    for i,(a,b) in enumerate(zip(spine['points'],spine['points'][1:])):
        road(a,b,spine['id']+'_'+str(i))
diagonal_tiles={}
r0,c0=PLAN['roads']['diagonal']['first_cell']
for i in range(PLAN['roads']['diagonal']['length']):
    diagonal_tiles[(r0+i,c0+i)]=217
    diagonal_tiles[(r0+i+1,c0+i)]=218
roads.update(diagonal_tiles)
road_paths.append({'id':'slanted_west_street','cells':list(diagonal_tiles)})
for building in PLAN['buildings']:
    if building['approach_kind'] != 'dedicated_lane':
        continue
    x,y = building['xy']; w,d = building['target_footprint']
    theta=math.radians(building['rotation_degrees'])
    normal=(math.sin(theta),-math.cos(theta))
    half_depth=building['local_footprint'][1]/2
    offset=building['door_offset_x']
    destination = (x+normal[0]*(half_depth+384)+math.cos(theta)*offset,
                   y+normal[1]*(half_depth+384)+math.sin(theta)*offset)
    closest = min(roads, key=lambda rc: math.dist(cell_xy(rc),destination))
    road(cell_xy(closest),destination,building['id']+'_lane')
road((12800,4096),(15360,14848),'castle_approach')
# Natural cave, ogre camps and wilderness treasure are reached across open terrain.
road((-19456,-1536),(-18432,15360),'obelisk_walk')
road((-18432,15360),(-18432,25088),'north_pass')
road((-22528,-1536),(-25088,-1536),'west_pass')
for route in PLAN['regional_exit_scenery']:
    path=[]
    for a,b in zip(route['cells'],route['cells'][1:]):
        dr,dc=b[0]-a[0],b[1]-a[1]
        assert dr==0 or dc==0, 'Exit centerline needs cardinal cell segments'
        length=abs(dr)+abs(dc)
        path.extend((a[0]+i*dr//length,a[1]+i*dc//length) for i in range(length))
    path.append(tuple(route['cells'][-1]))
    assert path[0] in roads, 'Exit continuation must join the existing approach'
    roads.update(path)
    road_paths.append({'id':route['id']+'_scenic_continuation','cells':path})

# Dirt at grid corners gives continuous existing grass/dirt edge and corner variants.
dirt = (river_distance < 1900) | pond_banks
# Local worn/exposed soil shapes complement sparse native stone-detail variants.
for patch in PLAN['terrain']['soil_patches']:
    px,py=patch['xy'];rx,ry=patch['radii']
    angle=np.arctan2((Y-py)/ry,(X-px)/rx)
    dirt |= np.hypot((X-px)/rx,(Y-py)/ry) < (1+.16*np.sin(3*angle)+.08*np.cos(5*angle))
grades=np.hypot(*np.gradient(height.astype(float)*32/512))
rock_corners=(height.astype(float)*32>2304)|(grades>.65)
# This native bank has rock/dirt and water/dirt, but no rock/water or rock/road transitions.
# Reserve a dirt strip around the wet corners and the complete road footprint first.
protected=water_corners.copy()
for row,column in roads:
    protected[row:row+2,column:column+2]=True
# A water/grass shoreline also needs the supported dirt transition on both sides of a cell.
wet_padded=np.pad(water_corners,1,mode='edge')
for dr in range(3):
    for dc in range(3):
        dirt |= wet_padded[dr:dr+128,dc:dc+128]
padded=np.pad(protected,1,mode='edge')
for dr in range(3):
    for dc in range(3):
        rock_corners &= ~padded[dr:dr+128,dc:dc+128]
# Native rock/dirt transitions receive a dirt collar before grass/dirt transitions.
padded_rock=np.pad(rock_corners,2,mode='edge')
for dr in range(5):
    for dc in range(5):
        dirt |= padded_rock[dr:dr+128,dc:dc+128]
for row, column in roads:
    px, py = cell_xy((row,column))
    dirt |= (abs(X-px) <= 256) & (abs(Y-py) <= 256)
for b in PLAN['buildings']:
    x,y=b['xy'];w,d=b['target_footprint']
    dirt |= (abs(X-x) <= w/2+128) & (abs(Y-y) <= d/2+128)

# Corner bit order NW, NE, SW, SE. Diagonal saddle cases cannot be represented by this bank.
# Verified against the actual corner pixels of all three native transition banks.
# XNE/XNW/etc carry ONE dirt corner; NE/NW/etc carry THREE, not the reverse.
variants = {0:0, 1:22, 2:20, 4:23, 8:21, 3:18, 5:17, 10:16, 12:19,
            7:14, 11:12, 13:15, 14:13, 15:-1}
dry_corners=~water_corners
nonrock_corners=~rock_corners
for mask in [dirt, dry_corners, nonrock_corners]:
    for _ in range(4):
        changed = False
        for r in range(127):
            for c in range(127):
                corners = [mask[r,c],mask[r,c+1],mask[r+1,c],mask[r+1,c+1]]
                bits = sum(int(v)<<i for i,v in enumerate(corners))
                if bits in (6,9):
                    mask[r:r+2,c:c+2] = True; changed = True
        if not changed:
            break
water_corners=~dry_corners
rock_corners=~nonrock_corners
tiles = np.full((128,128),90,dtype=np.uint8)
for r in range(127):
    for c in range(127):
        wet = water_corners[r:r+2,c:c+2]
        if wet.any():
            bits=sum(int(not wet[dy,dx])<<i for i,(dy,dx) in enumerate([(0,0),(0,1),(1,0),(1,1)]))
            assert bits in variants, ('water saddle',r,c)
            tiles[r,c] = 126+variants[bits] if bits != 15 else 1
        elif rock_corners[r:r+2,c:c+2].any():
            bits=sum(int(nonrock_corners[r+dy,c+dx])<<i for i,(dy,dx) in enumerate([(0,0),(0,1),(1,0),(1,1)]))
            assert bits in variants, ('rock saddle',r,c)
            tiles[r,c] = 162+variants[bits] if bits != 15 else 1
        else:
            bits=sum(int(dirt[r+dy,c+dx])<<i for i,(dy,dx) in enumerate([(0,0),(0,1),(1,0),(1,1)]))
            assert bits in variants, ('dirt saddle',r,c)
            tiles[r,c] = 90+variants[bits] if bits != 15 else 1
# Reference interior detail: real bitmap variants with the same corner material.
# Avoid changing shore/transition/road tiles or arbitrarily rotating native artwork.
rng=np.random.default_rng(930137)
variation=rng.random((128,128))
tiles[(tiles==90)&(variation<.05)]=92  # Grastyl2: irregular dirt and stones within grass.
plain_dirt=tiles==1
tiles[plain_dirt&(variation<.04)]=2   # DIRT1 / DIRT2: sparse embedded stones.
tiles[plain_dirt&(variation>=.04)&(variation<.08)]=4
# Road variant order comes from the current merged MM8 terrain descriptor table.
road_variant = {15:0,5:1,10:2,3:3,9:4,6:5,12:6,7:7,13:8,11:9,14:10,1:13,2:14,4:11,8:12}
for r,c in roads:
    if abs(cell_xy((r,c))[0]-5120) < 2304 and r == cell(0,256)[0]:
        continue
    bits=sum((1<<i) for i,(dr,dc) in enumerate([(-1,0),(0,1),(1,0),(0,-1)]) if (r+dr,c+dc) in roads)
    # The road leaves the mesh; an end-cap here would contradict its regional-travel role.
    if r==0:bits|=1
    if c==0:bits|=8
    tiles[r,c] = diagonal_tiles.get((r,c),198+road_variant.get(bits,0))

grid_vertices = [(float(X[r,c])/SCALE,float(Y[r,c])/SCALE,int(height[r,c])*32/SCALE)
                 for r in range(128) for c in range(128)]
grid_faces=[]
for r in range(127):
    for c in range(127):
        a=r*128+c
        grid_faces.extend([(a,a+128,a+1),(a+1,a+128,a+129)])
mesh=bpy.data.meshes.new('Native 128x128 height samples')
mesh.from_pydata(grid_vertices,[],grid_faces);mesh.update()
terrain=bpy.data.objects.new('TERRAIN_lg01',mesh);scene.collection.objects.link(terrain)
terrain['native_grid_width']=128;terrain['native_spacing']=512;terrain['levelgen_kind']='native_terrain'
terrain['native_height_quantum']=32
terrain['tile_map_hex']=tiles.tobytes().hex().upper()
table={int(row[0]):row for row in csv.reader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t')
       if row and row[0].isdigit()}
palette={}
for raw in sorted(set(int(v) for v in tiles.flat)):
    index=raw if raw<198 else raw-198+414
    key=table[index][1].lower()
    palette[raw]=len(mesh.materials);mesh.materials.append(material(key))
uv=mesh.uv_layers.new(name='Native tile UV')
for i,poly in enumerate(mesh.polygons):
    r,c=divmod(i//2,127);poly.material_index=palette[int(tiles[r,c])]
    points=[(0,1),(0,0),(1,1)] if i%2==0 else [(1,1),(0,0),(1,0)]
    for loop,point in zip(poly.loop_indices,points):uv.data[loop].uv=point


def sample(x,y):
    gx=x/512+64;gy=64-y/512;c=int(gx);r=int(gy);u=gx-c;v=gy-r
    a,b,d,e=[int(height[rr,cc])*32 for rr,cc in [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]]
    return round(a+(b-a)*u+(d-a)*v) if u+v<=1 else round(e+(d-e)*(1-u)+(b-e)*(1-v))


def box(lo,hi,wall,top=None):
    x,y,z=lo;X1,Y1,Z=hi;top=top or wall
    return [([(x,y,z),(x,Y1,z),(X1,Y1,z),(X1,y,z)],wall),
            ([(x,y,Z),(X1,y,Z),(X1,Y1,Z),(x,Y1,Z)],top),
            ([(x,y,z),(X1,y,z),(X1,y,Z),(x,y,Z)],wall),
            ([(X1,y,z),(X1,Y1,z),(X1,Y1,Z),(X1,y,Z)],wall),
            ([(X1,Y1,z),(x,Y1,z),(x,Y1,Z),(X1,Y1,Z)],wall),
            ([(x,Y1,z),(x,y,z),(x,y,Z),(x,Y1,Z)],wall)]


metadata={'version':1,'map_file':'lg01.odm','bmodels':[]}
semantics={'status':'authored geometry and population; full gameplay validation pending','buildings':PLAN['buildings'],
           'roads':road_paths,'arrivals':[],'events':[],'bmodels':[], 'texture_provenance':{}}


def model(name,panels,event=None,explicit_uvs=None):
    vertices=[];faces=[];uvs=[];keys=[]
    for points,key in panels:
        key=key.lower();material(key);keys.append(key)
        faces.append(tuple(range(len(vertices),len(vertices)+len(points))))
        vertices.extend(tuple(value/SCALE for value in p) for p in points)
        normal=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0]))
        dominant=max(range(3),key=lambda axis:abs(normal[axis]));axes=[a for a in range(3) if a!=dominant]
        tw,th=sizes[key]
        if key in ['bdoorb','cr_w128b']:
            assert len(points)==4
            uvs.extend([(0,0),(1,0),(1,1),(0,1)])
        else:
            uvs.extend((p[axes[0]]/(tw*2),p[axes[1]]/(th*2)) for p in points)
    if explicit_uvs is not None:
        assert len(explicit_uvs)==len(uvs)
        uvs=explicit_uvs
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new('BMODEL_'+name,mesh);scene.collection.objects.link(obj)
    obj['levelgen_kind']='bmodel';obj['semantic_id']=name
    unique=list(dict.fromkeys(keys))
    for key in unique:mesh.materials.append(materials[key])
    for poly,key in zip(mesh.polygons,keys):poly.material_index=unique.index(key)
    uv=mesh.uv_layers.new(name='MM8 texels')
    for loop,point in zip(uv.data,uvs):loop.uv=point
    # Read authored Blender geometry/UVs into OBJ. This avoids scene selection/exporter side effects.
    path=MODELS/(name+'.obj')
    lines=['o '+obj.name]
    lines += ['v '+' '.join(str(round(v,7)) for v in vertex.co) for vertex in mesh.vertices]
    lines += ['vt '+' '.join(str(round(v,7)) for v in data.uv) for data in uv.data]
    for poly in mesh.polygons:
        lines.append('usemtl '+unique[poly.material_index])
        lines.append('f '+' '.join(str(mesh.loops[i].vertex_index+1)+'/'+str(i+1) for i in poly.loop_indices))
    path.write_text('\n'.join(lines)+'\n')
    index=len(metadata['bmodels'])
    metadata['bmodels'].append({'geometry_id':'lg01:'+name,'runtime_bmodel_index':index,
      'source':{'asset_path':str(path),'scale':SCALE,'merge_coplanar_faces':False,'preserve_source_winding':True},
      'materials':{'default_texture':unique[0],'remaps':{key:key for key in unique}}})
    semantics['bmodels'].append({'id':name,'index':index,'faces':len(faces)})
    if event is not None:
        obj['event_id']=event
        semantics['events'].append({'id':event,'name':name,'bmodel_index':index,'faces':list(range(len(faces)))})
    return obj


def roof(x0,y0,x1,y1,eave,peak,key='t14b05',hipped=False):
    # Four planar surfaces for a hipped roof; a gable keeps the two end triangles.
    middle=(y0+y1)/2
    inset=min((x1-x0)*.22,(y1-y0)*.3) if hipped else 0
    a,b=(x0+inset,middle,peak),(x1-inset,middle,peak)
    return [([(x0,y0,eave),(x1,y0,eave),b,a],key),
            ([a,b,(x1,y1,eave),(x0,y1,eave)],key),
            ([(x0,y1,eave),(x0,y0,eave),a],key),
            ([(x1,y0,eave),(x1,y1,eave),b],key)]


sys.path.insert(0,str(PROJECT))
import importlib
import brackenford_house_kit
importlib.reload(brackenford_house_kit)
for i,b in enumerate(PLAN['buildings']):
    x,y=b['xy'];d=b['local_footprint'][1]
    kit=brackenford_house_kit.house(b)
    theta=math.radians(b['rotation_degrees']);co=math.cos(theta);si=math.sin(theta)
    def transform(p):
        return (round(x+co*p[0]-si*p[1]),round(y+si*p[0]+co*p[1]),round(p[2]))
    body=[([transform(p) for p in points],key) for points,key in kit['panels']]
    obj=model(b['id'],body,explicit_uvs=kit['uvs'])
    obj['building_form']=b['form'];obj['rotation_degrees']=b['rotation_degrees']
    obj['calibration']=kit['reference_policy']
    model(b['id']+'_door',[([transform(p) for p in kit['door']],kit['door_texture'])],100+i,
          [(0,0),(1,0),(1,1),(0,1)])
    b['door_position']=list(transform((b['door_offset_x'],-d/2-3,kit['door_floor'])))
    b['event_id']=100+i;b['door_outward']=[si,-co];b['approach_yaw']=math.atan2(co,-si)
    b['door_size']=[128,256];b['door_texture']=kit['door_texture']

# Open timber rails and plank deck on stone supports, calibrated against Ravenshore's crossings.
# Keep the walkable deck plane and component identities stable.
model('bridge_deck',box((3072,-256,BRIDGE_Z-64),(7680,768,BRIDGE_Z),'trim9_32','trimd'))
for y in [-256,704]:
    panels=box((3072,y,BRIDGE_Z+160),(7680,y+64,BRIDGE_Z+208),'trim9_32')
    for x in range(3072,7681,512):
        panels+=box((x-32,y,BRIDGE_Z-64),(x+32,y+64,BRIDGE_Z+272),'trim1_16')
    model('bridge_parapet_'+str(y),panels)
for x,end in [(3840,2560),(6144,7680)]:
    panels=box((x,-256,192),(x+256,768,BRIDGE_Z-64),'hhr1p')
    panels+=box((end,-320,384),(end+512,832,BRIDGE_Z),'hhr1p')
    model('bridge_pier_'+str(x),panels)

# New castle composition: four towers, curtain walls, keep and projecting gatehouse.
cx,cy,cz=15360,17920,1536
keep=box((cx-1152,cy-256,cz),(cx+1152,cy+1536,cz+2304),'gcst2-bs')
keep+=box((cx-1216,cy-320,cz+2112),(cx+1216,cy+1600,cz+2240),'gston1wl')
keep+=roof(cx-1280,cy-384,cx+1280,cy+1664,cz+2304,cz+3200,'t14b05',True)
model('castle_keep',keep)
for dx in [-2304,2304]:
    for dy in [-1792,1792]:
        x,y=cx+dx,cy+dy
        panels=box((x-512,y-512,cz-64),(x+512,y+512,cz+1792),'gcst2-bs')
        for sx in [-384,0,384]:
            for sy in [-384,384]:
                panels+=box((x+sx-96,y+sy-96,cz+1792),(x+sx+96,y+sy+96,cz+2048),'gcst2-bs')
        if dy>0:
            panels+=roof(x-448,y-448,x+448,y+448,cz+2048,cz+2816,'t14b05',True)
        panels+=box((x-536,y-536,cz+1536),(x+536,y+536,cz+1664),'gston1wl')
        model('castle_tower_'+str(dx)+'_'+str(dy),panels)
for dx in [-2304,2304]:
    model('castle_side_'+str(dx),box((cx+dx-128,cy-1792,cz),(cx+dx+128,cy+1792,cz+1152),'gcst2-bs'))
model('castle_rear',box((cx-2304,cy+1664,cz),(cx+2304,cy+1920,cz+1152),'gcst2-bs'))
for dx in [-1,1]:
    left,right=(cx-2304,cx-384) if dx<0 else (cx+384,cx+2304)
    model('castle_front_'+str(dx),box((left,cy-1920,cz),(right,cy-1664,cz+1280),'gcst2-bs'))
gatehouse=box((cx-640,cy-2560,cz+768),(cx+640,cy-1280,cz+1664),'gcst2-bs')
gatehouse+=roof(cx-736,cy-2656,cx+736,cy-1184,cz+1664,cz+2240,'t14b05',True)
model('castle_gatehouse',gatehouse)
model('castle_entrance',[([(cx-384,cy-1921,cz),(cx+384,cy-1921,cz),
                          (cx+384,cy-1921,cz+768),(cx-384,cy-1921,cz+768)],'gt002b')],1)

# A faceted, tapered rock outcrop joins the hillside. Shared edge coordinates close the three masses.
x,y,z=15360,-16640,1280
def cave_mass(profile):
    def front_depth(px,pz):
        if abs(px)<=272 and pz<=448:
            return -512
        return round(-352+max(0,pz)*.32+96*math.sin(px/480))
    front=[(x+px,y+front_depth(px,pz),z+pz) for px,pz in profile]
    back=[(x+px,y+768,z+pz-256) for px,pz in profile]
    panels=[([front[0],front[i],front[i+1]],'dirttyl') for i in range(1,len(profile)-1)]
    panels.append((list(reversed(back)),'dirttyl'))
    for i in range(len(profile)):
        j=(i+1)%len(profile)
        panels.extend([([front[i],back[i],back[j]],'dirttyl'),
                       ([front[i],back[j],front[j]],'dirttyl')])
    return panels
model('cave_left',cave_mass([(-768,-128),(-272,-128),(-192,448),(-448,704),(-704,448)]))
model('cave_right',cave_mass([(272,-128),(768,-128),(704,416),(448,704),(192,448)]))
model('cave_brow',cave_mass([(-192,448),(192,448),(448,704),(0,768),(-448,704)]))
mouth=[(-256,0),(256,0),(192,448),(-192,448)]
model('cave_entrance',[([(x+px,y-514,z+pz) for px,pz in mouth],'solid01')],2)

# Small MM8 props retain their original geometry/UVs, placed in an original landscape.
# Whole reference settlements/dungeons are never imported by the authoring build.
sys.path.insert(0,str(PROJECT))
import importlib
import build_outdoor_content
importlib.reload(build_outdoor_content)
content=build_outdoor_content.build(samples=height.ravel().tolist(),semantics=semantics)
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
reference_models=parse_odm_file(ROOT/'assets_dev/worlds/mm8/maps/out02.odm')['payload']['bmodels']
for prop in content['landmarks']:
    originals=[reference_models[i] for i in prop.get('reuse_bmodels',[prop.get('reuse_bmodel')])]
    original_vertices=[v for original in originals for v in original['vertices']]
    center=[(min(v[k] for v in original_vertices)+max(v[k] for v in original_vertices))/2 for k in 'xy']
    center.append(min(v['z'] for v in original_vertices))
    offset=[p-c for p,c in zip(prop['position'],center)]
    panels=[];coords=[]
    for original,face in [(o,f) for o in originals for f in o['faces']]:
        points=[tuple(original['vertices'][i][key]+offset[axis] for axis,key in enumerate('xyz'))
                for i in face['vertex_indices']]
        key=face['texture_name'].lower();material(key);tw,th=sizes[key]
        panels.append((points,key))
        coords.extend(((u+face['texture_delta_u'])/tw,1-(v+face['texture_delta_v'])/th)
                      for u,v in zip(face['texture_us'],face['texture_vs']))
    obj=model(prop['id'],panels,prop['event_id'],coords)
    obj['levelgen_kind']=prop['kind']
    obj['reuse_source']='mm8/out02.odm:bmodel:'+str(prop.get('reuse_bmodels',prop.get('reuse_bmodel')))
    prop['bmodel_index']=len(metadata['bmodels'])-1
semantics['content_landmarks']=content['landmarks']
semantics['fixed_actors']=content['markers']
semantics['loose_items']=content['world_items']
for marker in content['markers']:
    obj=bpy.data.objects.new('ACTOR_'+marker['id'],None);scene.collection.objects.link(obj)
    obj.location=tuple(p/SCALE for p in marker['position']);obj.empty_display_type='ARROWS'
    obj['levelgen_kind']='fixed_actor';obj['semantic_id']=marker['id'];obj['monster_id']=marker['monster_id']
    obj['actor_index']=marker['actor_index']
for item in content['world_items']:
    obj=bpy.data.objects.new('ITEM_'+item['source_id'],None);scene.collection.objects.link(obj)
    obj.location=tuple(item['position'][k]/SCALE for k in 'xyz');obj.empty_display_type='SPHERE'
    obj['levelgen_kind']='loose_item';obj['item_id']=item['item_id'];obj['semantic_id']=item['source_id']

for a in PLAN['arrivals']:
    x,y=a['xy'];z=sample(x,y)
    marker=bpy.data.objects.new('ARRIVAL_'+a['id'],None);scene.collection.objects.link(marker)
    marker.location=(x/SCALE,y/SCALE,z/SCALE);marker.empty_display_type='ARROWS'
    marker['levelgen_kind']='party_start' if a['id']=='default' else 'travel_arrival'
    semantics['arrivals'].append({'id':a['id'],'position':[x,y,z],'yaw':0})
semantics['terrain']={'width':128,'spacing':512,'height_quantum':32,'height_range':[int(height.min())*32,int(height.max())*32],
                       'native_tile_ids':sorted(palette),'bridge_deck_z':BRIDGE_Z,'water_z':256,'ponds':PLAN['terrain'].get('ponds',[])}
semantics['texture_provenance']={key:str(textures[key].relative_to(ROOT)) for key in materials}

import build_outdoor_decorations
importlib.reload(build_outdoor_decorations)
decorations=build_outdoor_decorations.build(height.ravel().tolist(),tiles.ravel().tolist(),semantics,content)
sys.path.insert(0,str(ROOT/'level_generation/scripts'))
from blender_native_decorations import add_billboards
add_billboards(scene,decorations['records'],ROOT,pack_images=True)
semantics['decorations']={'source':'lg01.decorations.json','counts':decorations['counts'],
                         'representation':'native ODM entities; Blender billboards are previews only'}

# Serialization reads the Blender grid, with explicit native range/quantization checks.
native_heights=[]
for i,vertex in enumerate(terrain.data.vertices):
    r,c=divmod(i,128);expected=xy(r,c)
    assert all(abs(vertex.co[a]*SCALE-expected[a])<.01 for a in range(2))
    native_z=round(vertex.co.z*SCALE)
    assert native_z%32==0 and 0<=native_z//32<=255
    native_heights.append(native_z//32)
terrain_meta={'version':1,'map_file':'lg01.odm','height_map_hex':bytes(native_heights).hex().upper(),
              'tile_map_hex':terrain['tile_map_hex'],'attribute_map_hex':bytes(128*128).hex().upper()}
for name,data in [('lg01.terrain.yml',terrain_meta),('lg01.geometry.yml',metadata),('lg01.semantic.json',semantics)]:
    (SOURCE/name).write_text(json.dumps(data,indent=2)+'\n')
bpy.data.libraries.write(str(SOURCE/'lg01.blend'),{scene},fake_user=True,compress=True)
print(json.dumps({'scene':scene.name,'bmodels':len(metadata['bmodels']),'road_cells':len(roads),
                  'buildings':len(PLAN['buildings']),'terrain':semantics['terrain']}))
