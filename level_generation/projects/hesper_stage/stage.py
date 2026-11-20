"""Assemble the shared Hesper stage: an isolated asset root that mounts the `hesper` world and owns every Hesper
registration, so assets_dev is never modified.

    python3 level_generation/projects/hesper_stage/stage.py [--stage DIR]

The stage (default output/hesper_stage, git-ignored) mirrors assets_dev: directories it does not change are links,
the ones it changes are real copies. Into it go
  - worlds/hesper: world.yml, every map project's runtime/worlds/hesper tree (maps.yml), the Hesper surface
    textures (design/kreegan_world/art, cooked to textures_x4), the 3D decorations (decorations.yml, cooked to
    models/ and bound in models/decorations.yml), the monsters (monsters.yml: the design's draft monster rows and
    their descriptors as the world's table contributions in data_tables/, the creature models cooked to models/
    and bound in models/actors.yml), the shared map Lua (common/*.lua, as events/common/hesper_common.lua);
  - engine/data_tables: map_stats rows (maps.yml); the decorations' rows are the world's own
    (data_tables/decoration_data.txt and rendering/sprite_frame_data_world_decorations.yml);
  - engine/terrain_materials: Hesper's library materials (terrain_library.yml, cooked from assets_source);
  - engine/rendering/sky: the hesper_ash preset and theme (design/kreegan_world/zone1/sky_preset.yml) and the
    night texture.
Run it after a map project's build; re-running refreshes everything (the cooks are incremental). Launch with

    ./tools/run_game.sh --isolated hesper --world hesper --map hes_out1.odm --assets <stage>/assets_editor_dev
"""
import argparse
import copy
import csv
import os
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
DEV = ROOT / 'assets_dev'
ART = ROOT / 'design/kreegan_world/art'
parser = argparse.ArgumentParser()
parser.add_argument('--stage', type=Path, default=ROOT / 'output/hesper_stage')
# The NPC portraits' after-pass look (design/kreegan_world/art/portraits/postpass, the user's choice of 2026-10-23:
# C_slate), or 'original' for the approved x2 copies that npcs*.yml and skills.yml name.
parser.add_argument('--portrait-look', default='C_slate', help="postpass look of the NPC portraits, or 'original'")
args = parser.parse_args()
PORTRAITS = ART / 'portraits'


def portrait_source(relative):
    """The file installed for a portrait named by its approved x2 copy: that look's processed copy of it."""
    path = ROOT / relative
    if args.portrait_look == 'original':
        return path
    assert path.parent == PORTRAITS / 'x2', relative
    processed = PORTRAITS / 'postpass/out' / args.portrait_look / 'x2' / path.name
    master = PORTRAITS / 'masters' / path.name
    if not processed.exists() or processed.stat().st_mtime < master.stat().st_mtime:
        raise SystemExit(f'{processed} is missing or older than its master: run '
                         f'design/kreegan_world/art/portraits/postpass/postpass.py --look {args.portrait_look} '
                         f'--only {path.stem}')
    return processed


stage = args.stage.resolve()
# The run builds into a copy of the live stage and swaps it in only when the whole run succeeds, so a failed run (a
# portrait being made, a bad entry) leaves the previous stage whole for every other builder (2026-10-23; about 4 s).
live = stage / 'assets_editor_dev'
assets = stage / 'assets_editor_dev.next'
if assets.exists() or assets.is_symlink():
    shutil.rmtree(assets)
if live.exists():
    subprocess.run(['cp', '-a', str(live), str(assets)], check=True)
sources = stage / 'sources'           # cook sources gathered from the design art and the prop projects
marker = stage / 'hesper_stage.json'
if stage.exists() and any(stage.iterdir()) and not marker.exists():
    raise SystemExit('Refusing a non-empty directory without the Hesper stage marker: ' + str(stage))

# --- The mirror ---------------------------------------------------------------------------------------------------
# COPY: copied whole (the stage edits files in them). EXPAND: a real directory whose children are mirrored in turn,
# so a stage file never writes through a link into assets_dev. HARDLINK: a real tree of hard-linked files (the HUD
# finds no icons through a linked icons directory; the stage never writes into these). Everything else is a
# directory link or a file copy (PhysicsFS does not follow file links inside a mount).
COPY = {('engine', 'data_tables')}
HARDLINK = {('engine', 'icons_x2')}
EXPAND = {(), ('engine',), ('worlds',), ('engine', 'terrain_materials'), ('engine', 'rendering'),
          ('engine', 'rendering', 'sky'), ('engine', 'rendering', 'weather'), ('engine', 'liquids'),
          ('engine', 'world_items'), ('engine', 'effects')}


def mirror(source, target, parts=()):
    target.mkdir(parents=True, exist_ok=True)
    for child in sorted(source.iterdir()):
        key = parts + (child.name,)
        destination = target / child.name
        if destination.exists() or destination.is_symlink():
            continue
        if child.is_dir() and key in EXPAND:
            mirror(child, destination, key)
        elif child.is_dir() and key in COPY:
            shutil.copytree(child, destination)
        elif child.is_dir() and key in HARDLINK:
            shutil.copytree(child, destination, copy_function=os.link)
        elif child.is_dir():
            destination.symlink_to(child, target_is_directory=True)
        else:
            shutil.copy2(child, destination)


if not assets.exists():
    mirror(DEV, assets)
# A COPY directory's file that is new or changed in assets_dev (a new or edited engine table) is copied in: a copy
# keeps its source's time and size, so any difference means the source changed. The tables the stage changes (Hesper
# rows appended) differ by design and are rebuilt from the assets_dev source further down on every run, so copying
# them here first changes nothing.
for parts in COPY:
    for child in sorted(DEV.joinpath(*parts).rglob('*')):
        destination = assets.joinpath(*parts, child.relative_to(DEV.joinpath(*parts)))
        if child.is_file() and (not destination.exists()
                                or (child.stat().st_mtime, child.stat().st_size)
                                != (destination.stat().st_mtime, destination.stat().st_size)):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, destination)
# A directory that joined EXPAND after the stage was made is still a link: replace it with its mirror.
for parts in sorted(EXPAND, key=len):
    path = assets.joinpath(*parts)
    if parts and path.is_symlink():
        path.unlink()
        mirror(DEV.joinpath(*parts), path, parts)
marker.write_text(json.dumps({'project': 'hesper_stage', 'original_assets': str(DEV)}, indent=2) + '\n')
for parts in EXPAND | COPY | HARDLINK:
    path = assets.joinpath(*parts)
    assert path.is_dir() and not path.is_symlink(), path
world = assets / 'worlds/hesper'
world.mkdir(exist_ok=True)


