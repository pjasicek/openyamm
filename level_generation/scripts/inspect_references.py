#!/usr/bin/env python3
"""Read-only source inspection; write reproducible evidence, never modify game assets.

Run from any directory: python3 level_generation/scripts/inspect_references.py
Requires numpy, matplotlib, Pillow and PyYAML. Uses OpenYAMM's own diagnostic parser.
The MM8 sector counts are decoded with the runtime's corrected offsets. ODM model
bounds are computed from vertices: the old diagnostic parser's header bounds are not used.
"""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
import numpy as np
from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[2]
STUDY_ROOT = ROOT / 'level_generation'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file, parse_odm_file

FLAGS = {'secret': 2, 'invisible': 0x2000, 'animated': 0x4000,
         'clickable': 0x02000000, 'pressure_plate': 0x04000000,
         'trigger_monster': 0x08000000, 'trigger_object': 0x10000000}

def relative(path):
    return str(path.relative_to(ROOT))

def sourceInfo(path):
    return {'path': relative(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def eventsFromLua(path):
    # Legacy STR-derived Lua may retain single-byte glyphs; scan ASCII syntax losslessly.
    text = path.read_text(encoding='latin-1')
    events = {}
    # Exported registrations start at column 0; stop at the next registration.
    matches = list(re.finditer(r'^Register(?:NoOp)?Event\((\d+),', text, re.M))
    for i, match in enumerate(matches):
        block = text[match.start():matches[i+1].start() if i+1 < len(matches) else len(text)]
        events[int(match[1])] = {
            'line': text.count('\n', 0, match.start()) + 1,
            'calls': sorted(set(re.findall(r'evt\.(\w+)\(', block))),
            'chests': sorted(set(map(int, re.findall(r'evt\.OpenChest\((\d+)', block)))),
            'houses': sorted(set(map(int, re.findall(r'evt\.EnterHouse\((\d+)', block)))),
            'doors': sorted(set(map(int, re.findall(r'evt\.SetDoorState\((\d+)', block)))),
            'destinations': sorted(set(re.findall(r'"([^"\n]+\.(?:blv|odm))"', block))),
        }
    return events

def tableRow(filename):
    for lineNumber, line in enumerate((ROOT / 'assets_dev/engine/data_tables/map_stats.txt').read_text().splitlines(), 1):
        row = line.split('\t')
        if len(row) > 28 and row[2].lower() == filename.lower():
            return {'id': int(row[0]), 'name': row[1], 'line': lineNumber,
                    'perception': int(row[5]), 'refill_days': int(row[6]),
                    'disarm': int(row[9]), 'trap_d20': int(row[10]), 'treasure': int(row[11]),
                    'encounter_chance': int(row[12]), 'music': row[28],
                    'encounters': [{'name': row[17+4*i], 'difficulty': row[18+4*i],
                                    'count': row[19+4*i].strip(), 'weight': int(row[13+i])} for i in range(3)]}
    raise ValueError('No map_stats row: ' + filename)

def referenceScript(world, stem):
    alias = re.sub(r'^[67](?=(?:d|t|out)\d)', '', stem)
    folder = ROOT / 'reference/mmext-scripts/Decompiled_Scripts' / (world + 'orig') / 'txt'
    return next((p for p in folder.glob('*.txt') if p.stem.lower() == alias.lower()), None)

def positions(records):
    return np.asarray([[r['position'][a] for a in 'xyz'] for r in records], dtype=float).reshape(-1,3)

def drawMarkers(ax, p, summary, kind):
    if p['spawns']:
        xyz = positions(p['spawns']) / 1000
        ax.scatter(xyz[:,0], xyz[:,1], marker='x', s=9, c='#a33142', alpha=.55, label='Spawn records')
    if kind == 'indoor' and p['lights']:
        xyz = np.array([[v[a] for a in 'xyz'] for v in p['lights']]) / 1000
        ax.scatter(xyz[:,0], xyz[:,1], s=9, c='#e2a52e', label='Explicit lights')
    for entry in summary['bound_events']:
        if 'position' not in entry or not any(c in entry['calls'] for c in ['EnterHouse', 'MoveToMap', 'OpenChest']):
            continue
        x,y,z = np.array(entry['position']) / 1000
        ax.scatter([x],[y],s=15,c='#2059a0',marker='s')
        if kind == 'indoor' and len(summary['bound_events']) < 35:
            ax.annotate(str(entry['id']), (x,y), xytext=(3,3),textcoords='offset points',fontsize=6)

def indoorPlot(p, summary, target):
    v = np.array([[x[a] for a in 'xyz'] for x in p['vertices']], dtype=float) / 1000
    fig, ax = plt.subplots(figsize=(8,8))
    polys, colors, edges = [], [], []
    for f in p['faces']:
        ids = f['vertex_indices']
        if len(ids) < 3 or f['is_portal'] or f['facet_type'] in (5,6):
            continue
        points = v[ids,:2]
        if f['facet_type'] in (3,4):
            polys.append(points)
            colors.append(plt.get_cmap('Pastel1')(f['room_number'] % 9))
        edges.extend(zip(points, np.roll(points,-1,axis=0)))
    ax.add_collection(PolyCollection(polys,facecolors=colors,edgecolors='none',alpha=.7))
    ax.add_collection(LineCollection(edges,colors='#64717c',linewidths=.25,alpha=.5))
    portalLines = []
    for f in p['faces']:
        if f['is_portal']:
            points = v[f['vertex_indices'],:2]
            portalLines.extend(zip(points,np.roll(points,-1,axis=0)))
    ax.add_collection(LineCollection(portalLines,colors='#17a7a0',linewidths=1.2))
    drawMarkers(ax,p,summary,'indoor')
    ax.autoscale()
    ax.set_aspect('equal')
    ax.margins(.07)
    ax.set_title(summary['map_stats']['name'] + '\n' + summary['world'] + '/' + summary['map'] +
                 ' — floor/wall projection; ceiling omitted', fontsize=11)
    ax.set_xlabel('X / 1000 game units')
    ax.set_ylabel('Y / 1000 game units')
    ax.grid(alpha=.12)
    fig.tight_layout()
    fig.savefig(target,dpi=130)
    plt.close(fig)

def terrainPalette(p, world):
    filename = {'mm6':'terrain_tile_data_3.txt','mm7':'terrain_tile_data_2.txt','mm8':'terrain_tile_data.txt'}[world]
    rows = [line.split('\t') for line in (ROOT / 'assets_dev/engine/data_tables' / filename).read_text().splitlines()[1:]]
    result = {}
    for tile in set(p['tile_map']):
        if tile >= 234:
            result[tile] = {'texture':'pending', 'flags':0, 'descriptor':None}
            continue
        if tile >= 90:
            idx = p['tile_set_lookup_indices'][(tile-90)//36] + (tile-90)%36
        else:
            idx = tile + ([0,450,630][p['master_tile']] if world == 'mm8' and tile else 0)
        row = rows[idx]
        result[tile] = {'texture':row[1].lower(), 'flags':int(row[6],0), 'descriptor':idx}
    return result

def outdoorPlot(p, summary, target):
    palette = summary['terrain']['palette']
    textures = {}
    # Namespaced imports retain their normal world ownership; try local then engine.
    for folder in [ROOT / 'assets_dev/engine/terrain', ROOT / 'assets_dev/engine/textures',
                   ROOT / 'assets_dev/worlds' / summary['world'] / 'terrain',
                   ROOT / 'assets_dev/worlds' / summary['world'] / 'textures']:
        if folder.exists():
            textures.update({f.stem.lower(): f for f in folder.glob('*') if f.suffix.lower() in ('.bmp','.png')})
    tiles = {}
    missing = []
    waterRows = (ROOT / 'assets_dev/engine/data_tables/hw_water_textures.txt').read_text().splitlines()[1:]
    waterAliases = dict(line.split('\t')[:2] for line in waterRows if '\t' in line)
    waterCounts = Counter(p['tile_map'])
    waterTiles = [t for t in palette if palette[t]['flags'] & 2 and not palette[t]['flags'] & 0x100]
    waterColor = np.array([50, 75, 100], dtype=np.uint8)
    if waterTiles:
        waterName = palette[max(waterTiles,key=lambda t:waterCounts[t])]['texture']
        waterName = waterAliases[waterName]+'000' if waterName in waterAliases else waterName
        if waterName in textures:
            with Image.open(textures[waterName]) as water:
                waterColor = np.array(water.convert('RGB').resize((1,1),Image.BOX))[0,0]
    for tile, info in palette.items():
        textureName = info['texture']
        if textureName in waterAliases:
            textureName = waterAliases[textureName] + '000'
            info['preview_texture'] = textureName
        path = textures.get(textureName)
        if path:
            with Image.open(path) as image:
                rgb = np.array(image.convert('RGB'))
                key = (rgb[:,:,0]>=248)&(rgb[:,:,1]<=8)&(rgb[:,:,2]>=248)
                # Diagnostic shore composition, not an emulation of the runtime water shader.
                rgb[key] = waterColor
                tiles[tile] = np.array(Image.fromarray(rgb).resize((8,8), Image.BOX))
        else:
            tiles[tile] = np.full((8,8,3), [165,80,165],dtype=np.uint8)
            missing.append(info['texture'])
    canvas = np.zeros((1024,1024,3),dtype=np.uint8)
    for y in range(128):
        for x in range(128):
            canvas[y*8:y*8+8,x*8:x*8+8] = tiles[p['tile_map'][y*128+x]]
    heights = np.array(p['height_map']).reshape(128,128)*32
    fig, axes = plt.subplots(1,2,figsize=(13,6.5))
    extent = (-32.768,32.768,-32.768,32.768)
    axes[0].imshow(canvas,extent=extent,origin='upper')
    axes[0].set_title('Resolved tile textures + BModel footprints / POIs')
    plot = axes[1].imshow(heights,extent=extent,origin='upper',cmap='terrain',vmin=0,vmax=8160)
    axes[1].set_title('Native height samples; Z in game units')
    fig.colorbar(plot,ax=axes[1],shrink=.65)
    edges = []
    for model in p['bmodels']:
        v = np.array([[x[a] for a in 'xyz'] for x in model['vertices']],dtype=float)/1000
        for f in model['faces']:
            points = v[f['vertex_indices'],:2]
            edges.extend(zip(points,np.roll(points,-1,axis=0)))
    axes[0].add_collection(LineCollection(edges,colors='#191919',linewidths=.25,alpha=.8))
    drawMarkers(axes[0],p,summary,'outdoor')
    for ax in axes:
        ax.set_xlabel('X / 1000 game units')
        ax.set_ylabel('Y / 1000 game units')
        ax.set_xlim(-32.768,32.768)
        ax.set_ylim(-32.768,32.768)
    fig.suptitle(summary['map_stats']['name'] + ' — ' + summary['world'] + '/' + summary['map'])
    fig.tight_layout()
    fig.savefig(target,dpi=115)
    plt.close(fig)
    summary['terrain']['missing_preview_textures'] = sorted(set(missing))

def inspect(kind, world, stem):
    extension = '.blv' if kind == 'indoor' else '.odm'
    mapPath = ROOT / 'assets_dev/worlds' / world / 'maps' / (stem+extension)
    scenePath = mapPath.with_suffix('.scene.yml')
    luaPath = ROOT / 'assets_dev/worlds' / world / 'events/maps' / (stem+'.lua')
    p = (parse_blv_file if kind == 'indoor' else parse_odm_file)(mapPath)['payload']
    scene = yaml.load(scenePath.read_text(),Loader=yaml.CSafeLoader)
    state = scene['initial_state']
    events = eventsFromLua(luaPath)
    refs = [sourceInfo(path) for path in [mapPath,scenePath,luaPath,
            ROOT / 'assets_dev/engine/data_tables/map_stats.txt']]
    if kind == 'outdoor':
        tableSuffix = {'mm6': '_3', 'mm7': '_2', 'mm8': ''}[world]
        refs.append(sourceInfo(ROOT / ('assets_dev/engine/data_tables/terrain_tile_data' + tableSuffix + '.txt')))
    refScript = referenceScript(world,stem)
    if refScript:
        refs.append(sourceInfo(refScript))
    overlays = sorted(luaPath.parent.glob(stem+'_*.lua'))
    refs.extend(sourceInfo(path) for path in overlays)
    summary = {'kind':kind, 'world':world, 'map':stem+extension, 'sources':refs,
               'map_stats':tableRow(stem+extension), 'source_version':p['version'],
               'scene_counts':{k:len(v) for k,v in state.items() if isinstance(v,list)},
               'entities':len(p['entities']), 'spawn_records':len(p['spawns']),
               'decorations':Counter(e['name'] for e in p['entities']),
               'unique_actors':[{k:a.get(k) for k in ['actor_index','name','monster_id','unique_name_index',
                                                    'carried_item_id','hp','group','position']}
                                for a in state['actors'] if a.get('unique_name_index') or a.get('carried_item_id')],
               'declared_event_count':len(events)}
    if kind == 'indoor':
        faces = p['faces']
        for f in faces:
            f['event_id'] = (f['face_param'] or {}).get('cog_triggered',0)
            f['position'] = np.array([[p['vertices'][i][a] for a in 'xyz'] for i in f['vertex_indices']]).mean(axis=0).tolist() if f['vertex_indices'] else [0,0,0]
        sectors = []
        for sector in p['sectors']:
            raw = base64.b64decode(sector['raw_record_base64'])
            shift = 4 if p['version'] == 8 else 0
            fields = {key:struct.unpack_from('<H',raw,offset+shift)[0]
                      for key,offset in [('floors',4),('walls',12),('ceilings',20),('portals',36),('faces',44)]}
            fields['ambient'] = struct.unpack_from('<h',raw,0x62+shift)[0]
            sectors.append(fields)
        summary.update({'vertices':len(p['vertices']), 'faces':len(faces), 'sectors':sectors,
                        'occupied_sectors':sum(s['faces']>0 for s in sectors),
                        'portal_faces':sum(f['is_portal'] for f in faces), 'outlines':len(p['outlines']),
                        'bsp_nodes':len(p['bsp_nodes']), 'lights':len(p['lights']),
                        'light_radius_range':[min((v['radius'] for v in p['lights']),default=0),
                                              max((v['radius'] for v in p['lights']),default=0)],
                        'facet_types':Counter(f['facet_type'] for f in faces)})
        vertices = np.array([[v[a] for a in 'xyz'] for v in p['vertices']])
        summary['bounds'] = [vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()]
        doorData = state.get('doors',[])
        summary['doors'] = [{k:v for k,v in d.items() if not isinstance(v,(list,dict))} for d in doorData]
    else:
        faces = []
        for model in p['bmodels']:
            for f in model['faces']:
                f['event_id'] = f['cog_triggered_number']
                f['position'] = np.array([[model['vertices'][i][a] for a in 'xyz'] for i in f['vertex_indices']]).mean(axis=0).tolist() if f['vertex_indices'] else [0,0,0]
                faces.append(f)
        palette = terrainPalette(p,world)
        counts = Counter(p['tile_map'])
        summary.update({'bmodels':len(p['bmodels']), 'faces':len(faces),
                        'bmodel_names':[m['name'] for m in p['bmodels']],
                        'terrain':{'height_range':[min(p['height_map'])*32,max(p['height_map'])*32],
                                   'master_tile':p['master_tile'], 'lookup':p['tile_set_lookup_indices'],
                                   'unique_tiles':len(counts), 'palette':palette,
                                   'tile_counts':counts,
                                   'road_bank_cells':sum(c for t,c in counts.items() if 198<=t<234),
                                   'water_flag_cells':sum(c for t,c in counts.items() if palette[t]['flags']&2),
                                   'burn_flag_cells':sum(c for t,c in counts.items() if palette[t]['flags']&1)}})
        assert len(p['height_map']) == len(p['tile_map']) == len(p['attribute_map']) == 16384
    summary['face_flags'] = {name:sum(bool(f['attributes']&mask) for f in faces) for name,mask in FLAGS.items()}
    summary['textures'] = dict(Counter(f['texture_name'] for f in faces).most_common())
    bound = Counter(f['event_id'] for f in faces if f['event_id'])
    bound.update(e['event_id_secondary'] for e in p['entities'] if e['event_id_secondary'])
    summary['bound_events'] = []
    for eventId,count in sorted(bound.items()):
        entry = {'id':eventId,'binding_count':count,**events.get(eventId,{'calls':[],'unresolved':True})}
        coords = [f['position'] for f in faces if f['event_id']==eventId]
        coords += [[e['position'][a] for a in 'xyz'] for e in p['entities'] if e['event_id_secondary']==eventId]
        if coords:
            entry['position'] = np.mean(coords,axis=0).tolist()
        summary['bound_events'].append(entry)
    summary['bound_chest_slots'] = sorted({c for e in summary['bound_events'] for c in e.get('chests',[])})
    summary['bound_door_ids'] = sorted({d for e in summary['bound_events'] for d in e.get('doors',[])})
    summary['bound_call_counts'] = Counter(c for e in summary['bound_events'] for c in e['calls'])
    target = STUDY_ROOT / 'evidence' / world
    target.mkdir(parents=True,exist_ok=True)
    (indoorPlot if kind == 'indoor' else outdoorPlot)(p,summary,target/(stem+'.png'))
    (target/(stem+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
    print(f"{world}/{stem}: {summary['map_stats']['name']}; faces={len(faces)}; "
          f"bound events={len(bound)}; chests={summary['bound_chest_slots']}",flush=True)
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world',choices=['mm6','mm7','mm8'])
    parser.add_argument('--kind',choices=['indoor','outdoor'])
    parser.add_argument('--map',dest='mapName')
    args = parser.parse_args()
    manifest = json.loads((STUDY_ROOT/'reference_maps.json').read_text())
    summaries = []
    for kind, worlds in manifest.items():
        if args.kind and args.kind != kind:
            continue
        for world, maps in worlds.items():
            for name in maps:
                if (args.world and args.world != world) or (args.mapName and args.mapName != name):
                    continue
                summaries.append(inspect(kind,world,name))
    if not summaries:
        raise SystemExit('No reference map matches the requested filter')

if __name__ == '__main__':
    main()
