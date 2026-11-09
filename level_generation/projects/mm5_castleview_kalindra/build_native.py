"""Build the current MM5 source checkpoint in an explicitly isolated composed base.

Early checkpoints may contain only reviewed prototypes. Counts and missing content are
reported honestly; this command is not the final environment acceptance gate.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SOURCE = PROJECT / 'implementation/source'
RUNTIME = PROJECT / 'implementation/runtime/worlds/mm5'
REVIEW = PROJECT / 'review/native'
MAP_ID = 13001
TERRAIN_BASE = 882


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def table_rows(path):
    with path.open(newline='') as stream:
        return list(csv.reader(stream, delimiter='\t'))


def save_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        csv.writer(stream, delimiter='\t', lineterminator='\n').writerows(rows)


def mirror_base(source, target):
    """Mount whole art/map directories; copy only mutable registry/config files."""
    target.mkdir(parents=True, exist_ok=True)
    mounted = {'icons', 'textures', 'sprites', 'audio', 'music', 'videos', 'terrain', 'maps', 'events'}
    for child in source.iterdir():
        destination = target / child.name
        if child.is_dir():
            if child.name in mounted:
                if destination.exists():
                    assert destination.is_symlink() and destination.resolve() == child.resolve(), destination
                else:
                    destination.symlink_to(child.resolve(), target_is_directory=True)
            else:
                mirror_base(child, destination)
        elif not destination.exists():
            shutil.copy2(child, destination)


def prepare_terrain(assets):
    rows = table_rows(ROOT / 'assets_dev/engine/data_tables/terrain_tile_data.txt')
    indexed = {int(row[0]): row for row in rows[1:] if row[0].isdigit()}
    assert list(indexed) == list(range(TERRAIN_BASE)), 'Terrain registry changed; reallocate contiguous appended rows'
    assert not any(TERRAIN_BASE <= index < TERRAIN_BASE + 144 for index in indexed)
    unique = {}
    # Collect actual bitmap/flag combinations, rather than spending whole banks on
    # duplicate base tiles. All appended rows belong to the isolated global registry.
    for index in [1, 2, 4, 450] + [i for start in [90, 126, 306, 594, 414] for i in range(start, start+36)]:
        row = indexed[index]
        if row[1] and row[1] != 'pending':
            unique.setdefault(row[1].lower(), list(row))
    for key in ['7sand', 'mm5void', 'rcsw']:
        unique[key] = ['0', key, '0', '0', '4', '0', '0x0000']
    unique['rcsw'] = ['0', 'rcsw', '0', '0', '6', '15', '0x0200']
    from terrain_materials import append_rows, prepare as prepare_materials
    append_rows(unique, indexed)
    prepare_materials(assets, RUNTIME, indexed)
    assert len(unique) <= 144
    palette = {}
    additions = []
    for offset, (name, row) in enumerate(unique.items()):
        row[0] = str(TERRAIN_BASE + offset)
        row[1] = name
        additions.append(row)
        palette[name] = 90 + offset
    # Unused bank slots are explicitly reserved, not reachable fallback selectors.
    for offset in range(len(additions), 144):
        additions.append([str(TERRAIN_BASE+offset), '', '0', '0', '255', '255', '0x0040'])
    save_rows(assets / 'engine/data_tables/terrain_tile_data.txt', rows + additions)
    save_rows(PROJECT / 'implementation/terrain_rows.tsv', [rows[0]] + additions)
    classes = list(Image.open(PROJECT / 'landscape/surface_classes.png').getdata())
    materials = {0:'mm5void',1:'grastyl',2:'dirttyl',3:'wtrtyl',4:'mm5acid',5:'7sand',8:'voltyl',10:'rctyl'}
    assert set(classes) <= materials.keys()
    from terrain_tiles import assign
    native_tiles = assign(palette, indexed)
    heights = (PROJECT / 'landscape/heightmap.raw').read_bytes()
    assert len(heights) == len(native_tiles) == 16384
    metadata = {'version':1,'map_file':'mm5_sw.odm','height_map_hex':heights.hex().upper(),
                'tile_map_hex':native_tiles.hex().upper(),'attribute_map_hex':bytes(16384).hex().upper()}
    write(SOURCE / 'mm5_sw.terrain.yml', metadata)
    write(PROJECT / 'implementation/terrain_palette.json', {
        'status':'all material families assigned, including authored sand joins and separate Acid Pond',
        'baseTableSha256':hashlib.sha256((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').read_bytes()).hexdigest(),
        'lookupBases':[TERRAIN_BASE + i*36 for i in range(4)],'localTileByTexture':palette,
        'surfaceClassMaterial':materials,'usedLocalTiles':sorted(set(native_tiles)),
        'padding':'unused slots reserved with pending flags; no terrain samples select them'})
    return metadata


def build(stage):
    marker = stage / 'mm5-stage.json'
    if stage.exists() and any(stage.iterdir()):
        assert marker.exists() and json.loads(marker.read_text())['project'] == 'mm5_castleview_kalindra'
    write(marker, {'project':'mm5_castleview_kalindra','base':str(ROOT/'assets_dev')})
    assets = stage / 'assets_dev'
    mirror_base(ROOT / 'assets_dev', assets)
    for folder in ['maps', 'events/maps', 'textures']:
        (RUNTIME / folder).mkdir(parents=True, exist_ok=True)
    world = {'id':'mm5','name':'MM5 — Darkside of Xeen','sourceGame':'mm8',
             'dependencies':['mm8','mm7'],'start':{'map':'mm5_sw.odm'}}
    (RUNTIME / 'world.yml').write_text(yaml.safe_dump(world, sort_keys=False, allow_unicode=True))
    from stage_script_policy import stage_policy
    stage_policy(stage)
    terrain = prepare_terrain(assets)
    semantics = json.loads((SOURCE / 'mm5_sw.semantic.json').read_text())
    for name, expected in semantics['world_rim']['sourceSha256'].items():
        assert hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() == expected, ('Stale rim source', name)
    Image.new('RGBA', (128,128), (0,0,0,0)).save(RUNTIME / 'textures/mm5void.png')
    # Native BModel texture names occupy exactly ten bytes. Reject lossy names before export.
    for key in semantics['texture_provenance']:
        assert key.isascii() and len(key.encode('ascii'))<=10, ('Native texture name exceeds ten bytes',key)
    from prepare_scenery import prepare as prepare_scenery
    scenery=prepare_scenery()
    plan = json.loads((PROJECT / 'layout.json').read_text())
    start_x, start_y = plan['defaultArrival']['point']
    height = bytes.fromhex(terrain['height_map_hex'])
    start_z = height[round(64-start_y/512)*128 + round(start_x/512+64)]*32
    start_facing={'east':0,'north':90,'west':180,'south':270}[plan['defaultArrival']['facing']]
    environment = {'sky_texture':'','ground_tileset_name':'','master_tile':0,
                   'tile_set_lookup_indices':[TERRAIN_BASE+i*36 for i in range(4)],
                   'day_bits_raw':0,'map_extra_bits_raw':0,'flags':{
                       'foggy':False,'raining':False,'snowing':False,'underwater':False,'no_terrain':False,
                       'always_dark':False,'always_light':False,'always_foggy':False,'red_fog':False},
                   'fog':{'weak_distance':0,'strong_distance':0},'ceiling':0}
    scene = {'format_version':1,'kind':'outdoor_scene','source':{'geometry_file':'mm5_sw.odm'},
             'environment':environment,'terrain':{'attribute_overrides':[],'footstep_sound_overrides':[]},
             'bmodel_faces':{'interactive_faces':[]},'entities':[], 'spawns':[],
             'initial_state':{'location':{'respawn_count':0,'last_respawn_day':0,'reputation':0,'alert_status':0},
                              'face_attribute_overrides':[],'actors':[],'sprite_objects':[],'chests':[],
                              'variables':{'map':[0]*75,'decor':[0]*125}}}
    scene['entities'].append({'entity_index':0,'name':'Party Start','decoration_list_id':13,'ai_attributes':2,
        'position':dict(zip('xyz',[start_x,start_y,start_z])),'facing':start_facing,
        'event_id_primary':0,'event_id_secondary':0,
        'variable_primary':0,'variable_secondary':0,'special_trigger':0,'initial_decoration_flag':2})
    for record in scenery['records']:
        scene['entities'].append({'entity_index':len(scene['entities']),'name':record['name'],
            'decoration_list_id':record['descriptorId'],'ai_attributes':0,
            'position':dict(zip('xyz',record['position'])),'facing':0,
            'event_id_primary':0,'event_id_secondary':record['eventId'],
            'variable_primary':0,'variable_secondary':0,'special_trigger':0,'initial_decoration_flag':0})
    lua = ['-- Authored MM5 environment checkpoint: every interaction is deliberately status-only.',
           'SetMapMetadata({ onLoad = {} })', '']
    for event in semantics['events']:
        for face in event['faces']:
            scene['bmodel_faces']['interactive_faces'].append({
                'bmodel_index':event['bmodel_index'],'face_index':face,
                'legacy_attributes':event.get('legacy_attributes', 0x2000000),
                'cog_number':0,'cog_triggered_number':event['id'],'cog_trigger':0})
    scene['bmodel_faces']['interactive_faces'].extend(semantics['face_overrides'])
    face_ids = [(f['bmodel_index'], f['face_index']) for f in scene['bmodel_faces']['interactive_faces']]
    assert len(face_ids) == len(set(face_ids)), 'Conflicting event and surface face bindings'
    events=semantics['events']+scenery['events']
    assert len({e['id'] for e in events})==len(events),'Local event ID collision'
    for event in events:
        label = event['label']
        lua += [f'RegisterEvent({event["id"]}, {json.dumps(label)}, function()',
                f'    evt.StatusText({json.dumps(label + ": not implemented yet.")})', 'end)', '']
    # Lua strings use UTF-8 text directly; JSON Unicode escapes are not Lua escapes.
    lua = '\n'.join(lua)
    for event in events:
        for value in [event['label'], event['label'] + ': not implemented yet.']:
            lua = lua.replace(json.dumps(value), json.dumps(value, ensure_ascii=False))
    (RUNTIME / 'events/maps/mm5_sw.lua').write_text(lua)
    write(SOURCE / 'mm5_sw.scene.yml', scene)
    package = {'format_version':1,'kind':'outdoor_map_package','package_id':'mm5:sw',
               'display_name':'Castleview and Kalindra','map_file':'mm5_sw.odm','scene_file':'mm5_sw.scene.yml',
               'geometry_metadata_file':'mm5_sw.geometry.yml','terrain_metadata_file':'mm5_sw.terrain.yml',
               'script_module':'maps/mm5_sw.lua','map_stats_id':MAP_ID,'redbook_track':0,
               'environment_name':'grassland','is_top_level_area':True,
               'outdoor_bounds':{'enabled':True,'min_x':-24576,'max_x':24576,'min_y':-24576,'max_y':24576}}
    write(SOURCE / 'mm5_sw.map.yml', package)
    rows = table_rows(ROOT / 'assets_dev/engine/data_tables/map_stats.txt')
    assert not any(row and row[0] == str(MAP_ID) for row in rows), 'Map ID collision'
    record = next(list(row) for row in rows if len(row)>2 and row[2].lower()=='out02.odm')
    record += [''] * max(0,35-len(record))
    record[0:3] = [str(MAP_ID),'Castleview and Kalindra','mm5_sw.odm']
    record[3:28] = ['0'] * 25
    record[6] = '0'
    record[28:35] = ['0','grassland','OpenYAMM','MM5 environment checkpoint','','-','mm5']
    save_rows(assets / 'engine/data_tables/map_stats.txt', rows + [record])
    navigation = table_rows(ROOT / 'assets_dev/engine/data_tables/map_navigation.txt')
    navigation.append(['mm5_sw.odm','-24576','24576','-24576','24576'] + ['0']*12 + ['']*12)
    save_rows(assets / 'engine/data_tables/map_navigation.txt', navigation)
    world_root = assets / 'worlds/mm5'
    world_root.mkdir(parents=True, exist_ok=True)
    for path in RUNTIME.rglob('*'):
        if path.is_file():
            dest = world_root / path.relative_to(RUNTIME)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    REVIEW.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mm5-native-') as temp:
        temp = Path(temp)
        for suffix in ['map.yml','scene.yml','geometry.yml','terrain.yml']:
            shutil.copy2(SOURCE / ('mm5_sw.'+suffix), temp / ('mm5_sw.'+suffix))
        # Freeze OBJ inputs as well as metadata: a later Blender revision must not
        # change the geometry being consumed by an already-running native build.
        geometry = json.loads((temp/'mm5_sw.geometry.yml').read_text())
        source_hashes = {}
        (temp/'models').mkdir()
        for model in geometry['bmodels']:
            source_path = Path(model['source']['asset_path'])
            snapshot = temp/'models'/source_path.name
            shutil.copy2(source_path, snapshot)
            source_hashes[source_path.name] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            model['source']['asset_path'] = str(snapshot)
        write(temp/'mm5_sw.geometry.yml', geometry)
        with (REVIEW / 'build.log').open('w') as log:
            subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(assets),'--world','mm5',
                            '--headless-build-map',str(temp/'mm5_sw.map.yml')],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
        shutil.copy2(temp/'mm5_sw.odm',RUNTIME/'maps/mm5_sw.odm')
    shutil.copy2(SOURCE/'mm5_sw.scene.yml', RUNTIME/'maps/mm5_sw.scene.yml')
    for name in ['mm5_sw.odm','mm5_sw.scene.yml']:
        (world_root/'maps').mkdir(exist_ok=True)
        shutil.copy2(RUNTIME/'maps'/name,world_root/'maps'/name)
    sys.path.insert(0,str(ROOT/'util'))
    from map_export import parse_odm_file
    native = parse_odm_file(RUNTIME/'maps/mm5_sw.odm')['payload']
    for key in ['height_map','tile_map','attribute_map']:
        assert bytes(native[key]) == bytes.fromhex(terrain[key+'_hex'])
    assert len(native['bmodels']) == len(semantics['bmodels'])
    assert len(native['bmodels']) == len(geometry['bmodels'])
    for model,source_model in zip(native['bmodels'],geometry['bmodels']):
        # Donor bitmap registries preserve legacy casing; asset lookup is case-insensitive.
        expected={key.lower() for key in source_model['materials']['remaps'].values()}
        actual={face['texture_name'].lower() for face in model['faces']}
        assert actual==expected, ('Native material names changed',source_model['geometry_id'],expected,actual)
    assert not native['spawns']
    assert len(native['entities'])==len(scene['entities'])
    for entity,expected in zip(native['entities'],scene['entities']):
        assert entity['event_id_secondary']==expected['event_id_secondary']
        assert entity['name'].lower()==expected['name'].lower()
        assert entity['decoration_list_id']==expected['decoration_list_id']
        assert entity['position']==expected['position']
        assert entity['facing']==expected['facing']
    for event in semantics['events']:
        for face in event['faces']:
            assert native['bmodels'][event['bmodel_index']]['faces'][face]['cog_triggered_number'] == event['id']
    for override in semantics['face_overrides']:
        face = native['bmodels'][override['bmodel_index']]['faces'][override['face_index']]
        assert face['attributes'] & 0x20002004 == override['legacy_attributes']
        assert face['cog_triggered_number'] == 0
    report = {'status':'native export/readback checkpoint; visual and delivery acceptance tracked separately',
              'world':'mm5','map':'mm5_sw.odm','mapStatsId':MAP_ID,'stage':str(stage),
              'assemblies':len(semantics['buildings']),'bmodels':len(native['bmodels']),
              'props':len(semantics['props']), 'landscapeGroups':len(semantics['landscape']),
              'sourceObjSha256':source_hashes,
              'nativeEvents':len(events),'entities':len(native['entities']),
              'scenery':scenery['counts'],
              'spawns':len(native['spawns']),'actors':len(scene['initial_state']['actors']),
              'terrainArraysExact':True,'nativeMaterialNamesExact':True,
              'nativeBytes':(RUNTIME/'maps/mm5_sw.odm').stat().st_size,
              'nativeSha256':hashlib.sha256((RUNTIME/'maps/mm5_sw.odm').read_bytes()).hexdigest(),
              'remainingAssemblies':[b['id'] for b in plan['buildings']
                                     if b['id'] not in {e['id'] for e in semantics['buildings']}],
              'limitations':['static readback does not certify visual composition, game clicks or save/reload',
                             'see COMPLETION.md and linked native/runtime reviews for acceptance evidence']}
    write(REVIEW/'build.json',report)
    from review_environment import review as review_environment
    review_environment()
    from review_bridges import review as review_bridges
    review_bridges()
    from review_watchtower import review as review_watchtower
    review_watchtower()
    from review_castle import review as review_castle
    review_castle()
    from review_camps import review as review_camps
    review_camps()
    from review_natural_entrances import review as review_natural_entrances
    review_natural_entrances()
    from review_sewer import review as review_sewer
    review_sewer()
    from review_clearings import review as review_clearings
    review_clearings()
    from review_skyrope import review as review_skyrope
    review_skyrope()
    from review_roads import review as review_roads
    review_roads()
    from review_town_sewers import review as review_town_sewers
    review_town_sewers()
    from review_town_chests import review as review_town_chests
    review_town_chests()
    from review_source_wells import review as review_source_wells
    review_source_wells()
    from review_waymarks import review as review_waymarks
    review_waymarks()
    from review_message_bottles import review as review_message_bottles
    review_message_bottles()
    from review_melon_patches import review as review_melon_patches
    review_melon_patches()
    from review_wreck import review as review_wreck
    review_wreck()
    from review_camp_pyramid import review as review_camp_pyramid
    review_camp_pyramid()
    from review_chapter_court import review as review_chapter_court
    review_chapter_court()
    from review_inner_road import review as review_inner_road
    review_inner_road()
    from review_route_placeholders import review as review_route_placeholders
    review_route_placeholders()
    from review_ranger_yard import review as review_ranger_yard
    review_ranger_yard()
    from review_frontage_signs import review as review_frontage_signs
    review_frontage_signs()
    from review_public_notices import review as review_public_notices
    review_public_notices()
    (stage/'settings.ini').write_text('[assets]\nroot='+str(assets)+'\n[audio]\nsound_volume=0\nmusic_volume=0\n'
        '[debug]\nimmortal=false\nunlimited_mana=false\nnew_game_god_lich=false\nmovement_speed_multiplier=1\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, default=Path('/tmp/openyamm-mm5-castleview'))
    build(parser.parse_args().stage.resolve())