def fnv1a64(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return value


def run(command):
    subprocess.run([str(part) for part in command], check=True, cwd=ROOT)


def write_table(path, rows):
    with path.open('w', newline='') as stream:
        csv.writer(stream, delimiter='\t', lineterminator='\n').writerows(rows)


def read_table(path):
    with path.open(newline='') as stream:
        return list(csv.reader(stream, delimiter='\t'))


# --- The world and its maps ---------------------------------------------------------------------------------------
registry = yaml.safe_load((PROJECT / 'maps.yml').read_text())['maps']
# Hesper's decoration numbers (decoration_data '#', a map entity's decoration_list_id + 1), clear of the engine's rows
# (1-673 in 2026-10) and MM9's 2001-2999; their sprites 25001-25999, clear of MM9's 24801-24999.
DECORATION_RANGE = (3001, 3999)
DECORATION_SPRITE_BASE = 25001
(world / 'world.yml').write_text(yaml.safe_dump({
    'id': 'hesper', 'name': 'Hesper', 'sourceGame': 'mm8', 'dependencies': ['mm8', 'mm7', 'mm6'],
    'start': {'map': 'hes_out1.odm'},             # new games start at the crash (hesper_out1 README, The arrival)
    # A monster's melee reaches the party across a height difference of at most half the lower body's height, so a
    # party on a ledge is out of reach and the monster finds the way up (design/kreegan_world/ENGINE.md; the
    # walkability report in WORK_PACKAGES/requests/P3.md).
    'actorCombat': {'meleeVerticalReach': 0.5},
    # No generated MMerge mercenaries in Hesper's taverns (the user, 2026-10-26: the Last Lamp seats none).
    'tavernHirelings': False,
    # Hesper's own loading pages (level_generation/ui/hesper_loading/selected, installed below as icons).
    'loadingScreens': ['hes_loading1', 'hes_loading2', 'hes_loading3', 'hes_loading4'],
    # AUDIO.md "Ambience": the two beds under the music; "Music": Landfall's district on hes_out1 hears its own track
    # (103, hes_music_landfall) inside the town walls (design/kreegan_world/zone1/landfall_plan.py's box).
    'ambience': {'hes_out1.odm': 'amb_starport_bed', 'hes_d00.blv': 'amb_facility_bed', 'hes_d01.blv': 'amb_facility_bed',
                 'hes_d02.blv': 'amb_facility_bed', 'hes_d10.blv': 'amb_facility_bed'},
    'ambienceVolume': 0.6,
    'musicAreas': {'hes_out1.odm': [{'track': 103, 'rect': [-21600, -21000, -10200, -12400]}]},
    # The Hum (COMBAT "The Hum", QBITS: nodes 100009, 100010, 100014): party damage spells at 50/65/80/100 % as the
    # nodes fall; the Crownspire always full, the Undervault shielded from it, D9 a null field (only a Null Damper II
    # casts there, at half power).
    'hum': {'qbits': [100009, 100010, 100014], 'percents': [50, 65, 80, 100],
            'maps': {'hes_d12.blv': 50, 'hes_undervault.blv': 100, 'hes_d09.blv': 0}},
    # Burning floors (the Scour's and the Foundry's slag) burn as Fire that resistances cut, and a FireImmune item (the
    # Kreegan Gland, the Forgemaster's Hammer) spares its wearer; the Brood Spires' acid (its burning tiles) is Body
    # (ENGINE.md, typed floor burn and liquid harm).
    'floorBurn': {'type': 'fire', 'resisted': True, 'maps': {'hes_out3.odm': 'body'}},
    # The major objectives (QBITS.md "Derived values"): the four ship parts, the three nodes, the four shards and the
    # Brood Mother; how many are done gates the shops' later stock (vendor stock min_objectives: 3 and 7).
    'objectives': [100040, 100041, 100042, 100043, 100009, 100010, 100014, 100018, 100019, 100020, 100021, 100011],
    # The Hesper monsters (monsters.yml): the design's ids, appended to the engine's monster tables.
    # The Hesper items the engine can already use (items.yml): the design's ids, appended to the engine's item table.
    # Hesper's own missiles' objects (projectiles.yml): rows appended to the engine's object table.
    # The scouts', the Ashrunners' and the packages' shops (npcs*.yml `vendors`): deterministic-stock vendors in the
    # house blocks (9300-9499, design/kreegan_world/WORK_PACKAGES/README.md).
    # The 3D decorations (decorations.yml): the world's decoration rows, numbered by decoration_ids.yml.
    'idRanges': {'monsters': {'begin': 10000, 'end': 10999}, 'items': {'begin': 11000, 'end': 11999},
                 'objects': {'begin': 21000, 'end': 21999}, 'vendors': {'begin': 9300, 'end': 9499},
                 'decorations': {'begin': DECORATION_RANGE[0], 'end': DECORATION_RANGE[1]}},
    'tableContributions': [
        {'table': 'items', 'idDomain': 'items', 'mode': 'append', 'path': 'data_tables/items.txt',
         'sourceIdColumn': 19, 'canonicalIdColumn': 18},       # source_item_id (the id itself), hesper:item/...
        {'table': 'item_effects', 'idDomain': 'items', 'mode': 'append', 'path': 'data_tables/item_effects.txt'},
        {'table': 'item_sets', 'idDomain': 'items', 'mode': 'append', 'path': 'data_tables/item_sets.txt'},
        {'table': 'workshop_mods', 'idDomain': 'items', 'mode': 'append', 'path': 'data_tables/workshop_mods.txt'},
        {'table': 'monster_data', 'idDomain': 'monsters', 'mode': 'append', 'path': 'data_tables/monster_data.txt'},
        {'table': 'monster_descriptors', 'idDomain': 'monsters', 'mode': 'append',
         'path': 'data_tables/monster_descriptors.txt'},
        {'table': 'object_descriptors', 'idDomain': 'objects', 'mode': 'append',
         'path': 'data_tables/object_descriptors.txt'},
        # The staged readables' texts (items.yml `readable`: the readText use action reads them).
        {'table': 'readable_scrolls', 'idDomain': 'items', 'mode': 'append', 'path': 'data_tables/readable_items.txt'},
        {'table': 'vendors', 'idDomain': 'vendors', 'mode': 'append', 'path': 'data_tables/vendors.txt'},
        {'table': 'vendor_aliases', 'idDomain': 'vendors', 'mode': 'append', 'path': 'data_tables/vendor_aliases.txt'},
        {'table': 'vendor_stock', 'idDomain': 'vendors', 'mode': 'append', 'path': 'data_tables/vendor_stock.txt'},
        # The staged items' paperdoll placements (level_generation/ui/hesper_paperdoll), written with the items.
        {'table': 'complex_item_pictures', 'idDomain': 'items', 'mode': 'append',
         'path': 'data_tables/complex_item_pictures.txt'},
        {'table': 'decorations', 'idDomain': 'decorations', 'mode': 'append',
         'path': 'data_tables/decoration_data.txt'}]},
    sort_keys=False))
# The world's own icons (its minimaps, later its portraits) are a declared icon package.
packages = (DEV / 'engine/icon_packages.txt').read_text()
assert 'worlds/hesper' not in packages
(assets / 'engine/icon_packages.txt').write_text(packages.rstrip('\n') + '\nworlds/hesper x2\n')
installed = []
for entry in registry:
    runtime = ROOT / 'level_generation/projects' / entry['project'] / 'runtime/worlds/hesper'
    if not (runtime / 'maps' / entry['file']).exists():
        print(f"skip {entry['file']}: {runtime} has no build yet")
        continue
    for path in sorted(p for p in runtime.rglob('*') if p.is_file()):
        target = world / path.relative_to(runtime)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    installed.append(entry)
    # The map's lighting bake (<stage>/bakes, from level_generation/projects/hesper_stage/bake.sh), installed only
    # while it was baked from this very map: the game refuses to load a map whose .lighting was cooked for other
    # geometry, so after a rebuild the map goes unbaked until it is baked again.
    odm = world / 'maps' / entry['file']
    lighting = odm.with_suffix('.lighting')
    baked = stage / 'bakes' / lighting.name
    if odm.suffix == '.odm':
        current = baked.exists() and struct.unpack_from('<Q', baked.read_bytes(), 16)[0] == fnv1a64(odm.read_bytes())
        for suffix in ('.lighting', '.bake.json'):
            installed_file = odm.with_suffix(suffix)
            if current:
                shutil.copy2(baked.with_suffix(suffix), installed_file)
            elif installed_file.exists():
                installed_file.unlink()
        if baked.exists() and not current:
            print(f"{entry['file']}: its lighting bake is for an older build of the map; installed unbaked")

table = assets / 'engine/data_tables/map_stats.txt'
rows = [row for row in read_table(DEV / 'engine/data_tables/map_stats.txt')]
for entry in installed:
    assert not any(len(row) > 2 and row[2].lower() == entry['file'] for row in rows), entry['file']
    assert not any(row and row[0] == str(entry['id']) for row in rows), entry['id']
    reference = next(row for row in rows if len(row) > 2 and row[2] == entry['reference'])
    row = list(reference) + [''] * max(0, 35 - len(reference))
    row[0], row[1], row[2] = str(entry['id']), entry['name'], entry['file']
    if 'encounters' in entry:
        row[12] = str(entry['encounters'])
    for slot in (1, 2, 3):                      # the encounter slots: Mon Pic, Mon name, Dif 1-5, # (count range)
        encounter = entry.get('slots', {}).get(slot)
        column = 16 + 4 * (slot - 1)
        if encounter:
            row[column:column + 4] = [encounter['picture'], encounter['name'], str(encounter['difficulty']),
                                      f"{encounter['count'][0]}-{encounter['count'][1]}"]
        elif 'slots' in entry:
            row[column:column + 4] = ['0', '0', '1', '1-3']           # an unused slot, as MM writes one
    row[30], row[31], row[33], row[34] = 'level_generation', 'Hesper (stage only)', '-', 'hesper'
    rows.append(row)
write_table(table, rows)
# Map-edge travel (edges.yml): each installed outdoor map's row of map_navigation.txt, its edges leading to the
# installed maps its crossings join. The arrival height is the destination's ground: the native triangle under the
# point in its project's built terrain (source/<map>.terrain.yml).
def terrain_height(entry, x, y):
    terrain = json.loads((ROOT / 'level_generation/projects' / entry['project'] / 'source' /
                          (Path(entry['file']).stem + '.terrain.yml')).read_text())
    heights = list(bytes.fromhex(terrain['height_map_hex']))
    fx, fy = (x + 32768.0) / 512.0, (32768.0 - y) / 512.0
    ix, iy = min(max(int(fx), 0), 126), min(max(int(fy), 0), 126)
    tx, ty = fx - ix, fy - iy
    h00, h10, h01, h11 = (heights[(iy + dy) * 128 + ix + dx] * 32.0 for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)))
    if tx + ty <= 1:
        return round(h00 + (h10 - h00) * tx + (h01 - h00) * ty)
    return round(h11 + (h01 - h11) * (1 - tx) + (h10 - h11) * (1 - ty))


by_file = {entry['file']: entry for entry in installed}
navigation = {}
for crossing in yaml.safe_load((PROJECT / 'edges.yml').read_text())['crossings']:
    if crossing['a']['map'] not in by_file or crossing['b']['map'] not in by_file:
        continue
    for origin, destination in ((crossing['a'], crossing['b']), (crossing['b'], crossing['a'])):
        x, y = destination['arrival']
        z = terrain_height(by_file[destination['map']], x, y)
        # A heading of 0 reads as "none" in the table, so east is 360.
        navigation.setdefault(origin['map'], {})[origin['edge']] = (destination['map'], destination['facing'] or 360,
                                                                    (x, y, z))
nav_rows = read_table(DEV / 'engine/data_tables/map_navigation.txt')
for map_file, map_edges in navigation.items():
    assert not any(row and row[0].lower() == map_file for row in nav_rows), map_file
    row = [map_file, '-23040', '23040', '-23040', '23040']
    for edge in ('north', 'south', 'east', 'west'):
        target, facing, _ = map_edges.get(edge, ('0', 0, None))
        row += [target, '0', str(facing)]
    for edge in ('north', 'south', 'east', 'west'):
        position = map_edges.get(edge, (None, None, None))[2]
        row += [str(value) for value in position] if position else ['', '', '']
    nav_rows.append(row)
write_table(assets / 'engine/data_tables/map_navigation.txt', nav_rows)
# Hesper's continent (the integrator's follow-up 27; design/kreegan_world/quests/REPUTATION.md): reputation affects the
# shops and the NPCs, not the guards (the walls never fire on the party); NPC followers on (the Refuge's hirelings). A
# map's continent comes from its bolster_maps.txt row: one per staged map, with bolstering and MM's weather off (Hesper's
# ash is weather.yml's) and no continent skies, so only the reputation changes. No death maps: the party's defeat
# respawn stays as without a continent.
HESPER_CONTINENT = 5
continents = DEV / 'engine/data_tables/continent_settings.txt'
native = continents.read_bytes()
assert not any(line.split(b'\t', 1)[0].strip() == str(HESPER_CONTINENT).encode() for line in native.split(b'\n'))
continent_row = [str(HESPER_CONTINENT), 'Hesper', '', 'x', 'x', '', 'x', '1', '1'] + [''] * 14
(assets / 'engine/data_tables/continent_settings.txt').write_bytes(
    native + (b'' if native.endswith(b'\n') else b'\r\n') + ('\t'.join(continent_row) + '\r\n').encode('ascii'))
bolster = DEV / 'engine/data_tables/bolster_maps.txt'
native = bolster.read_bytes()
taken = {line.split(b'\t', 1)[0].strip() for line in native.split(b'\n')}
bolster_rows = [[str(entry['id']), entry['name'], str(HESPER_CONTINENT), '-', '-', '-', '-', '0', '0', '', '-', '-']
                for entry in registry]
assert not taken & {row[0].encode() for row in bolster_rows}
(assets / 'engine/data_tables/bolster_maps.txt').write_bytes(
    native + (b'' if native.endswith(b'\n') else b'\r\n') + ''.join('\t'.join(r) + '\r\n' for r in bolster_rows).encode('ascii'))

# --- Surface textures (BLV and BModel faces) ------------------------------------------------------------------------
texture_sources = sources / 'worlds/hesper/textures_x4'
texture_sources.mkdir(parents=True, exist_ok=True)
names = []
# Whole sets, then single keys of the zone kits that a built map uses ahead of their own maps: K3's root-lock bulkhead
# on the Undervault's Deep Stair (CR-P3-03; D15's build adds the rest of K3).
SURFACE_SETS = [ART / 'textures_d0/blv', ART / 'textures_out1/masters', ART / 'textures_interiors/masters']
SURFACE_SETS.append(ART / 'textures_k7_hive/masters')  # D9 Brood Pits
SURFACE_KEYS = [ART / 'textures_k3_transit/masters' / f'{key}.png' for key in ('htbulk', 'htbulkon')]
SURFACE_SETS += [ART / 'textures_k6_foundry/masters']  # D8 Foundry
SURFACE_KEYS += [ART / 'textures_k5_grafted/masters' / f'{key}.png' for key in ('hkrib', 'hkglyph')]
# D3's surfaces beyond D8's shared hkrib/hkglyph entries.
SURFACE_KEYS += [ART / 'textures_k5_grafted/masters' / f'{key}.png' for key in
                 ('hkrock', 'hkvein', 'hkfloor', 'hkore', 'hkceil', 'hktrim', 'hkskylat', 'hkblast', 'hkdoor',
                  'hkgraft', 'hkgraft2', 'hkgrlite', 'hkpylon', 'hkpylonx', 'hkconsol', 'hkconsok', 'hkloom',
                  'hkloomx', 'hkcage')]
SURFACE_SETS.append(ART / 'textures_k5_grafted/masters')  # D4 Labor Pens
SURFACE_SETS += [ART / 'textures_k9_lattice/masters', ART / 'textures_k3_transit/masters']  # D6 and node rooms
# Builders add the kits their maps need, so one master may be listed twice (a whole set and a single key): that is
# fine, but two different files of one name are not.
SURFACE_SETS.append(ART / 'textures_k8_ship/masters')  # D11 Seedship
SURFACE_KEYS += [ART / 'textures_k10_palace/masters' / f'{key}.png' for key in
                 ('hpwall', 'hptrim', 'hpfloor', 'hptroph1', 'hptroph2', 'hpbanner')]
SURFACE_SETS += [ART / 'textures_k3_transit/masters', ART / 'textures_k4_transitions/masters']  # D15 Undercroft
SURFACE_SETS += [ART / 'textures_k10_palace/masters', ART / 'textures_k9_lattice/masters',
                 ART / 'textures_k3_transit/masters']  # D12 Crownspire
SURFACE_SETS += [ART / 'textures_k12_salvage/masters', ART / 'textures_k5_grafted/masters',
                 ART / 'textures_k6_foundry/masters']  # the Scour (hes_out2): the Kept shanties, K5, K6
SURFACE_SETS += [ART / 'textures_k11_greenhouse/masters', ART / 'textures_k7_hive/masters',
                 ART / 'textures_k8_ship/masters']  # the Brood Spires (hes_out3): K11's greenhouses, D9's mouth, the gantry
source_by_name = {}
for paths in [sorted(folder.glob('*.png')) for folder in SURFACE_SETS] + [SURFACE_KEYS]:
    for path in paths:
        assert len(path.stem) <= 10, f'{path.name}: BLV and ODM face texture names are 10 characters at most'
        if path.stem in source_by_name:
            assert source_by_name[path.stem] == path.resolve(), f'{path.stem}: two Hesper textures of one name'
            continue
        source_by_name[path.stem] = path.resolve()
        names.append(path.stem)
        target = texture_sources / path.name
        if not target.exists() or target.read_bytes() != path.read_bytes():
            shutil.copy2(path, target)
run([sys.executable, ROOT / 'tools/cook_surface_textures.py', '--sources', sources, '--output', assets,
     '--world', 'hesper'])
assert all((world / 'textures_x4' / (name + '.oytex')).exists() for name in names)

# --- 3D decorations -------------------------------------------------------------------------------------------------
decorations = yaml.safe_load((PROJECT / 'decorations.yml').read_text())
model_sources = sources / 'worlds/hesper/models'
model_sources.mkdir(parents=True, exist_ok=True)


def glb_extent(path):
    """The model's extent along glTF x, y (up) and z, from its POSITION accessors."""
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20 + length])
    lows, highs = [], []
    for mesh in gltf['meshes']:
        for primitive in mesh['primitives']:
            accessor = gltf['accessors'][primitive['attributes']['POSITION']]
            lows.append(accessor['min'])
            highs.append(accessor['max'])
    return [max(high[i] for high in highs) - min(low[i] for low in lows) for i in range(3)]


# The Meshy models' exports are normalised; their size is the design's length (world units of the longest side).
designs = json.loads((ROOT / 'level_generation/props/hesper_decorations/designs.json').read_text())


bindings, decoration_rows = [], []
for entry in decorations['decorations']:
    name = entry['name']
    model = entry.get('model', name)                     # a variant (its own light) may reuse another's model
    candidates = [ROOT / folder / f'{model}{suffix}.glb' for folder in decorations['source_dirs']
                  for suffix in ('', '_export')]
    source = next(path for path in candidates if path.exists())
    target = model_sources / f'{name}.glb'
    if not target.exists() or target.read_bytes() != source.read_bytes():
        shutil.copy2(source, target)
    extent = glb_extent(source)
    if name in designs:
        height = round(designs[name]['length'] * extent[1] / max(extent))
    else:
        height = round(extent[1] * 100)             # the Blender models are built in metres
    bindings.append({'name': name, 'model': f'worlds/hesper/models/{name}.glb', 'height': height,
                     'yaw': 'facing', **{key: entry[key] for key in ('mount', 'turn_in') if key in entry}})
    decoration_rows.append((name, entry.get('radius', 0), height, entry.get('light', [0, 0, 0, 0])))
# The monsters' models (monsters.yml) are cooked with the decorations.
monster_input = yaml.safe_load((PROJECT / 'monsters.yml').read_text())
def check_model_rules(path):
    """Rules the game refuses a model for (engine/models/GltfModelLoader.cpp) that no headless scenario sees, since
    those load no models: a mesh listing itself, a missing mesh or one mesh twice in its LOD or shadow chain, and a
    specular-mask material without a metallic-roughness texture. A loader check in the engine would cover all of them
    (design/kreegan_world/ENGINE.md, engine queue)."""
    data = path.read_bytes()
    gltf = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
    meshes = gltf.get('meshes', [])
    for index, mesh in enumerate(meshes):
        for key, most in (('openyamm_lods', 3), ('openyamm_shadow_lods', 4)):
            chain = (mesh.get('extras') or {}).get(key)
            if chain is not None:
                assert 0 < len(chain) <= most and len(set(chain)) == len(chain) \
                    and all(other < len(meshes) and other != index for other in chain), \
                    f'{path}: mesh {index} {key} {chain} (the game refuses the model)'
    for index, material in enumerate(gltf.get('materials', [])):
        assert not (material.get('extras') or {}).get('openyamm_specular_mask') \
            or 'metallicRoughnessTexture' in material.get('pbrMetallicRoughness', {}), \
            f"{path}: material {index} {material.get('name')} has a specular mask but no metallic-roughness texture " \
            '(the game refuses the model)'
        # A split that copies extras without their textures leaves dangling indices (Noble attachments, 2026-10-24).
        for key, value in (material.get('extras') or {}).items():
            if isinstance(value, dict) and 'index' in value:
                assert value['index'] < len(gltf.get('textures', [])), \
                    f"{path}: material {index} {material.get('name')} {key} names texture {value['index']}, but the " \
                    f"model has {len(gltf.get('textures', []))} (strip the extra or keep its texture)"


def check_burn_maps(path):
    """A burn death (death_effect type burn) needs extras.openyamm_burn_map on every material a skinned primitive draws
    with, variants included (game/fx/WorldFxSystem.cpp; the desktop refuses the actor, no headless run sees it).
    level_generation/creatures/claude_shared/burn_maps.py adds them."""
    data = path.read_bytes()
    gltf = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
    materials = gltf.get('materials', [])
    skinned = {node['mesh'] for node in gltf.get('nodes', []) if 'skin' in node and 'mesh' in node}
    for mesh_index in skinned:
        for primitive in gltf['meshes'][mesh_index]['primitives']:
            used = {primitive.get('material')} | {mapping['material'] for mapping in
                    primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])}
            for index in sorted(used - {None}):
                assert 'openyamm_burn_map' in (materials[index].get('extras') or {}), \
                    f"{path}: material {index} {materials[index].get('name')} has no openyamm_burn_map, but its " \
                    'binding burns on death (the game refuses the actor; claude_shared/burn_maps.py)'
                # A 1x1 map cooks with one level while its sampler wants mips; the desktop refuses it as "prepared
                # for another use" (engine/render/ModelRenderer.cpp).
                image = gltf['images'][gltf['textures'][materials[index]['extras']['openyamm_burn_map']['index']]['source']]
                view = gltf['bufferViews'][image['bufferView']]
                start = 28 + struct.unpack_from('<I', data, 12)[0] + view.get('byteOffset', 0)
                width, height = struct.unpack_from('>II', data, start + 16)
                assert min(width, height) >= 4, f"{path}: burn map {image.get('name')} is {width}x{height}; use 4x4 or more"


# The Hesper items' own ground models (item_models.yml, level_generation/props/hesper_items_claude): cooked with the
# decorations as worlds/hesper/models/item_<icon>.glb, their textures already at the ground items' sizes (colour 512,
# normal and metallic-roughness 256; the sidecar keeps the creature class's relief lift off). Built in world units:
# the binding's length is the model's longest horizontal side.
item_models = yaml.safe_load((PROJECT / 'item_models.yml').read_text())['models']
item_model_lengths = {}
for entry in item_models:
    source, target = ROOT / entry['source'], model_sources / f"item_{entry['icon']}.glb"
    check_model_rules(source)
    if not target.exists() or target.read_bytes() != source.read_bytes():
        shutil.copy2(source, target)
    sidecar = target.with_suffix('.cook.yml')
    sidecar_text = 'max_size: 512\nnormal_strength: 1\n'
    if not sidecar.exists() or sidecar.read_text() != sidecar_text:
        sidecar.write_text(sidecar_text)
    extent = glb_extent(source)
    # `length`: a binding length other than the model's own (it is scaled to it): a size corrected after its bake.
    item_model_lengths[entry['icon']] = entry.get('length', round(max(extent[0], extent[2]), 1))

for name, source in monster_input['models'].items():
    source, target = ROOT / source, model_sources / name
    check_model_rules(source)
    if not target.exists() or target.read_bytes() != source.read_bytes():
        shutil.copy2(source, target)
run([sys.executable, ROOT / 'tools/cook_models.py', '--source', sources, '--output', assets, '--profile', 'desktop',
     '--only', 'worlds/hesper/models/*'])
(world / 'models').mkdir(exist_ok=True)
for manifest in ('decorations.yml', 'indoor_decorations.yml'):        # outdoor and indoor (BLV) maps alike
    (world / 'models' / manifest).write_text(
        '# Generated by level_generation/projects/hesper_stage/stage.py from its decorations.yml.\n'
        + yaml.safe_dump({'decorations': bindings}, sort_keys=False))

# The decorations are the world's own (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md): their rows are the world's
# `decorations` contribution (worlds/hesper/data_tables/decoration_data.txt, numbers in world.yml's decorations range)
# and their sprites the world's sprite frames (worlds/hesper/rendering/sprite_frame_data_world_decorations.yml); the
# stage's engine copies of decoration_data.txt and sprite_frame_data_common.yml stay plain copies of assets_dev.
engine_rows = read_table(DEV / 'engine/data_tables/decoration_data.txt')
known = {row[1].lower() for row in engine_rows if len(row) > 1}
engine_last = max(int(row[0]) for row in engine_rows if row and row[0].isdigit())
assert engine_last < DECORATION_RANGE[0], \
    f"the engine's decoration table reaches {engine_last}, into Hesper's range {DECORATION_RANGE}: move the range"
common_frames = 'engine/rendering/sprite_frame_data_common.yml'
if (assets / common_frames).read_bytes() != (DEV / common_frames).read_bytes():
    shutil.copy2(DEV / common_frames, assets / common_frames)      # once a Hesper-extended copy (until 2026-10-29)
# Built maps store decoration ids, so they never move: decoration_ids.yml holds every id given, and a new decoration
# takes the next free one (appended to the file).
ids_path = PROJECT / 'decoration_ids.yml'
deco_registry = yaml.safe_load(ids_path.read_text())
assert deco_registry['base'] == DECORATION_RANGE[0], (deco_registry['base'], DECORATION_RANGE)
listed = {name for name, *_ in decoration_rows}
dropped = sorted(set(deco_registry['ids']) - listed)
assert not dropped, f'decorations.yml no longer lists {dropped}: maps were built with their ids; keep them'
added = [name for name, *_ in decoration_rows if name not in deco_registry['ids']]
for name in added:
    deco_registry['ids'][name] = max(deco_registry['ids'].values(), default=DECORATION_RANGE[0] - 1) + 1
if added:
    with ids_path.open('a') as stream:
        stream.writelines(f"  {name}: {deco_registry['ids'][name]}\n" for name in added)
assert all(DECORATION_RANGE[0] <= value <= DECORATION_RANGE[1] for value in deco_registry['ids'].values()), \
    f'a decoration id is outside {DECORATION_RANGE}: widen the range in stage.py'
# A decoration's model is found through its sprite, so each needs its own sprite: one frame of the engine's
# placeholder texture, never drawn while the model is bound. Its id follows the decoration's (3001 -> 25001).
header = [row for row in engine_rows[:3] if not (row and row[0].isdigit())]
rows, sprites, decoration_ids = [], [], {}
by_name = {name: (radius, height, light) for name, radius, height, light in decoration_rows}
for name, decoration_id in sorted(deco_registry['ids'].items(), key=lambda item: item[1]):
    assert name.lower() not in known, name
    radius, height, (light_radius, red, green, blue) = by_name[name]
    decoration_ids[name] = decoration_id
    sprite_id = DECORATION_SPRITE_BASE + decoration_id - DECORATION_RANGE[0]
    sprites.append({'sprite_id': sprite_id, 'sprite_name': name, 'frames': [
        {'texture_name': 'pending', 'frame_length_raw': 0, 'flags': ['First'], 'scale': 1.0}]})
    # 14 columns like the native rows: a 15th is the map aliases column.
    rows.append([str(decoration_id), name, name.replace('hes_', '').replace('_', ' '), '0', str(radius), str(height),
                 str(light_radius), str(red), str(green), str(blue), '0', '0', str(sprite_id), '-'])
(world / 'data_tables').mkdir(exist_ok=True)
write_table(world / 'data_tables/decoration_data.txt', header + rows)
(world / 'rendering').mkdir(exist_ok=True)
(world / 'rendering/sprite_frame_data_world_decorations.yml').write_text(
    "# Hesper's decoration sprites (one per 3D decoration), written by level_generation/projects/hesper_stage/stage.py.\n"
    + yaml.safe_dump({'format_version': 1, 'kind': 'world_decoration_sprite_frames', 'package_id': 'hesper',
                      'sprites': sprites}, sort_keys=False, width=120))
(stage / 'decoration_ids.json').write_text(json.dumps(decoration_ids, indent=1) + '\n')

# --- Monsters -------------------------------------------------------------------------------------------------------
# The draft rows (39 columns: # Name Picture ...), the descriptors named by their Picture, and the actor bindings.
draft = read_table(ROOT / 'design/kreegan_world/data/monster_data.txt')
draft_header = [row for row in draft if not row[0].isdigit() and not row[0].startswith('# ')][:2]
draft_rows = {int(row[0]): row for row in draft if row[0].isdigit()}
engine_descriptors = read_table(DEV / 'engine/data_tables/monster_descriptors.txt')
descriptor_by_name = {row[1]: row for row in engine_descriptors if len(row) > 1 and row[0].isdigit()}
data_rows, descriptor_rows, actor_bindings, binding_files = [], [], [], {}
for monster in monster_input['monsters']:
    row = draft_rows[monster['id']]
    assert not any('"' in cell for cell in row), row
    if 'picture' in monster:                    # an encounter family's MM-style "<family> A/B/C" picture
        row = list(row)
        row[2] = monster['picture']
    if monster.get('special') is not None:
        row = list(row)
        row[-1] = str(monster['special'])  # scripted summons replace the native unlimited summoner
    picture = row[2]
    data_rows.append(row)
    descriptor = list(descriptor_by_name[monster['reference']])
    descriptor[0], descriptor[1] = str(monster['id']), picture
    descriptor[2], descriptor[3] = str(monster['height']), str(monster['radius'])
    if 'sprite' in monster:                 # an explicitly selected greybox sprite (D9's eggs)
        descriptor[11:19] = [monster['sprite']] * 8   # SpriteStanding..SpriteBored (columns 11-18)
    descriptor_rows.append(descriptor)
    if monster.get('sprite_only', False):    # native roster bodies until their Hesper models are ready
        assert 'binding' not in monster
        continue
    source = monster['binding']
    if source['from'] not in binding_files:
        binding_files[source['from']] = yaml.safe_load((ROOT / source['from']).read_text())
    binding = copy.deepcopy(next(entry for entry in binding_files[source['from']]
                                 if entry['descriptor'] == source['entry']))
    binding['descriptor'] = picture
    if 'skin' in source:
        binding['skin'] = source['skin']
    if source.get('death_effect') == 'none':    # an integrator hold: the model can't do its death effect yet
        binding.pop('death_effect', None)
    if 'animation' in source:
        binding['animation'] = {**binding['animation'], **source['animation']}
    # The game reads stride_length from every animation block without a default and refuses the whole file without it.
    assert 'animation' not in binding or 'stride_length' in binding['animation'], \
        f"monster {monster['id']}: its binding's animation has no stride_length (add it in the row's binding)"
    # Every state clip, attack_ranged included for melee monsters (point it at the melee clip); only a Wimp (AI Type)
    # may leave out the two attacks. A missing one makes the game refuse the whole file at load.
    states = ['standing', 'walking', 'attack_melee', 'attack_ranged', 'hit', 'dying', 'dead', 'fidget']
    missing = [state for state in states if state not in binding.get('clips', {})
               and not (row[11] == 'Wimp' and state.startswith('attack'))]
    assert not missing, f"monster {monster['id']}: its binding has no clips {missing}"
    # A spellcaster (either Spl,Mas,Skil column set) needs a cast clip, or the game refuses the whole file at load.
    spell_columns = [index for index, name in enumerate(draft_header[1]) if name.startswith('Spl')]
    assert all(row[index].strip() in ('', '0') for index in spell_columns) \
        or 'cast' in binding.get('animation', {}), \
        f"monster {monster['id']} casts spells: its binding needs animation: {{cast: <clip>}} (Carbine_Attack on Kreegans)"
    models_bound = [binding['model']] + [part['model'] for part in binding.get('attachments', [])]
    for path in models_bound:
        assert Path(path).name in monster_input['models'] and path.startswith('worlds/hesper/models/'), path
    if (binding.get('death_effect') or {}).get('type') == 'burn':
        check_burn_maps(ROOT / monster_input['models'][Path(binding['model']).name])
    actor_bindings.append(binding)
tables = world / 'data_tables'
tables.mkdir(exist_ok=True)
write_table(tables / 'monster_data.txt', draft_header + data_rows)
write_table(tables / 'monster_descriptors.txt', engine_descriptors[:2] + descriptor_rows)
(world / 'models' / 'actors.yml').write_text(
    '# Generated by level_generation/projects/hesper_stage/stage.py from its monsters.yml: the creature projects\'\n'
    '# staged bindings (integration/actors.yml), keyed by the Hesper monster rows\' Picture names.\n'
    + yaml.safe_dump({'actors': actor_bindings}, sort_keys=False, width=120))
# The design's draft columns of the Hesper monsters (design/kreegan_world/data/monster_hesper.txt): shield, grade,
# regeneration delay (shields.yml below), the shield-break reaction and the rule flags.
with (ROOT / 'design/kreegan_world/data/monster_hesper.txt').open(newline='') as stream:
    hesper_columns = {int(row[0]): row for row in csv.reader(stream, delimiter='\t') if row and row[0].isdigit()}
# The monsters' declarative tactics (monsters.yml `tactics`) as the world's actor behaviour catalogue, which the engine
# reads beside engine/behaviors/behaviors.yml (devdocs/ACTOR_SCRIPTING_INVESTIGATION.md, Tactics). A monster whose
# design reaction to a shield break is "Falls back" gets `shield_break: {react: fall_back}` (it flees its target while
# its shield is down, at most 8 s); "Staggers 4 s when its shield breaks" gets `{react: stagger, max_seconds: 4}` (it
# holds its hit pose); "Climbs out of reach" gets `{react: climb}` (it falls back and a flyer rises above the party);
# blinking is the blink modifier's on_shield_break.
tactics = {monster['id']: dict(monster.get('tactics', {})) for monster in monster_input['monsters']}
for monster_id, monster_tactics in tactics.items():
    reaction = hesper_columns[monster_id][7].strip().lower()
    if reaction == 'falls back':
        monster_tactics['shield_break'] = {'react': 'fall_back'}
    elif reaction.startswith('climbs out of reach'):
        monster_tactics['shield_break'] = {'react': 'climb'}
    elif reaction.startswith('staggers') and 'when its shield breaks' in reaction:
        seconds = float(reaction.split()[1]) if reaction.split()[1].replace('.', '').isdigit() else 4.0
        monster_tactics['shield_break'] = {'react': 'stagger', 'max_seconds': seconds}
tactics = {monster_id: monster_tactics for monster_id, monster_tactics in tactics.items() if monster_tactics}
behaviors_path = world / 'behaviors.yml'
behavior_catalog = {'schema': 'openyamm.actorBehaviors.v1', 'tactics': tactics,
                          'behaviors': monster_input.get('behaviors', {})}
# Map projects may supply world-local scripts alongside their maps; merge their catalogues with staged tactics.
for entry in installed:
    catalog = ROOT / 'level_generation/projects' / entry['project'] / 'behaviors.yml'
    if catalog.exists():
        for key, values in yaml.safe_load(catalog.read_text()).items():
            assert key in ('behaviors', 'monsters'), (catalog, key)
            target = behavior_catalog.setdefault(key, {})
            for name, value in values.items():
                assert name not in target or target[name] == value, (catalog, name)
                target[name] = value
if tactics or behavior_catalog.get('behaviors'):
    behaviors_path.write_text(
        '# Generated by level_generation/projects/hesper_stage/stage.py from its monsters.yml (`tactics`).\n'
        + yaml.safe_dump({'schema': 'openyamm.actorBehaviors.v1', 'tactics': tactics,
                         'monsters': behavior_catalog.get('monsters', {}),
                         'behaviors': behavior_catalog.get('behaviors', {})}, sort_keys=False,
                         default_flow_style=None, width=120))
elif behaviors_path.exists():
    behaviors_path.unlink()

# --- Shields and relations ---------------------------------------------------------------------------------------
# shields.yml: the rules, sounds and grades, plus one entry per staged monster from the design's draft columns
# (design/kreegan_world/data/monster_hesper.txt: shield, shield_grade, shield_regen_delay_s); relations.yml: the
# factions and relations as they are. The engine reads both beside world.yml (devdocs/ENERGY_SHIELDS_AND_RELATIONS.md).
# The rule flags add the Overseers' shield link (ShieldLink), energy immunity (EnergyImmune, the Glassbacks) and, from
# the stage's `machines`, the machines an EMP grenade stuns.
shields = yaml.safe_load((PROJECT / 'shields.yml').read_text())
link = shields.pop('shield_link')
machines = set()
for span in shields.pop('machines'):
    first, _, last = str(span).partition('-')
    machines.update(range(int(first), int(last or first) + 1))
shield_overrides = shields.pop('monsters', {})
shields['monsters'] = {}
for monster in monster_input['monsters']:
    row = hesper_columns[monster['id']]
    pool, grade, delay = int(row[2] or 0), row[3], row[4]
    flags = set(row[8].split('|'))
    entry = {'shield': pool, 'grade': grade, 'regen_delay_seconds': float(delay)} if pool > 0 else {}
    if 'ShieldLink' in flags and pool > 0:
        entry['link'] = link
    if 'EnergyImmune' in flags:
        entry['energy_immune'] = True
    if monster['id'] in machines:
        entry['machine'] = True
    entry.update(shield_overrides.get(monster['id'], {}))
    shields['monsters'][monster['id']] = entry
(world / 'shields.yml').write_text(
    '# Generated by level_generation/projects/hesper_stage/stage.py from its shields.yml and the design\'s\n'
    '# monster_hesper.txt (the staged monsters).\n' + yaml.safe_dump(shields, sort_keys=False, default_flow_style=None,
                                                                    width=120))
shutil.copy2(PROJECT / 'relations.yml', world / 'relations.yml')
# modifiers.yml: the staged monsters' engine modifiers (true aim, never staggers, kites party, blink), the rows of the
# design's generated data/monster_modifiers.yml (make_monster_tables.py MODIFIER_RULES, from the rule flags); none
# staged removes the file (devdocs/MONSTER_MODIFIERS.md).
design_modifiers = yaml.safe_load((ROOT / 'design/kreegan_world/data/monster_modifiers.yml').read_text())
staged_modifiers = {monster['id']: design_modifiers['monsters'][monster['id']] for monster in monster_input['monsters']
                    if monster['id'] in (design_modifiers.get('monsters') or {})}
# Explicit build-document modifiers supplement omissions in the design's generated roster.
for monster in monster_input['monsters']:
    for modifier in monster.get('modifiers', []):
        values = staged_modifiers.setdefault(monster['id'], [])
        if modifier not in values:
            values.append(modifier)
# The monsters' own sounds (the engine's sounds modifier, AUDIO.md "Engine needs" 3) from audio.yml's monster rows:
# the drones hover always, the crawlers skitter while they move, the turrets wind up when they notice the party.
SOUND_MODIFIERS = {'drone_hover_loop': {'loop': 'drone_hover_loop', 'loop_always': True, 'loop_volume': 0.5},
                   'crawler_skitter': {'loop': 'crawler_skitter', 'loop_volume': 0.6},
                   'turret_servo_loop': {'aware': 'turret_windup'}}
staged_ids = {monster['id'] for monster in monster_input['monsters']}
for monster_id, sounds in (yaml.safe_load((PROJECT / 'audio.yml').read_text()).get('monsters') or {}).items():
    if monster_id in staged_ids and sounds.get('bored') in SOUND_MODIFIERS:
        staged_modifiers.setdefault(monster_id, []).append({'sounds': SOUND_MODIFIERS[sounds['bored']]})
modifiers_path = world / 'modifiers.yml'
if staged_modifiers:
    modifiers_path.write_text(
        '# Generated by level_generation/projects/hesper_stage/stage.py from the design\'s data/monster_modifiers.yml\n'
        '# (the staged monsters).\n'
        + yaml.safe_dump({'schema': design_modifiers['schema'], 'monsters': staged_modifiers}, sort_keys=False,
                         default_flow_style=None, width=120))
elif modifiers_path.exists():
    modifiers_path.unlink()

# --- Projectiles ----------------------------------------------------------------------------------------------------
# projectiles.yml (design/kreegan_world/PROJECTILES.md): Hesper's own missile tokens, which the design's monster rows
# name (make_monster_tables.py MISSILES). Each gets an object row (a copy of MM's laser object 555 with its own name and
# speed) in the world's object_descriptors contribution, a token in worlds/hesper/monster_projectiles.yml (object,
# impact object, shield tier; engine: devdocs/PROJECTILE_VFX_ALL_PROPOSAL.md section 12), and its flight and impact
# effects (projectile_effects.py) bound by object name in the stage's copy of engine/effects/projectiles.yml.
projectile_input = yaml.safe_load((PROJECT / 'projectiles.yml').read_text())
AUDIO_SOUND_IDS = yaml.safe_load((PROJECT / 'audio.yml').read_text())['sound_ids']
object_range = projectile_input['objects']
assert object_range == {'begin': 21000, 'end': 21999}       # world.yml's objects range above
engine_objects = read_table(DEV / 'engine/data_tables/object_list.txt')
laser = next(row for row in engine_objects if len(row) > 2 and row[2] == '555')
engine_object_names = {row[0].lower() for row in engine_objects if row}
engine_tokens = {row[0].lower() for row in read_table(DEV / 'engine/data_tables/monster_projectiles.txt')[1:] if row}
object_rows, missile_entries, object_bindings = [], {}, {}
for token, entry in projectile_input['missiles'].items():
    item = entry['object']
    assert token.lower() not in engine_tokens and item['name'].lower() not in engine_object_names, token
    assert object_range['begin'] <= item['id'] <= object_range['end'], token
    row = list(laser)
    row[0], row[2], row[6] = item['name'], str(item['id']), str(item['speed'])
    object_rows.append(row)
    missile_entries[token] = {'object': item['id'], 'impact_object': entry['impact_object'],
                              **({'tier': entry['tier']} if 'tier' in entry else {}),
                              **({'impact_sound_id': AUDIO_SOUND_IDS[entry['impact_sound']]}
                                 if 'impact_sound' in entry else {})}
    object_bindings[item['name']] = {'flight': f"hesper:fx/projectile/{item['name']}",
                                     'impact': f"hesper:fx/impact/{item['name']}", 'sprite': 'hidden',
                                     'light': entry['light'], 'impact_light': entry['impact_light']}
write_table(tables / 'object_descriptors.txt', [engine_objects[0]] + object_rows)
(world / 'monster_projectiles.yml').write_text(
    '# Generated by level_generation/projects/hesper_stage/stage.py from its projectiles.yml.\n'
    + yaml.safe_dump({'schema': 'openyamm.monsterProjectiles.v1', 'missiles': missile_entries,
                      'party': {item_id: {'missile': gun['missile'], 'shot_sound_id': AUDIO_SOUND_IDS[gun['shot_sound']]}
                                for item_id, gun in projectile_input['party'].items()}},
                     sort_keys=False, default_flow_style=None, width=120))
sys.path.insert(0, str(PROJECT))
import projectile_effects  # noqa: E402
effect_ids = set(projectile_effects.write(world / 'effects/projectile_library.yml'))
for binding in object_bindings.values():
    assert binding['flight'] in effect_ids and binding['impact'] in effect_ids, binding
effects_library = yaml.safe_load((DEV / 'engine/effects/library.yml').read_text())
effects_library['imports'].append('worlds/hesper/effects/projectile_library.yml')
if (world / 'effects/d06.yml').exists():
    effects_library['imports'].append('worlds/hesper/effects/d06.yml')
if (world / 'effects/d07.yml').exists():
    effects_library['imports'].append('worlds/hesper/effects/d07.yml')
if (world / 'effects/d13.yml').exists():
    effects_library['imports'].append('worlds/hesper/effects/d13.yml')
if (world / 'effects/hes_out4.yml').exists():          # the Crown's great cannon (hesper_out4/crown_effects.py)
    effects_library['imports'].append('worlds/hesper/effects/hes_out4.yml')
(assets / 'engine/effects/library.yml').write_text(
    '# Stage copy of assets_dev/engine/effects/library.yml plus Hesper\'s projectile effects.\n'
    + yaml.safe_dump(effects_library, sort_keys=False))
engine_bindings = (DEV / 'engine/effects/projectiles.yml').read_text()
assert 'objects' not in yaml.safe_load(engine_bindings)
(assets / 'engine/effects/projectiles.yml').write_text(
    engine_bindings.rstrip('\n') + '\n# Stage: Hesper\'s own missiles by object name '
    '(level_generation/projects/hesper_stage/projectiles.yml).\n'
    + yaml.safe_dump({'objects': object_bindings}, sort_keys=False, default_flow_style=None, width=120))
# Every staged monster's ranged attack names a missile the engine or Hesper has.
for row in data_rows:
    for column in (19, 23):
        assert row[column] in ('0', '') or row[column].lower() in engine_tokens \
            or row[column] in missile_entries, (row[0], row[column])

# --- Items --------------------------------------------------------------------------------------------------------
# items.yml: the draft item rows (design/kreegan_world/data/items.txt) that the engine can already use, as the world's
# items contribution (world.yml above). An item's icon is its own approved one (design/kreegan_world/art/item_icons/x2,
# installed in the world's icons; its inventory cells from the icon's size) or a stand-in engine icon. On the ground
# an item borrows its `ground` engine icon's object (the draft rows have no sprite index) and, for an own icon, that
# icon's 3D model (a binding added to the stage's copy of engine/world_items/items.yml).
with (ROOT / 'design/kreegan_world/data/items.txt').open(newline='') as stream:
    item_draft = [row for row in csv.reader(stream, delimiter='\t') if row]
item_rows = {int(row[0]): row for row in item_draft[1:] if row[0].isdigit()}
engine_sprites = {}
with (DEV / 'engine/data_tables/items.txt').open(newline='', encoding='latin-1') as stream:
    engine_item_rows = list(csv.reader(stream, delimiter='\t'))[1:]
for row in engine_item_rows:
    if len(row) > 11 and row[0].isdigit() and row[11].isdigit() and int(row[11]) > 0:
        engine_sprites.setdefault(row[1], row[11])
ground_bindings = DEV / 'engine/world_items/items.yml'
binding_lines = {line.split('icon: ', 1)[1].split(',', 1)[0]: line
                 for line in ground_bindings.read_text().splitlines() if line.startswith('  - {icon: ')}
added_bindings = []
item_icons = ROOT / 'design/kreegan_world/art/item_icons/x2'
(world / 'icons_x2').mkdir(exist_ok=True)
staged_items = []
# Held weapons and emitters (level_generation/ui/hesper_paperdoll/grips.yml): the hand's point in the icon (Equip X / Y,
# the draft rows have 0,0) and, for the guns, the muzzle-up icon the doll holds as MM8 holds its blasters.
grips = yaml.safe_load((ROOT / 'level_generation/ui/hesper_paperdoll/grips.yml').read_text())['grips']
for item in yaml.safe_load((PROJECT / 'items.yml').read_text())['items']:
    row = list(item_rows[item['id']])
    ground = item.get('ground', item['icon'])
    own = item_icons / (item['icon'] + '.png')
    grip = grips.get(item['id'])
    if own.exists():                                 # its own icon (a shared one may serve several items)
        assert ground != item['icon'], item
        row[1] = item['icon']
        if grip and len(grip) == 3:                  # a gun held as MM6-MM7 hold blasters (grips.yml up / out)
            with Image.open(own) as icon:
                if grip[2] == 'up':
                    icon.transpose(Image.Transpose.ROTATE_90).save(world / 'icons_x2' / own.name)
                    grip = [grip[1], icon.width // 2 - grip[0]]
                else:
                    icon.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(world / 'icons_x2' / own.name)
                    grip = [icon.width // 2 - grip[0], grip[1]]
        else:
            shutil.copy2(own, world / 'icons_x2' / own.name)
        if grip:                                     # Equip X / Y: where the doll's hand holds it
            row[14], row[15] = str(grip[0]), str(grip[1])
        with Image.open(world / 'icons_x2' / own.name) as icon:   # x2 pixels; the engine's 1 + (native - 14) / 32 cells
            row[29], row[30] = (str(max(1, min(14, 1 + (max(14, size // 2) - 14) // 32))) for size in icon.size)
        if any(f'icon: {item["icon"]},' in line for line in added_bindings):          # one binding per icon
            pass
        elif item['icon'] in item_model_lengths:     # its own ground model (bounds by tools/item_model_shapes.py)
            added_bindings.append(f'  - {{icon: {item["icon"]}, model: worlds/hesper/models/item_{item["icon"]}.glb, '
                                  f'length: {item_model_lengths[item["icon"]]}}}   # Hesper {row[2]}')
        else:
            added_bindings.append(binding_lines[ground].replace(f'icon: {ground},', f'icon: {item["icon"]},', 1)
                                  .split('   #')[0] + f'   # Hesper {row[2]} (stand-in: {ground})')
    else:
        row[1] = item['icon']
        assert (DEV / 'engine/icons_x2' / (item['icon'] + '.png')).exists(), item
    row[11] = row[11] if row[11] not in ('', '0') else engine_sprites[ground]
    row[19] = row[19] or row[0]                  # the provenance the engine requires of a world's items
    assert all('\t' not in cell and '"' not in cell for cell in row), row
    staged_items.append(row)
write_table(tables / 'items.txt', [item_draft[0]] + staged_items)
# loot.yml: the world's random loot, the staged items' weights per loot class of the design's draft hesper_loot.txt
# (H1 rolls for treasure levels 1-3, H2 for 4-5, H3 for 6, as ITEMS.md sizes the classes). With it, Hesper's chests and
# monsters roll only Hesper items; unstaged items wait for their rows.
loot_rows = [row for row in read_table(ROOT / 'design/kreegan_world/data/hesper_loot.txt')[2:] if row and row[0]]
loot_ids = {row[0] for row in staged_items}
loot_lines = ['# Generated by level_generation/projects/hesper_stage/stage.py from design/kreegan_world/data/'
              'hesper_loot.txt.', 'schema: openyamm.worldLoot.v1', 'treasure_levels: [H1, H1, H1, H2, H2, H3]',
              'classes:']
for column, loot_class in ((3, 'H1'), (4, 'H2'), (5, 'H3')):
    loot_lines.append(f'  {loot_class}:')
    loot_lines += [f'    {row[0]}: {row[column]}  # {row[2]}' for row in loot_rows
                   if row[0] in loot_ids and int(row[column] or 0) > 0]
# The curated enchantment pool (design/kreegan_world/data/enchant_pool.txt, ITEMS.md "Enchantments"): the standard
# bonuses Hesper loot may roll, and the special ones by grade (H1 rolls grades A and B, H2 B and C, H3 C and D), by
# the engine tables' names. Hesper's own kinds (hesper_standard, hesper_special) have no engine effects yet.
pool = [row for row in read_table(ROOT / 'design/kreegan_world/data/enchant_pool.txt')[2:] if row and row[0]]
engine_standard = {row[1].strip().lower() for row in read_table(DEV / 'engine/data_tables/standard_item_enchants.txt')
                   if len(row) > 1}
engine_special = {row[1].strip().lower() for row in read_table(DEV / 'engine/data_tables/special_item_enchants.txt')
                  if len(row) > 1}
standard_pool = [row[1] for row in pool if row[0] == 'standard']
assert all(name.lower() in engine_standard for name in standard_pool), standard_pool
loot_lines += ['enchantments:', f'  standard: {json.dumps(standard_pool)}', '  special:']
for loot_class, grades in (('H1', 'AB'), ('H2', 'BC'), ('H3', 'CD')):
    names = [row[1] for row in pool if row[0] == 'special' and (row[2] == 'all' or row[2] in grades)]
    assert all(name.lower() in engine_special for name in names), names
    loot_lines.append(f'    {loot_class}: {json.dumps(names)}')
# Hesper's own enchantments (the pool's hesper_standard and hesper_special rows; ITEMS "Enchantments") as the world's
# enchantments.yml, ids 100-199: rolled only on Hesper items, and listed in the pool beside the MM ones. Kreegan-bane
# and Kreegan Slaying strike the relations' Kreegan faction, the collared Kept (10060-10062) apart.
kreegan_ids = set()
for span in yaml.safe_load((PROJECT / 'relations.yml').read_text())['factions']['kreegans']['monsters']:
    first, _, last = str(span).partition('-')
    kreegan_ids.update(range(int(first), int(last or first) + 1))
kreegan_ids -= {10060, 10061, 10062}
kreegan_ranges = []
for monster_id in sorted(kreegan_ids):
    if kreegan_ranges and kreegan_ranges[-1][1] == monster_id - 1:
        kreegan_ranges[-1][1] = monster_id
    else:
        kreegan_ranges.append([monster_id, monster_id])
SLOTS = {'weapons': [20, 20, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'energy blades only': [20, 20, 0] + [0] * 9,
         'armour, emitters, jewellery': [0, 0, 0, 10, 10, 0, 0, 0, 0, 0, 10, 10],
         'armour, cloaks': [0, 0, 0, 10, 0, 0, 0, 10, 0, 0, 0, 0]}
HESPER_EFFECTS = {'of Static': {'shield_damage': 15}, 'of Disruption': {'shield_damage': 30},
                  'of Ions': {'energy_damage': [4, 10]}, 'of Plasma': {'energy_damage': [10, 24]},
                  'Overloading': {'overload_chance': 5}, 'of Collapse': {'overload_chance': 10},
                  "Hunter's": {'exposed_damage': 15}, "Predator's": {'exposed_damage': 30},
                  'Kreegan-bane': {'bonus_damage': 20, 'against': kreegan_ranges},
                  'Kreegan Slaying': {'bonus_damage': 40, 'against': kreegan_ranges},
                  'of Charge': {'personal_shield': 200}, 'of the Capacitor': {'personal_shield': 500},
                  'of Grounding': {'energy_damage_taken': -10}, 'of Earthing': {'energy_damage_taken': -20}}
fire_resistance = next(row for row in read_table(DEV / 'engine/data_tables/standard_item_enchants.txt')
                       if len(row) > 1 and row[1].strip().lower() == 'of fire resistance')
hesper_special = []
for index, row in enumerate([row for row in pool if row[0] == 'hesper_special']):
    rarity = row[2][0]
    hesper_special.append({'id': 100 + index, 'name': row[1], 'rarity': rarity, 'slots': SLOTS[row[3]],
                           'value': 1500 if rarity == 'B' else 4000, 'description': row[4],
                           **({'requires_flag': 'EnergyBlade'} if row[3] == 'energy blades only' else {}),
                           'effect': HESPER_EFFECTS[row[1]]})
assert len(hesper_special) == len(HESPER_EFFECTS), [entry['name'] for entry in hesper_special]
hesper_standard = [{'id': 100 + index, 'name': row[1], 'stat': 'energy_resistance',
                    'slots': [int(value or 0) for value in fire_resistance[2:11]]}
                   for index, row in enumerate([row for row in pool if row[0] == 'hesper_standard'])]
(world / 'enchantments.yml').write_text(
    '# Generated by level_generation/projects/hesper_stage/stage.py from design/kreegan_world/data/enchant_pool.txt.\n'
    + yaml.safe_dump({'schema': 'openyamm.worldEnchantments.v1', 'standard': hesper_standard,
                      'special': hesper_special}, sort_keys=False, default_flow_style=None, width=120))
# The pool lists them too: of Insulation with the standard bonuses, the specials by their grade.
loot_lines[loot_lines.index('enchantments:') + 1] = (
    f"  standard: {json.dumps(standard_pool + [entry['name'] for entry in hesper_standard])}")
for loot_class, grades in (('H1', 'AB'), ('H2', 'BC'), ('H3', 'CD')):
    line = next(i for i, text in enumerate(loot_lines) if text.startswith(f'    {loot_class}: '))
    names = json.loads(loot_lines[line].split(': ', 1)[1]) + [entry['name'] for entry in hesper_special
                                                              if entry['rarity'] in grades]
    loot_lines[line] = f'    {loot_class}: {json.dumps(names)}'
(world / 'loot.yml').write_text('\n'.join(loot_lines) + '\n')
# The worn art (level_generation/ui/hesper_paperdoll): a staged item's fitted paperdoll files (<icon>v1 ... v5a, x2,
# beside its own icon) and its complex_item_pictures row. Without them a worn piece draws its inventory icon whole.
paperdoll = ROOT / 'level_generation/ui/hesper_paperdoll/runtime'
paperdoll_rows = read_table(paperdoll / 'complex_item_pictures.txt')
staged_by_id = {row[0]: row for row in staged_items}
staged_pictures = [row for row in paperdoll_rows[2:] if row[1] in staged_by_id]
for row in staged_pictures:
    files = sorted((paperdoll / 'icons_x2').glob(staged_by_id[row[1]][1] + 'v*.png'))
    assert files or row[3] == 'Gauntlets', row         # gauntlets have no doll files, only a centring point
    for file in files:
        shutil.copy2(file, world / 'icons_x2' / file.name)
write_table(tables / 'complex_item_pictures.txt', paperdoll_rows[:2] + staged_pictures)
# The readables' texts (items.yml `readable`, from design/kreegan_world/quests/READABLES.md): the readable_scrolls
# contribution the readText use action reads (columns as the engine's english/scroll.txt). Always written, as world.yml
# names it.
readable_rows = [[str(item['id']), item['readable'].replace('"', "'"), 'Hesper', item_rows[item['id']][2]]
                 for item in yaml.safe_load((PROJECT / 'items.yml').read_text())['items'] if 'readable' in item]
for row in readable_rows:
    assert item_rows[int(row[0])][22] == 'readText' and '\t' not in row[1], row[0]
# CSV quoting preserves headings and paragraph breaks; the engine's text-table reader accepts multiline cells.
write_table(tables / 'readable_items.txt', [['Item#', 'message text', 'Location', 'Item Name']] + readable_rows)
staged_bindings = assets / 'engine/world_items/items.yml'
staged_bindings.unlink(missing_ok=True)
staged_bindings.write_text(ground_bindings.read_text().rstrip('\n') + '\n' + ''.join(line + '\n'
                                                                                  for line in added_bindings))
run([sys.executable, ROOT / 'tools/item_model_shapes.py', '--bindings', staged_bindings, '--assets', assets])
# The staged items' rows of the design's draft item_effects.txt (its first line is a comment), as the world's
# item_effects contribution: the engine reads energy_resistance and personal_shield after effect_flags.
with (ROOT / 'design/kreegan_world/data/item_effects.txt').open(newline='') as stream:
    effect_draft = [row for row in csv.reader(stream, delimiter='\t') if row and not row[0].startswith('#')]
staged_ids = {row[0] for row in staged_items}
staged_effects = [row for row in effect_draft[1:] if row[0] in staged_ids]
write_table(tables / 'item_effects.txt', [effect_draft[0]] + staged_effects)
# The set bonuses of the design's draft item_sets.txt whose set a staged item names (items column 24, set_id), as the
# world's item_sets contribution: the engine applies a row while that many pieces of its set are worn.
with (ROOT / 'design/kreegan_world/data/item_sets.txt').open(newline='') as stream:
    set_draft = [row for row in csv.reader(stream, delimiter='\t') if row and not row[0].startswith('#')]
staged_sets = {row[24] for row in staged_items if len(row) > 24 and row[24]}
staged_set_rows = [row for row in set_draft[1:] if row[0] in staged_sets]
assert {row[0] for row in staged_set_rows} == staged_sets, 'a staged item names a set with no bonus row'
write_table(tables / 'item_sets.txt', [set_draft[0]] + staged_set_rows)
# The Workshop's mods (design/kreegan_world/data/workshop.txt; ITEMS "Workshop mods") as the world's workshop_mods
# table: id, name, the equip stats it fits, then the item_effects columns (the Shieldbreaker's damage to shields is
# its ShieldDamage20 flag). The gold, the salvage and the unlocks are the Workshop topics' (common/workshop.lua).
effect_columns = effect_draft[0][2:]
WORKSHOP_MODS = [(1, 'Shieldbreaker', 'Weapon|Weapon2|Weapon1or2|Missile', {'effect_flags': 'ShieldDamage20'}),
                 (2, 'Insulation', 'Armor|Helm|Cloak', {'energy_resistance': '20'}),
                 (3, 'Swift Coupling', 'Weapon|Weapon2|Weapon1or2|Missile', {'recovery_reduction_ticks': '10'}),
                 (4, 'Capacitor Link', 'Armor|Shield', {'personal_shield': '300'})]
workshop_names = [row[0] for row in read_table(ROOT / 'design/kreegan_world/data/workshop.txt')[2:] if row and row[0]]
assert [name for _, name, _, _ in WORKSHOP_MODS] == workshop_names, workshop_names
write_table(tables / 'workshop_mods.txt', [['mod_id', 'name', 'fits'] + effect_columns]
            + [[str(mod_id), name, fits] + [effects.get(column, '') for column in effect_columns]
               for mod_id, name, fits, effects in WORKSHOP_MODS])
# Opted-in fixed drops use the engine's existing death-drop table; leave other draft drops for their own builds.
death_drop_ids = {str(item['id']) for item in yaml.safe_load((PROJECT / 'items.yml').read_text())['items']
                  if item.get('death_drop')}
assert death_drop_ids <= staged_ids
with (ROOT / 'design/kreegan_world/data/monster_death_drops.txt').open(newline='') as stream:
    added_drops = [row for row in csv.reader(stream, delimiter='\t') if len(row) >= 6 and row[2] in death_drop_ids]
assert {row[2] for row in added_drops} == death_drop_ids, 'An opted-in item has no death-drop row'
monster_ids = {str(monster['id']) for monster in yaml.safe_load((PROJECT / 'monsters.yml').read_text())['monsters']}
assert all(row[0] in monster_ids for row in added_drops), 'A death-drop monster is not staged'
write_table(assets / 'engine/data_tables/monster_death_drops.txt',
            read_table(DEV / 'engine/data_tables/monster_death_drops.txt') + added_drops)


# --- NPCs, their topics, the journal --------------------------------------------------------------------------------
# npcs.yml: rows appended to the stage copies of the engine's NPC tables (the engine reads them only from
# engine/data_tables), the portraits as npc<id>.png in the world's icons, and the topics' Lua as the world's global
# overlay (events/Global_<name>.lua: a topic runs the global event of its id; worlds/hesper is mounted only with the
# world). The native files are CRLF text, partly not UTF-8, with quoted multi-line cells: the rows are appended as
# bytes, the native rows left untouched.
# npcs.yml holds the arrival's people, Aster and the shared news; npcs_<place>.yml files (one per map project's people)
# add theirs. Each file may have npcs, topics, quests, autonotes, houses and vendors; they are merged in name order.
NPC_SECTIONS = ('npcs', 'topics', 'quests', 'autonotes', 'houses', 'vendors')
npc_input = {section: [] for section in NPC_SECTIONS}
for path in [PROJECT / 'npcs.yml'] + sorted(PROJECT.glob('npcs_*.yml')):
    data = yaml.safe_load(path.read_text()) or {}
    assert set(data) <= set(NPC_SECTIONS), (path.name, set(data) - set(NPC_SECTIONS))
    for section in NPC_SECTIONS:
        npc_input[section] += data.get(section) or []
for section, key in (('npcs', 'id'), ('topics', 'id'), ('quests', 'qbit'), ('autonotes', 'id'), ('houses', 'id'),
                     ('vendors', 'id')):
    keys = [entry[key] for entry in npc_input[section]]
    assert len(keys) == len(set(keys)), (section, sorted({k for k in keys if keys.count(k) > 1}))


def append_rows(relative, rows):
    native = (DEV / 'engine/data_tables' / relative).read_bytes()
    if not native.endswith(b'\n'):
        native += b'\r\n'
    for row in rows:
        assert all('\t' not in cell and '\n' not in cell and '"' not in cell for cell in row), row
    added = ''.join('\t'.join(row) + '\r\n' for row in rows).encode('ascii')
    (assets / 'engine/data_tables' / relative).write_bytes(native + added)


def native_ids(relative):
    text = (DEV / 'engine/data_tables' / relative).read_bytes().decode('latin-1')
    return {line.split('\t', 1)[0] for line in text.splitlines() if line.split('\t', 1)[0].isdigit()}


npc_rows, greet_rows, topic_rows = [], [], []
taken = {name: native_ids(name) for name in ('npc.txt', 'npc_greet.txt', 'npc_topic.txt')}
icons = world / 'icons_x2'
icons.mkdir(exist_ok=True)
extra_slots = []                                    # (npc, slot, topic): the topics past an NPC's six slots
for npc in npc_input['npcs']:
    key = str(npc['id'])
    assert key not in taken['npc.txt'] and key not in taken['npc_greet.txt'], npc['id']
    topics = [str(topic) for topic in npc['topics'][:6]] + ['0'] * max(0, 6 - len(npc['topics']))
    extra_slots += [(npc['id'], slot, topic) for slot, topic in enumerate(npc['topics']) if slot >= 6]
    # # Name Pic A B C 2D-location profession greet join topics A-F notes. `house`: the house the NPC lives in (a map
    # event that moves an NPC by QBits uses evt.MoveNPC, which overrides it).
    npc_rows.append([key, npc['name'], key, '0', '0', '0', str(npc.get('house', 0)), '0', key, '0'] + topics +
                    ['Hesper (stage)'])
    greet_rows.append([key, npc['greeting'][0], npc['greeting'][1], '', 'Hesper'])
    if 'portrait' in npc:                           # none until the NPC's own portrait is painted
        shutil.copy2(portrait_source(npc['portrait']), icons / f'npc{npc["id"]:04d}.png')
lua = ['-- Generated by level_generation/projects/hesper_stage/stage.py from its npcs.yml: the Hesper NPCs\' topics.']
SLOT_EVENTS = (9098, 9099)                          # the extra slots' on-load event and NPC-enter hook (no topics)
for topic in npc_input['topics']:
    key = str(topic['id'])
    assert key not in taken['npc_topic.txt'] and topic['id'] not in SLOT_EVENTS, topic['id']
    topic_rows.append([key, topic['title'], '0', '', '', 'Hesper'])
    if 'map_event' in topic:                        # no global event: the map's own event of the topic's id runs
        assert 'lua' not in topic, topic['id']
    else:
        body = '\n'.join('    ' + line for line in topic['lua'].rstrip('\n').split('\n'))
        lua.append(f'\nRegisterGlobalEvent({key}, {json.dumps(topic["title"])}, function()\n{body}\nend)')
    # show_after / show_until QBits: one condition per topic (a second RegisterCanShowTopic replaces the first).
    shown = ([f'IsQBitSet(QBit({topic["show_after"]}))'] if 'show_after' in topic else []) + \
            [f'not IsQBitSet(QBit({qbit}))' for qbit in
             (topic['show_until'] if isinstance(topic.get('show_until'), list) else [topic.get('show_until')])
             if qbit is not None]
    if shown:
        lua.append(f'RegisterCanShowTopic({key}, function() return {" and ".join(shown)} end)')
if extra_slots:
    # npc.txt has six topic slots (A-F); the engine lists override slots past them (evt.SetNPCTopic), so the extra
    # topics are set on every map load and whenever their NPC's dialogue opens.
    rows = ', '.join(f'{{{npc}, {slot}, {topic}}}' for npc, slot, topic in extra_slots)
    lua.append(f'\nlocal HESPER_EXTRA_TOPICS = {{{rows}}}\n'
               'local function setHesperExtraTopics(npcId)\n'
               '    for _, entry in ipairs(HESPER_EXTRA_TOPICS) do\n'
               '        if npcId == nil or npcId == entry[1] then evt.SetNPCTopic(entry[1], entry[2], entry[3]) end\n'
               '    end\n'
               'end\n'
               f'RegisterGlobalOnLoadEvent({SLOT_EVENTS[0]}, "Hesper NPCs\' extra topic slots", function() '
               'setHesperExtraTopics(nil) end)\n'
               f'RegisterGlobalNpcEnterHook({SLOT_EVENTS[1]}, "Hesper NPCs\' extra topic slots", function(context) '
               'setHesperExtraTopics(context.npcId) end)')
append_rows('npc.txt', npc_rows)
append_rows('npc_greet.txt', greet_rows)
append_rows('npc_topic.txt', topic_rows)
assert not native_ids('english/quests.txt') & {str(q['qbit']) for q in npc_input['quests']}
append_rows('english/quests.txt', [[str(q['qbit']), q['text'], q['notes'], 'Hesper'] for q in npc_input['quests']])
assert not native_ids('english/autonote.txt') & {str(a['id']) for a in npc_input['autonotes']}
append_rows('english/autonote.txt', [[str(a['id']), a['text'], a['category'], '', ''] for a in npc_input['autonotes']])
(world / 'events').mkdir(exist_ok=True)
(world / 'events/Global_hesper.lua').write_text('\n'.join(lua) + '\n')

# --- Shared map Lua -------------------------------------------------------------------------------------------------
# The engine runs the world's events/common/hesper_common.lua before every Hesper map script (and the global one):
# the files of common/ in name order (pickups.lua: the dungeon pickups, PICKUPS.md).
(world / 'events/common').mkdir(exist_ok=True)
(world / 'events/common/hesper_common.lua').write_text(
    '-- Generated by level_generation/projects/hesper_stage/stage.py from its common/*.lua.\n'
    + '\n'.join(f'\n-- {path.name}\n' + path.read_text() for path in sorted((PROJECT / 'common').glob('*.lua'))))
# The pickups' decoration swaps as an overlay of each map that places pickups: the game loads a map's decoration
# models from its placements and the literal SetSprite targets of its own scripts only (pickup_sprites.lua).
for entry in installed:
    script = world / 'events/maps' / (Path(entry['file']).stem + '.lua')
    overlay = script.with_name(f'{script.stem}_pickups.lua')
    if script.exists() and 'HesperPickups.setup' in script.read_text(errors='replace'):
        shutil.copy2(PROJECT / 'pickup_sprites.lua', overlay)
    elif overlay.exists():
        overlay.unlink()

# --- Terrain materials ----------------------------------------------------------------------------------------------
library_path = assets / 'engine/terrain_materials/library.yml'
library = yaml.safe_load((DEV / 'engine/terrain_materials/library.yml').read_text())
hesper_library = yaml.safe_load((PROJECT / 'terrain_library.yml').read_text())['materials']
assert not set(hesper_library) & set(library['materials'])
library['materials'].update(hesper_library)
library_path.write_text('# Stage copy: assets_dev/engine/terrain_materials/library.yml plus Hesper\'s '
                        '(level_generation/projects/hesper_stage/terrain_library.yml).\n'
                        + yaml.safe_dump(library, sort_keys=False))
run([sys.executable, ROOT / 'tools/terrain_materials.py', 'cook', '--profile', 'desktop', '--output', assets]
    + sorted(hesper_library))

# --- Sky ------------------------------------------------------------------------------------------------------------
sky_path = assets / 'engine/rendering/sky/sky.yml'
sky = yaml.safe_load((DEV / 'engine/rendering/sky/sky.yml').read_text())
registered = {entry['file'] for entry in installed}
# Every zone's preset and theme (design/kreegan_world/zone<N>/sky_preset.yml: zone 1's hesper_ash, the zones' own
# presets inheriting from it), and each installed map's theme.
for preset_file in sorted((ROOT / 'design/kreegan_world').glob('zone*/sky_preset.yml')):
    hesper_sky = yaml.safe_load(preset_file.read_text())
    for section in ('presets', 'themes'):
        assert not set(hesper_sky.get(section) or {}) & set(sky[section]), preset_file
        sky[section].update(hesper_sky.get(section) or {})
    sky['maps'].update({name: theme for name, theme in (hesper_sky.get('maps') or {}).items() if name in registered})
sky_path.write_text('# Stage copy of assets_dev/engine/rendering/sky/sky.yml with the Hesper preset and theme.\n'
                    + yaml.safe_dump(sky, sort_keys=False, width=120))
# The sky textures: the night sky with the debris ring, and the layers of design/kreegan_world/art/sky/make_sky.py.
# The panoramas (stars, the horizon band) and the moon have one level, as they wrap at the atan2 seam; the cloud
# layer keeps its mips (the line format of tools/cook_sky_textures.py).
SKY_TEXTURES = [(ART / 'sky/hesper_night.png', False), (ART / 'sky/runtime/hesper_horizon.png', False),
                (ART / 'sky/runtime/hesper_moon.png', False), (ART / 'sky/runtime/hesper_ashveil.png', True)]
# The zones' own layers (art/sky/hes_out<N>/runtime, from each folder's make_sky script): horizon bands and night skies
# (panoramas) without mips, cloud layers with them.
SKY_TEXTURES += [(path, 'horizon' not in path.stem and 'night' not in path.stem)
                 for path in sorted(ART.glob('sky/hes_out*/runtime/*.png'))]
receipts_path = stage / 'sky_receipts.json'
receipts = json.loads(receipts_path.read_text()) if receipts_path.exists() else {}
jobs = []
for source, mips in SKY_TEXTURES:
    cooked = sky_path.parent / (source.stem + '.oytex')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    if cooked.exists() and receipts.get(cooked.name) == digest:
        continue
    jobs.append('\t'.join((str(source), str(cooked), 'bc7', 'linear', '0', '1' if mips else '0', '8192', '0',
                           digest, 'model')))
    receipts[cooked.name] = digest
if jobs:
    with tempfile.TemporaryDirectory() as scratch:
        job_file = Path(scratch) / 'jobs.tsv'
        job_file.write_text('\n'.join(jobs) + '\n')
        run([ROOT / 'build/game/openyamm_model_texture_cook', job_file])
    receipts_path.write_text(json.dumps(receipts, indent=1) + '\n')

# --- Weather --------------------------------------------------------------------------------------------------------
# weather.yml's per-map entries for the Hesper maps (weather.yml next to this script): ash fall on Starport Reach.
weather_path = assets / 'engine/rendering/weather/weather.yml'
weather = yaml.safe_load((DEV / 'engine/rendering/weather/weather.yml').read_text())
hesper_weather_input = yaml.safe_load((PROJECT / 'weather.yml').read_text())
hesper_weather = hesper_weather_input['maps']
assert not set(hesper_weather) & set(weather['maps'])
weather['maps'].update({name: entry for name, entry in hesper_weather.items() if name in registered})
# Hesper's own flake looks (ember) beside the engine's snow and ash.
assert not set(hesper_weather_input.get('flakes', {})) & set(weather['flakes'])
weather['flakes'].update(hesper_weather_input.get('flakes', {}))
weather_path.write_text('# Stage copy of assets_dev/engine/rendering/weather/weather.yml with the Hesper maps '
                        '(level_generation/projects/hesper_stage/weather.yml).\n'
                        + yaml.safe_dump(weather, sort_keys=False, width=120))

# --- Liquids ---------------------------------------------------------------------------------------------------------
# Hesper's liquids (liquids.yml next to this script) ahead of the shared ones, and the coverage masks of the MM8 water
# shore tiles its maps draw the brine with (worlds/<world>/terrain_materials/liquid_edges, read by the world's id).
liquids_path = assets / 'engine/liquids/liquids.yml'
hesper_liquids = (PROJECT / 'liquids.yml').read_text()
shared_liquids = (DEV / 'engine/liquids/liquids.yml').read_text()
assert yaml.safe_load(hesper_liquids)['liquids'] and shared_liquids.count('\nliquids:\n') == 1
liquids_path.write_text('# Stage copy of assets_dev/engine/liquids/liquids.yml with Hesper\'s liquids first '
                        '(level_generation/projects/hesper_stage/liquids.yml).\n'
                        + shared_liquids.replace('\nliquids:\n', '\nliquids:\n' + hesper_liquids.split('\nliquids:\n', 1)[1]
                                                 + '\n', 1))
assert [entry['id'] for entry in yaml.safe_load(liquids_path.read_text())['liquids']][:1] == ['rust_brine']
edges = world / 'terrain_materials/liquid_edges'
edges.mkdir(parents=True, exist_ok=True)
for pattern in ('wtrdr*.png', 'lvdr*.png', 'tr*.png'):   # the brine's shores, the Scour's molten slag's (the lava
                                                        # tiles) and the Brood Spires' acid's (the tar tiles)
    for mask in sorted((DEV / 'worlds/mm8/terrain_materials/liquid_edges').glob(pattern)):
        shutil.copy2(mask, edges / mask.name)

# --- Tech skills ----------------------------------------------------------------------------------------------------
# skills.yml: the houses that sell the technology skills' Novice, the Expert and Master teachers, the skill sheet's
# descriptions and the map events entering the houses (skills_stage.py; after the NPC section, whose tables it extends).
sys.path.insert(0, str(PROJECT))
import skills_stage  # noqa: E402
tech_skills = skills_stage.install(PROJECT, DEV, assets, world, {entry['file']: entry['id'] for entry in registry},
                                   portrait_source)

# --- Houses and vendors (npcs*.yml) -----------------------------------------------------------------------------------
# houses: plain houses and temples in the integrator's block 9450-9499 (design/kreegan_world/WORK_PACKAGES/README.md),
# appended to the stage copy of house_data.txt after the tech-skill houses; their people live in them by npc.txt's 2D
# location (`house`), and the map events enter them (each map project's own handlers). type House (talk only) or Temple
# (heal and donate: MM's Donate lowers the reputation). hours: [open, close], MM's hours (0, 0: always open).
# vendors: shops with a fixed stock (the engine's deterministic vendor stock, as MM9's vendors), the world's vendors,
# vendor_aliases and vendor_stock contributions; `stock` is [item, quantity] per slot (up to eight), the special lane
# `special` or the same list. Restocked every `restock_days`.
map_numbers = {entry['file']: entry['id'] for entry in registry}
# The house blocks of the packages' maps (9300-9449: the Scour, the Brood Spires, the Crown) and the integrator's
# (9450-9499), design/kreegan_world/WORK_PACKAGES/README.md.
HOUSE_IDS = range(9300, 9500)
house_rows = []
for house in npc_input['houses']:
    kind = house.get('type', 'House')
    assert kind in ('House', 'Temple', 'Town Hall', 'Tavern') and house['id'] in HOUSE_IDS, house
    open_hour, close_hour = house.get('hours', [0, 0])
    # # # Type Map Picture Name Proprietor Title Picture State Rep Per Val A B C Notes Notes(2) Open Closed Pic Map
    # Restrictions EnterText OfferedSkills (Val: the price multiplier, a temple's donation and healing price).
    # teaches / skill_price: a house that also sells tech skills' Novice (A: the price, x 500 gold), as skills.yml's
    # houses do; skills the engine does not know yet are left out (skills_stage.offered). A house that teaches nothing
    # says `none`, so the engine does not give it its type's MM skills (a Tavern's Stealing, Disarm Traps, Perception).
    # price_after: {qbit, price}: the price once the party has the QBit (house_data cell 25, "qbit:multiplier").
    house_rows.append([str(house['id']), '0', kind, str(map_numbers.get(house['map'], 0)), str(house.get('picture', 27)),
                       house['name'], '', '', '0', '0', '0', '0', str(house.get('price', 1)),
                       str(house.get('skill_price', 1)), '', '0', 'Hesper (stage)', '', str(open_hour),
                       str(close_hour), '0', '0', '0', '', skills_stage.offered(house.get('teaches', [])) or 'none',
                       ('{qbit}:{price}'.format(**house['price_after']) if 'price_after' in house else '')])
house_table = assets / 'engine/data_tables/house_data.txt'
assert not skills_stage.native_ids(house_table) & {int(row[0]) for row in house_rows}
data = house_table.read_bytes()
house_table.write_bytes(data + (b'' if data.endswith(b'\n') else b'\r\n') + skills_stage.encode(house_rows))
VENDOR_COLUMNS = ['vendor_id', 'package_id', 'source_vendor_id', 'canonical_id', 'name', 'location', 'source_type',
                  'merchandise', 'profile', 'magic_school', 'wealth', 'merchant_base', 'standard_min', 'standard_max',
                  'standard_concat_percent', 'special_min', 'special_max', 'special_concat_percent', 'restock_days',
                  'can_sell', 'can_identify', 'can_repair', 'scene_policy', 'opening_policy', 'source_line',
                  'source_quantity', 'source_restock', 'source_file', 'normalized_service_type',
                  'legacy_house_audio_policy', 'legacy_house_video_policy', 'open_hour', 'close_hour',
                  'resale_cap_percent']
vendor_rows, alias_rows, stock_rows = [], [], []
staged_item_ids = {int(row[0]) for row in staged_items}
for vendor in npc_input['vendors']:
    key = str(vendor['id'])
    assert vendor['id'] in HOUSE_IDS, vendor
    vendor_rows.append([key, 'hesper', key, f'hesper:vendor/{key}', vendor['name'], vendor['location'], 'General Store',
                        vendor['merchandise'], 'Mm9GeneralStore', '', 'Moderate', str(vendor.get('price', 1)), '1', '2',
                        '0', '1', '2', '0', str(vendor.get('restock_days', 7)), '1', '0', '0',
                        'HouseVideo' if vendor.get('picture') else 'LiveGameplay', '', '0',
                        '', '', 'level_generation/projects/hesper_stage', 'Shop', 'Disabled',
                        'Enabled' if vendor.get('picture') else 'Disabled',
                        *[str(hour) for hour in vendor.get('hours', [0, 0])],
                        # Hesper's vendors pay at most 30 % of an item's value, whatever the Merchant skill (ITEMS,
                        # "The economy check"); the Workshop buys salvage at full value (common/workshop.lua).
                        str(vendor.get('resale_cap', 30))])
    alias_rows.append([key, 'hesper', key, '0', ''])
    for lane in ('standard', 'special'):
        stock = vendor['stock'] if lane == 'standard' else vendor.get('special', vendor['stock'])
        # An entry is [item, quantity] or [item, quantity, objectives]: sold once the party has done that many of the
        # world's major objectives (world.yml objectives; ITEMS "Who sells what"). The general-store profile wants
        # every page full, so a list repeats its entries in order up to whole pages of eight: an untiered one fills
        # its one page; a tiered one is written whole, and the engine shows eight of what the party has earned each
        # restock.
        tiered = any(len(entry) > 2 and entry[2] > 0 for entry in stock)
        assert 0 < len(stock) and (tiered or len(stock) <= 8), vendor
        stock = [stock[slot % len(stock)] for slot in range(8 * ((len(stock) + 7) // 8))]
        for index, (item, quantity, *gate) in enumerate(stock):
            assert item in staged_item_ids, (vendor['id'], item)
            stock_rows.append([key, lane, str(index // 8), str(index % 8), str(item), str(quantity), '1', '0', '0',
                               '0', '1', str(gate[0] if gate else 0)])
write_table(tables / 'vendors.txt', [VENDOR_COLUMNS] + vendor_rows)
write_table(tables / 'vendor_aliases.txt', [['vendor_id', 'package_id', 'source_vendor_id', 'source_line',
                                             'rude_source_files']] + alias_rows)
write_table(tables / 'vendor_stock.txt', [['vendor_id', 'lane', 'page', 'slot', 'item_id', 'quantity', 'identified',
                                           'standard_enchant_id', 'standard_enchant_power', 'special_enchant_id',
                                           'generation_version', 'min_objectives']] + stock_rows)

# --- House backdrops ------------------------------------------------------------------------------------------------
# Numeric pictures need both animation and movie rows; the clips themselves belong to the Hesper world.
backdrops = json.loads((ROOT / 'level_generation/ui/hesper_house_backdrops/backdrops.json').read_text())
venues = yaml.safe_load((PROJECT / 'skills.yml').read_text())['houses'] + npc_input['houses'] + npc_input['vendors']
pictures = {house: backdrop['picture'] for backdrop in backdrops for house in backdrop['houses']}
assert len(pictures) == sum(len(backdrop['houses']) for backdrop in backdrops)
assert len({backdrop['picture'] for backdrop in backdrops}) == len(backdrops)
assert set(pictures) == {venue['id'] for venue in venues}, 'Update the house-backdrop inventory for new venues'
assert all(venue['picture'] == pictures[venue['id']] for venue in venues)
movies = world / 'videos/Houses'
movies.mkdir(parents=True, exist_ok=True)
movie_rows = []
for backdrop in backdrops:
    source = ROOT / backdrop['source']
    assert source.suffix == '.ogv' and source.is_file(), source
    shutil.copy2(source, movies / source.name)
    movie_rows.append([str(backdrop['picture']), source.stem, '0', 'House', '0'])
skills_stage.append_from_assets_dev(DEV, assets, 'house_movies.txt', movie_rows)
# Residents stay in npc.txt (including MoveNPC gates); no inherited native house voices or portraits.
animation_rows = [[str(venue['id']), str(venue['picture']), venue['name'], '', '', '', '0', '0', '0', '']
                  for venue in venues]
skills_stage.append_from_assets_dev(DEV, assets, 'house_animations.txt', animation_rows)

# --- Loading pages --------------------------------------------------------------------------------------------------
loading_pages = [f'hes_loading{number}.png' for number in range(1, 5)]
for name in loading_pages:
    source = ROOT / 'level_generation/ui/hesper_loading/selected' / name
    with Image.open(source) as page:
        assert page.size == (1280, 960) and page.mode == 'RGB', source
    shutil.copy2(source, world / 'icons_x2' / name)

# --- Sounds ---------------------------------------------------------------------------------------------------------
# audio.yml (design/kreegan_world/AUDIO.md): the picked ElevenLabs WAVs into worlds/hesper/audio/hesper (named
# placeholders such as the shields' play them by file name), sounds.txt rows 90000+ for the names tables refer to by
# number, and the staged monsters' descriptor sound columns (audio_stage.py; after the monster section).
import audio_stage  # noqa: E402
audio = audio_stage.install(ROOT, PROJECT, DEV, assets, world)

report = {'stage': str(assets), 'maps': [entry['file'] for entry in installed], 'textures': len(names),
          'decorations': len(decoration_rows), 'monsters': [m['id'] for m in monster_input['monsters']],
          'monster_tactics': sorted(tactics), 'monster_modifiers': sorted(staged_modifiers),
          'items': [int(row[0]) for row in staged_items],
          'monster_models': monster_input['models'], 'tech_skills': tech_skills,
          'npcs': len(npc_input['npcs']), 'topics': len(npc_input['topics']),
          'houses': [h['id'] for h in npc_input['houses']], 'vendors': [v['id'] for v in npc_input['vendors']],
          'readables': [int(row[0]) for row in readable_rows], 'audio': audio}
# Swap the finished stage in (game runs and builds hold stage.lock shared, this run holds it exclusive).
retired = stage / 'assets_editor_dev.old'
if retired.exists():
    shutil.rmtree(retired)
if live.exists():
    live.rename(retired)
assets.rename(live)
if retired.exists():
    shutil.rmtree(retired)
report['stage'] = str(live)
(stage / 'stage_report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
