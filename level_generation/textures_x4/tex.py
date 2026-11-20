#!/usr/bin/env python3
"""Central x4 surface-texture pipeline for MM6-MM8 BLV and outdoor BModel face textures, and MM9 remade maps.

Commands (run from anywhere):
  inventory [--world W] [--map M]
                             rebuild inventory.json from maps, events and native sources (only W's entries with
                             --world; --map adds a map to a scoped world such as mm9)
  status                     counts per world and status
  next --count N [...]       claim a coherent set of pending textures and create jobs (--names: only these)
  gen [JOB...] [--world W]    keep --parallel codex exec workers busy across jobs (all open jobs by default);
                             one scheduler per world can run at once, or one for all worlds
  materials JOB < lines      set per-texture material text (name: description) before gen
  retry JOB NAME --note TXT  queue another version of one texture with an extra prompt note
  check JOB                  build candidates, metrics, contact sheet and review page
  accept JOB [NAME[@vN]...]  accept candidates (default: every passing latest candidate)
  reject JOB NAME --reason   reject the latest candidate of NAME (it stays claimed)
  release JOB [NAME...]      return claimed textures to pending
  import-codex-mm6           accept the 82 masters from the earlier Codex MM6 study
  calibrate [--target T]     re-gain every master to the shared brightness target (native or esrgan)
  rebuild [--world W]        rebuild accepted family masters from their raws with the current recipe
  verify-families            check that family masters still carry their sources' exact shared pixels
  alpha-from-native ID...    give accepted opaque masters of alpha natives the native's alpha at 4x (MM9 32-bit BMPs)
  redo [NAME...] [--world W] --reason R
                             reopen accepted textures for regeneration with the current recipe
  stage RUN [--tier x4|x2]   hard-link assets_dev into output/textures_x4_runs/RUN with accepted masters
  install [--world W]        accepted masters as the game's tier sources (assets_source); MM9 also cooked into the
                             review root (output/mm9_rework/assets_dev) through review_root.install()
  play RUN --world W --map M print/run the run_game command for a staged run
"""
import argparse
import concurrent.futures
import contextlib
import fcntl
import hashlib
import functools
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'util'))

WORLDS = ['mm6', 'mm7', 'mm8', 'mm9']
SKY_TEXTURES = {'stormclds'}  # sky art on BModel faces whose names do not say so; out of scope like sky
ESRGAN_X4 = {'mm6': 'out_prod_bmodel', 'mm7': 'out_prod_bmodel_mm7', 'mm8': 'out_prod_bmodel_mm8',
             'mm9': 'out_prod_bmodel_mm9'}
# MM9 (the rework): the remade native maps live in the isolated review root, not in assets_dev, and only the maps named
# in the inventory's `map_scope` are read (`inventory --world mm9 --map anskramkeep.blv`). Its natives are the
# importer's decoded DTX bitmaps (10-character aliases, in assets_source/worlds/mm9/textures); the tiers are installed
# into the review root (`install`).
REVIEW_ROOT = ROOT / 'output/mm9_rework/assets_dev'
WORLD_CONTENT = {'mm9': REVIEW_ROOT / 'worlds/mm9'}         # maps/ and events/maps/ per world (default assets_dev)
SCOPED_WORLDS = {'mm9'}                                      # worlds inventoried only for their map_scope
TILED_MATERIAL_WORLDS = {'mm9'}                              # independently tiling materials (see set_neighbors)
# MM9 helper materials (collision-only, editor helpers): never drawn, so out of scope like sky.
MM9_HELPER_TEXTURES = {'invisible', 'black', 'greenscreen', 'perception', 'occluder', 'sky', 'skyportal',
                       'default', 'firethrough',  # 'default': LithTech's checker on MM9's invisible collision brushes
                       'monster', 'item'}         # the editor's spawn markers (A1IsleofAshes\\misc, on the Bootcamp)
# MM9 sources out of scope by their DTX folder or kind (2026-10-31): skybox art (starfield, the Arslegaard cube,
# Clouds1) is sky; animated `.spr` surfaces and the water/slime frame folders belong to the water shader
# (`liquids.yml`) or the texture frame table (MM9 visual properties, bit 0x4000), not to one static master.
MM9_SKY_FOLDERS = {'skybox'}
MM9_WATER_FOLDERS = {'water', 'water115', 'water125', 'slime', 'ocean'}   # 'ocean': Ocean4's frames (SpriteTextures)
# MM9 outdoor maps (2026-11-02): until each region is rebuilt as an outdoor BLV, its textures are read from the old
# import's ODM (output/mm9_rework/assets_dev/worlds/mm9/maps/<region>.odm), whose `MM9_*` BModels are the props and
# objects (trees, barrels, statues, chests) that the outdoor BLVs place as decoration models: their skins are the
# props' job, not surface masters. Without them an old ODM names the same surface textures as its outdoor BLV
# (Sturmford: 31 against the BLV's 32, the difference helpers).
MM9_ODM_PROP_PREFIX = 'MM9_'
# What the prompt calls the game and its source artefacts (MM6-MM8: 8-bit palette art; MM9: DXT1-compressed 3D art).
ERA = {'mm9': ('an early-2000s 3D first-person RPG remaster',
               'Any 4x4 block or banding artefact of texture compression in the reference is an artefact: paint '
               'smooth continuous material.')}
ERA_DEFAULT = ('a 1990s first-person RPG remaster',
               'Any fine checkered or crosshatch dither in the reference is a palette artefact: paint smooth '
               'continuous material.')
INVENTORY = HERE / 'inventory.json'
LEDGER = HERE / 'ledger.jsonl'
JOBS = HERE / 'jobs'
MASTERS = HERE / 'masters'
RUNS = ROOT / 'output' / 'textures_x4_runs'
SCALE = 4
JOB_SIZE = 24

# Acceptance thresholds for automatic flags (the visual review still decides).
MIN_GAIN, MAX_GAIN = 0.3, 2.0  # overall calibration gain outside this range means the art drifted too far
MAX_HUE_SPREAD = 0.45         # log spread between significant channel gains (colour drift, not brightness)
MIN_LAYOUT_CORRELATION = 0.80  # blurred native vs reduced candidate luma correlation
MAX_REGISTRATION_SHIFT = 1.5  # native pixels
MAX_TRACED = 0.15             # fine-detail correlation with the native pixel staircase (copied raster/dither)
DEFAULT_REF_BLUR = 1.2        # native-pixel blur of references: keeps layout, removes pixel noise the model would trace
CONFIG = HERE / 'config.json'  # {"brightness": "native" | "esrgan"}: shared calibration target of every master
RELATION_MIN_SHARED = 0.15     # share of a texture's pixels identical to another texture at some offset
# Engraved glyph plates share their blank plate exactly, but each glyph meets it along a curved native-pixel
# staircase: copying a relative's plate pixels left stair-stepped glyph edges and ghost strokes of the other glyphs
# (MM8 alphanum plates, 2026-10-09). They are generated independently.
NO_FAMILY_PREFIXES = ('mm8/alphanum',)
COPY_TOLERANCE = 8.0          # mean per-channel native difference allowed for `retry --copy-from`
FULL_COVERAGE = 0.995          # a texture this covered by accepted relatives is derived without generation
MAX_DERIVED_GAP = 4            # largest uncovered native-pixel patch a derived texture may fill from its neighbours
BLOCK = 8                      # exact-match block size for relation search
SEAM_TOLERANCE = 1.5          # wrap-boundary contrast may exceed the native's own boundary contrast by this factor


def esrgan_x4(world, name, cache={}):
    """Saved Real-ESRGAN x4 output for a native texture (filenames are mixed case)."""
    if world not in cache:
        directory = ROOT / 'tools/upscaling' / ESRGAN_X4[world]
        cache[world] = {path.stem.lower(): path for path in directory.glob('*.png')} if directory.is_dir() else {}
    return cache[world].get(name.lower())


def world_content(world):
    return WORLD_CONTENT.get(world, ROOT / 'assets_dev/worlds' / world)


def world_map_paths(world, scope=None):
    """The maps a world's inventory reads: every BLV/ODM of its maps folder, or only `scope` for scoped worlds."""
    maps_dir = world_content(world) / 'maps'
    paths = sorted(maps_dir.glob('*.blv')) + sorted(maps_dir.glob('*.odm'))
    if world in SCOPED_WORLDS:
        wanted = {name.lower() for name in scope or []}
        paths = [path for path in paths if path.name.lower() in wanted]
    return paths


@functools.lru_cache(maxsize=None)
def mm9_alias_sources():
    """MM9 alias -> original DTX path (`*.material_aliases.yml` of every MM9 map): names the helper materials and
    gives the reviewer the original material name."""
    import yaml
    sources = {}
    for path in sorted((ROOT / 'assets_dev/worlds/mm9/maps').glob('*.material_aliases.yml')):
        for item in (yaml.safe_load(path.read_text()) or {}).get('textures') or []:
            sources.setdefault(item['alias'].lower(), item['source_texture'])
    return sources


@contextlib.contextmanager
def job_lock(job_dir):
    """Serialises read-modify-write of one job.json between the scheduler and review commands."""
    with open(Path(job_dir) / '.lock', 'w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def load_json(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(data, indent=1, sort_keys=False) + '\n')
    tmp.replace(path)


# ----------------------------------------------------------------------------------------------- ledger

def ledger_append(records):
    with open(LEDGER, 'a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        for record in records:
            stream.write(json.dumps({'ts': now(), **record}, sort_keys=True) + '\n')
        fcntl.flock(stream, fcntl.LOCK_UN)


def ledger_state():
    """Fold the ledger into {id: {'status', 'job', 'master', 'version'}}."""
    state = {}
    if not LEDGER.exists():
        return state
    for line in LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        entry = state.setdefault(event['id'], {'status': 'pending'})
        kind = event['event']
        if kind == 'claim':
            if entry['status'] != 'accepted':
                entry.update(status='claimed', job=event['job'])
        elif kind == 'candidate':
            if entry['status'] != 'accepted':
                entry.update(status='candidate', job=event['job'], version=event['version'])
        elif kind == 'reject':
            if entry['status'] != 'accepted':
                entry.update(status='claimed')
        elif kind == 'accept':
            entry.update(status='accepted', job=event.get('job'), master=event['master'],
                         version=event.get('version'))
        elif kind == 'reopen':
            entry.update(status='claimed', job=event['job'])
        elif kind == 'unaccept':
            entry.update(status='pending', master=None)
        elif kind == 'release':
            if entry['status'] != 'accepted':
                entry.update(status='pending', job=None)
    return state


# -------------------------------------------------------------------------------------------- inventory

class NativeSources:
    """Original bitmaps: world source textures (assets_source), the MMerge LOD export, then the runtime world ZIP."""

    def __init__(self, world):
        self.world = world
        self.files = {}
        for directory in [ROOT / 'reference/mmerge_data_forus/Data' / f'{world}.bitmaps.lod',
                          ROOT / 'assets_source/worlds' / world / 'textures']:
            if directory.is_dir():
                for path in directory.iterdir():
                    if path.suffix.lower() in ('.bmp', '.png'):
                        self.files[path.stem.lower()] = ('file', path)
        archive = ROOT / 'assets/worlds' / f'{world}.zip'
        self.zip = zipfile.ZipFile(archive) if archive.exists() else None
        if self.zip:
            for info in self.zip.infolist():
                parts = info.filename.split('/')
                if len(parts) == 2 and parts[0] == 'textures' and parts[1].lower().endswith(('.bmp', '.png')):
                    self.files.setdefault(Path(parts[1]).stem.lower(), ('zip', info.filename))

        for entry_id, spec in periodic_bases().items():
            world, name = entry_id.split('/')
            if world == self.world:
                self.files[name] = ('periodic', spec)

    def path(self, name):
        found = self.files.get(name)
        if not found:
            return None
        if found[0] == 'periodic':
            source = self.path(found[1]['from'].split('/')[1])
            return f"{source}#period{found[1]['period'][0]}x{found[1]['period'][1]}"
        return rel(found[1]) if found[0] == 'file' else f'assets/worlds/{self.world}.zip:{found[1]}'

    def image(self, name):
        found = self.files.get(name)
        if not found:
            return None
        if found[0] == 'periodic':
            return periodic_base_image(self.image(found[1]['from'].split('/')[1]), found[1]['period'],
                                       found[1].get('exclude'))
        if found[0] == 'file':
            return bmp32_alpha(Image.open(found[1]), found[1])
        with self.zip.open(found[1]) as stream:
            image = Image.open(stream)
            image.load()
            return image


PERIODIC_BASES = HERE / 'periodic_bases.json'  # {base id: {"from": texture id, "period": [px, py]}}


@functools.lru_cache(maxsize=None)
def periodic_bases():
    """Tiled bases under a foreground: a texture painted as a small repeating pattern with something on top (the MM9
    Anskram ceiling: a 32-pixel lattice under crossed beams). The base's native is the pattern alone, reconstructed as
    the per-phase median of the source's cells (the foreground covers each phase in a minority of the cells); it is
    generated once as its own seamless tile, and the source is composed on it (`compose.json` with `refine: diff`), so
    only the foreground is painted over the finished pattern. A base has no faces and is never installed."""
    return load_json(PERIODIC_BASES, {}) or {}


def periodic_base_image(source, period, exclude=None):
    """The repeating pattern under a foreground: per phase, the median of the source's cells, leaving out pixels of
    the `exclude` mask (the foreground) where enough cells remain."""
    rgb = np.asarray(source.convert('RGB')).astype(float)
    height, width = rgb.shape[:2]
    px, py = period
    offsets = [(y, x) for y in range(0, height - py + 1, py) for x in range(0, width - px + 1, px)]
    cells = np.stack([rgb[y:y + py, x:x + px] for y, x in offsets])
    if exclude is not None:
        mask = np.asarray(Image.open(HERE / exclude).convert('L')) > 127
        hidden = np.stack([mask[y:y + py, x:x + px] for y, x in offsets])
        cells[hidden] = np.nan
        enough = (~hidden).sum(0) >= 3
        cell = np.where(enough[..., None], np.nanmedian(cells, axis=0),
                        np.median(np.stack([rgb[y:y + py, x:x + px] for y, x in offsets]), axis=0))
    else:
        cell = np.median(cells, axis=0)
    tiled = np.tile(cell, (math.ceil(height / py), math.ceil(width / px), 1))[:height, :width]
    return Image.fromarray(np.clip(tiled + 0.5, 0, 255).astype(np.uint8), 'RGB')


def open_native(world, name, cache={}):
    if world not in cache:
        cache[world] = NativeSources(world)
    if '%' in name:
        # Rolled view `name%ox,oy` (see rolled_entry): the native shifted so (ox, oy) is its top-left pixel.
        base, offsets = name.rsplit('%', 1)
        ox, oy = (int(value) for value in offsets.split(','))
        image = open_native(world, base)
        rolled = Image.fromarray(np.roll(np.asarray(image), (-oy, -ox), (0, 1)), image.mode)
        if image.mode == 'P':
            rolled.putpalette(image.getpalette())
        rolled.info = dict(image.info)
        return rolled
    if name.startswith('@'):
        return assembly_image(world, name[1:])
    return cache[world].image(name)


ASSEMBLY_OVERRIDES = HERE / 'assembly_overrides.json'  # [{"members": [ids in order], "axis": "u"|"v"}]
# Reviewer-declared false joints: pairs whose native edge profiles correlate by chance (MM9 `beamtbbuah` timber
# ceiling beside the `clif0ebr22` cliff on one face). Neither a neighbour link nor an assembly.
LINK_EXCLUSIONS = HERE / 'link_exclusions.json'  # [[id, id], ...]


def apply_assembly_overrides(textures):
    """Reviewer-declared assemblies: pictures split across textures that detection skips because the members have
    family relatives (MM7 two-part banners wizh-a/b, chb1p6/7, banwiz-a/b). Generated separately, each half got its
    own native-mean gain and the cloth stepped at the joint; one canvas gives both halves one calibration."""
    for chain in load_json(ASSEMBLY_OVERRIDES, []) or []:
        members = chain['members']
        if any(member not in textures for member in members):
            continue
        head = max(members, key=lambda member: (textures[member]['area'], member))
        for member in members:
            textures[member]['assembly'] = {'head': head, 'axis': chain['axis'], 'members': members}


@functools.lru_cache(maxsize=None)
def assembly_spec(world, head_name):
    entry = inventory()[f'{world}/{head_name}']
    return entry['assembly']


def assembly_image(world, head_name):
    """The members of an assembly placed edge to edge: the picture the original artist split."""
    spec = assembly_spec(world, head_name)
    images = [open_native(world, member.split('/')[1]).convert('RGBA') for member in spec['members']]
    if spec['axis'] == 'u':
        canvas = Image.new('RGBA', (sum(i.width for i in images), images[0].height))
        offset = 0
        for image in images:
            canvas.paste(image, (offset, 0))
            offset += image.width
    else:
        canvas = Image.new('RGBA', (images[0].width, sum(i.height for i in images)))
        offset = 0
        for image in images:
            canvas.paste(image, (0, offset))
            offset += image.height
    return canvas


def bmp32_alpha(image, path):
    """A 32-bit BI_RGB BMP with its fourth byte as alpha, as SDL loads it for the runtime (MM9 natives decoded from
    DTX: cut-out crowds, grilles, banners, blood). PIL reads these as RGB and drops the alpha, so the 2026-11-01
    inventory listed 266 MM9 cut-outs as opaque. SDL ignores the byte when it is zero everywhere (opaque art)."""
    if image.format != 'BMP' or image.mode != 'RGB':
        return image
    data = Path(path).read_bytes()
    offset, = struct.unpack_from('<I', data, 10)
    width, height = struct.unpack_from('<ii', data, 18)
    bits, compression = struct.unpack_from('<HI', data, 28)
    if bits != 32 or compression != 0:
        return image
    rows = np.frombuffer(data, np.uint8, count=width * abs(height) * 4, offset=offset).reshape(abs(height), width, 4)
    if height > 0:
        rows = rows[::-1]
    alpha = rows[..., 3]
    if not alpha.any():
        return image
    rgba = image.convert('RGBA')
    rgba.putalpha(Image.fromarray(np.ascontiguousarray(alpha), 'L'))
    return rgba


def native_rgba(image):
    """Decode to RGBA; native magenta colour key becomes transparent like the runtime loader."""
    rgba = np.array(image.convert('RGBA'))
    key = (rgba[..., 0] >= 248) & (rgba[..., 1] <= 8) & (rgba[..., 2] >= 248)
    rgba[key, 3] = 0
    return rgba


def polygon_area(points):
    points = np.asarray(points, float)
    if len(points) < 3:
        return 0.0
    total = np.zeros(3)
    for index in range(1, len(points) - 1):
        total += np.cross(points[index] - points[0], points[index + 1] - points[0])
    return float(np.linalg.norm(total) / 2)


def face_wrap(us, vs, du, dv, width, height):
    """Axes on which a face samples outside one texture period."""
    axes = set()
    u = np.asarray(us, float) + du
    v = np.asarray(vs, float) + dv
    if len(u) and (u.max() - u.min() > width + 1 or math.floor(u.min() / width) != math.floor((u.max() - 1) / width)):
        axes.add('u')
    if len(v) and (v.max() - v.min() > height + 1 or math.floor(v.min() / height) != math.floor((v.max() - 1) / height)):
        axes.add('v')
    return axes


def cmd_inventory(args):
    from map_export import parse_blv_file, parse_odm_file
    import csv
    terrain = set()
    for table in (ROOT / 'assets_dev/engine/data_tables').glob('terrain_tile_data*.txt'):
        with table.open(newline='') as stream:
            terrain.update(row['texture_name'].lower() for row in csv.DictReader(stream, delimiter='\t'))
    import yaml
    # Water/lava/oil faces are drawn by renderer-owned animated materials, not by their bitmap.
    material_names, material_prefixes = set(), []
    # (Liquids moved from engine/rendering/surface_materials.yml to engine/liquids/liquids.yml, same match format.)
    # The MM9 review root carries its own liquids (its water entries are not in assets_dev yet).
    liquids = []
    for path in (ROOT / 'assets_dev/engine/liquids/liquids.yml', REVIEW_ROOT / 'engine/liquids/liquids.yml'):
        if path.exists():
            liquids += yaml.safe_load(path.read_text())['liquids']
    for material in liquids:
        if 'face' in material.get('applies_to', []):
            material_names.update(name.lower() for name in material['match'].get('texture_names', []))
            material_prefixes += [prefix.lower() for prefix in material['match'].get('texture_prefixes', [])]
    old = load_json(INVENTORY, {}) or {}
    previous = {entry['id']: entry for entry in old.get('textures', [])}
    # `--world` rebuilds only those worlds; every other world's entries stay exactly as they are.
    rebuilt = args.world or WORLDS
    scope = {world: list(maps) for world, maps in (old.get('map_scope') or {}).items()}
    for name in args.map or []:
        for world in rebuilt:
            if world in SCOPED_WORLDS and name.lower() not in scope.setdefault(world, []):
                scope[world].append(name.lower())
    textures = {entry_id: entry for entry_id, entry in previous.items() if entry['world'] not in rebuilt}
    for world in rebuilt:
        sources = NativeSources(world)
        uses = {}
        abutments = {}
        maps_dir = world_content(world) / 'maps'
        for map_path in world_map_paths(world, scope.get(world)):
            indoor = map_path.suffix == '.blv'
            try:
                payload = (parse_blv_file if indoor else parse_odm_file)(map_path)['payload']
            except Exception as error:  # noqa: BLE001 - report and continue with other maps
                print(f'skip {world}/{map_path.name}: {error}', file=sys.stderr)
                continue
            if indoor:
                groups = [(payload['vertices'], payload['faces'])]
            else:
                groups = [(model['vertices'], model['faces']) for model in payload['bmodels']
                          if not (world == 'mm9' and model['name'].startswith(MM9_ODM_PROP_PREFIX))]
            for vertices, faces in groups:
                collect_abutments(vertices, faces, indoor, abutments)
                for face in faces:
                    name = (face.get('texture_name') or '').strip().lower()
                    indices = face.get('vertex_indices') or []
                    if not name or len(indices) < 3 or face.get('is_portal'):
                        continue
                    if indoor:
                        param = face.get('face_param') or {}
                        du, dv = param.get('texture_delta_u', 0), param.get('texture_delta_v', 0)
                    else:
                        du, dv = face.get('texture_delta_u', 0), face.get('texture_delta_v', 0)
                    use = uses.setdefault(name, {'maps': set(), 'faces': 0, 'area': 0.0, 'uv': [], 'event': False})
                    use['maps'].add(map_path.name)
                    use['faces'] += 1
                    # Invisible faces (MM9 collision brushes: ramps, fire-through clips) are never drawn.
                    use['visible'] = use.get('visible', 0) + (0 if indoor and face.get('attributes', 0) & 0x2000 else 1)
                    use['area'] += polygon_area([[vertices[i][k] for k in 'xyz'] for i in indices])
                    use['uv'].append((face.get('texture_us') or [], face.get('texture_vs') or [], du, dv))
        scoped_stems = {Path(name).stem for name in scope.get(world, [])}
        for lua in (world_content(world) / 'events/maps').glob('*.lua'):
            if world in SCOPED_WORLDS and lua.stem.lower() not in scoped_stems:
                continue
            for name in re.findall(r'SetTexture\(\s*\d+\s*,\s*"([^"]+)"', lua.read_text(errors='ignore')):
                use = uses.setdefault(name.lower(), {'maps': set(), 'faces': 0, 'area': 0.0, 'uv': [], 'event': False})
                use['event'] = True
                stem = lua.stem.lower()
                for suffix in ('.blv', '.odm'):
                    if (maps_dir / (stem + suffix)).exists():
                        use['maps'].add(stem + suffix)
        for name, use in sorted(uses.items()):
            entry_id = f'{world}/{name}'
            entry = {'id': entry_id, 'world': world, 'name': name,
                     'maps': sorted(use['maps']), 'faces': use['faces'], 'area': round(use['area']),
                     'event_switched': use['event']}
            image = sources.image(name)
            exclude = None
            if world == 'mm9':
                entry['source_texture'] = mm9_alias_sources().get(name)
            original = Path((entry.get('source_texture') or '').replace('\\', '/')).stem.lower()
            source_path = Path((entry.get('source_texture') or '').replace('\\', '/').lower())
            if world == 'mm9' and original in MM9_HELPER_TEXTURES:
                exclude = 'helper'
            elif world == 'mm9' and source_path.parts[:1] == ('skins',) and \
                    not any(name_.endswith('.blv') for name_ in use['maps']):
                # a prop's skin on an old outdoor import's geometry only (the isle's chests): the props' job; on a
                # rebuilt BLV's geometry (a dungeon's crate, rope, candle) it is a surface like any other
                exclude = 'prop_skin'
            elif world == 'mm9' and source_path.parent.name in MM9_SKY_FOLDERS:
                exclude = 'sky'
            elif world == 'mm9' and (source_path.suffix == '.spr' or source_path.parent.name in MM9_WATER_FOLDERS):
                exclude = 'renderer_material'
            elif 'sky' in name or name in SKY_TEXTURES:
                exclude = 'sky'
            elif name in material_names or name.startswith(tuple(material_prefixes)):
                exclude = 'renderer_material'
            elif image is None:
                exclude = 'terrain_only' if name in terrain else 'missing_native'
            elif use['faces'] and not use.get('visible') and not use['event']:
                exclude = 'invisible_only'
            if image is not None:
                rgba = native_rgba(image)
                width, height = image.size
                if not exclude and len(np.unique(rgba.reshape(-1, 4), axis=0)) <= 2:
                    # The importer's placeholder checker for a DTX it could not decode (MM9 StuccoTan): no art to
                    # redraw; fix the import, then rerun the inventory.
                    exclude = 'placeholder_native'
                axes = set()
                for us, vs, du, dv in use['uv']:
                    axes |= face_wrap(us, vs, du, dv, width, height)
                entry.update(native=sources.path(name), size=[width, height],
                             sha=hashlib.sha256(rgba.tobytes() + bytes(f'{width}x{height}', 'ascii')).hexdigest()[:16],
                             cutout=bool((rgba[..., 3] < 128).any()), wrap=''.join(sorted(axes)),
                             also_terrain=name in terrain)
                esrgan = esrgan_x4(world, name)
                entry['esrgan_x4'] = rel(esrgan) if esrgan else None
                entry['predicted_scale'] = round(predicted_scale(entry), 2)
            if exclude:
                entry['exclude'] = exclude
            entry['abutments'] = abutments.get(name, [])
            entry['material'] = (previous.get(entry_id) or {}).get('material', '')
            textures[entry_id] = entry
        for base_id, spec in periodic_bases().items():
            source = textures.get(spec['from'])
            if base_id.split('/')[0] != world or not source or source.get('exclude'):
                continue
            image = sources.image(base_id.split('/')[1])
            rgba = native_rgba(image)
            entry = {'id': base_id, 'world': world, 'name': base_id.split('/')[1], 'maps': source['maps'], 'faces': 0,
                     # The source's area: the base is generated before the piece composed on it.
                     'area': source['area'], 'event_switched': False, 'base_of': spec['from'],
                     'native': sources.path(base_id.split('/')[1]), 'size': list(image.size),
                     'sha': hashlib.sha256(rgba.tobytes() + bytes('%dx%d' % image.size, 'ascii')).hexdigest()[:16],
                     'cutout': False, 'wrap': 'uv', 'also_terrain': False, 'esrgan_x4': None, 'abutments': [],
                     'material': (previous.get(base_id) or {}).get('material', '')}
            entry['predicted_scale'] = round(predicted_scale(entry), 2)
            textures[base_id] = entry
    # Exact duplicates share one canonical generation (first world, then name order).
    by_sha = {}
    for entry in textures.values():
        if entry.get('sha') and not entry.get('exclude'):
            by_sha.setdefault(entry['sha'], []).append(entry['id'])
    accepted = {entry_id for entry_id, record in ledger_state().items() if record.get('status') == 'accepted'}
    for ids in by_sha.values():
        # An already accepted copy stays canonical when a scope grows (MM9 cities, 2026-11-01): a new duplicate with
        # an earlier name must not orphan its master.
        ids.sort(key=lambda value: (value not in accepted, WORLDS.index(value.split('/')[0]), value))
        for entry_id in ids:
            textures[entry_id]['canonical'] = ids[0]
            if len(ids) > 1:
                textures[entry_id]['duplicates'] = [other for other in ids if other != entry_id]
    find_relations(textures, rebuilt)
    find_assemblies(textures, rebuilt)
    apply_assembly_overrides(textures)
    entries = sorted(textures.values(), key=lambda entry: (WORLDS.index(entry['world']), entry['name']))
    write_json(INVENTORY, {'generated': now(), 'scale': SCALE,
                           'scope': 'MM6-MM8 BLV face and outdoor BModel face textures incl. event-switched names; '
                                    'MM9 face textures of the remade maps in map_scope; terrain-only, sky, water '
                                    'animation, MM9 helper names and textures only on invisible faces are excluded',
                           'map_scope': scope,
                           'textures': entries})
    summary = {}
    for entry in entries:
        if entry['world'] not in rebuilt:
            continue
        key = (entry['world'], entry.get('exclude') or ('canonical' if entry.get('canonical') == entry['id']
                                                        else 'duplicate'))
        summary[key] = summary.get(key, 0) + 1
    for key in sorted(summary):
        print(*key, summary[key])


@functools.lru_cache(maxsize=None)
def native_keys(world, name):
    """One integer per native pixel (RGBA, colour key applied) for exact comparisons."""
    rgba = native_rgba(open_native(world, name)).astype(np.uint64)
    return (rgba[..., 0] << 24) | (rgba[..., 1] << 16) | (rgba[..., 2] << 8) | rgba[..., 3]


def shifted(source, dx, dy, height, width):
    """result[y, x] = source[(y - dy) % h, (x - dx) % w] (textures repeat, so offsets wrap)."""
    ys = (np.arange(height) - dy) % source.shape[0]
    xs = (np.arange(width) - dx) % source.shape[1]
    return source[ys][:, xs]


def wrap_morphology(function, mask, size=3):
    padded = np.pad(mask, size, mode='wrap')
    return function(padded, np.ones((size, size), bool))[size:-size, size:-size]


def find_relations(textures, worlds=WORLDS):
    """Exact shared regions between natives of one world at any offset.

    The original artists cut wall families (plain wall, corner, post, niche, drain...) from shared painted canvases,
    so most variants are pixel-identical to a relative over large areas. Every 8x8 block of every texture is hashed
    at every position and looked up among the grid blocks of all others; offsets with enough matching blocks are
    then verified pixel by pixel."""
    weights = np.random.default_rng(1).integers(1, 2 ** 63, size=(BLOCK, BLOCK), dtype=np.uint64)
    for world in worlds:
        ids = [entry['id'] for entry in textures.values() if entry['world'] == world and not entry.get('exclude')
               and entry.get('canonical') == entry['id'] and min(entry['size']) >= BLOCK]
        keys = {entry_id: native_keys(world, textures[entry_id]['name']) for entry_id in ids}
        hashes = {}
        for entry_id in ids:
            height, width = keys[entry_id].shape
            window = np.zeros((height - BLOCK + 1, width - BLOCK + 1), np.uint64)
            for i in range(BLOCK):
                for j in range(BLOCK):
                    window += keys[entry_id][i:i + height - BLOCK + 1, j:j + width - BLOCK + 1] * weights[i, j]
            hashes[entry_id] = window
        grid_hash, grid_ref = [], []
        for index, entry_id in enumerate(ids):
            window = hashes[entry_id]
            for y in range(0, window.shape[0], BLOCK):
                for x in range(0, window.shape[1], BLOCK):
                    if len(np.unique(keys[entry_id][y:y + BLOCK, x:x + BLOCK])) >= 12:  # textured blocks only
                        grid_hash.append(window[y, x])
                        grid_ref.append((index, x, y))
        if not grid_hash:
            continue
        grid_hash = np.array(grid_hash, np.uint64)
        grid_ref = np.array(grid_ref)
        order = np.argsort(grid_hash)
        grid_hash, grid_ref = grid_hash[order], grid_ref[order]
        votes = {}
        for index_a, entry_id in enumerate(ids):
            flat = hashes[entry_id].ravel()
            row_width = hashes[entry_id].shape[1]
            positions = np.minimum(np.searchsorted(grid_hash, flat), len(grid_hash) - 1)
            for hit in np.nonzero(grid_hash[positions] == flat)[0]:
                ya, xa = divmod(int(hit), row_width)
                cursor = positions[hit]
                while cursor < len(grid_hash) and grid_hash[cursor] == flat[hit]:
                    index_b, xb, yb = (int(value) for value in grid_ref[cursor])
                    cursor += 1
                    if index_b == index_a:
                        continue
                    height_b, width_b = keys[ids[index_b]].shape
                    key = (index_a, index_b, (xa - xb) % width_b, (ya - yb) % height_b)
                    votes[key] = votes.get(key, 0) + 1
        relatives = {entry_id: [] for entry_id in ids}
        union = {entry_id: np.zeros(keys[entry_id].shape, bool) for entry_id in ids}
        for (index_a, index_b, dx, dy), count in votes.items():
            if count < 4:
                continue
            a, b = ids[index_a], ids[index_b]
            equal = keys[a] == shifted(keys[b], dx, dy, *keys[a].shape)
            shared = float(equal.mean())
            if shared >= RELATION_MIN_SHARED:
                relatives[a].append({'id': b, 'dx': dx, 'dy': dy, 'shared': round(shared, 3)})
                union[a] |= equal
        for entry_id in ids:
            textures[entry_id]['relatives'] = sorted(relatives[entry_id], key=lambda relation: -relation['shared'])
            textures[entry_id]['shared_px'] = int(union[entry_id].sum())


def face_uvs(face, indoor):
    if indoor:
        param = face.get('face_param') or {}
        du, dv = param.get('texture_delta_u', 0), param.get('texture_delta_v', 0)
    else:
        du, dv = face.get('texture_delta_u', 0), face.get('texture_delta_v', 0)
    return ([u + du for u in face.get('texture_us') or []], [v + dv for v in face.get('texture_vs') or []])


def collect_abutments(vertices, faces, indoor, abutments):
    """Coplanar faces with different textures that meet along an edge lying on both textures' borders.

    The edges only have to be collinear and overlap, not share both vertices: facades often meet in T-junctions (a
    shorter face beside a door, a pole face on the joint), and exact-vertex matching missed them (MM8 inn and hut
    doors, 2026-10-10). UVs are interpolated along each edge over the overlap. Records abutments[name] =
    [{other, axis, side, edge, other_edge, offset}] where side 'max' means `other` continues past this texture's
    high-u (or high-v) border. Raw UV values are kept; native sizes are applied later."""
    planes = {}
    for face in faces:
        name = (face.get('texture_name') or '').strip().lower()
        indices = face.get('vertex_indices') or []
        us, vs = face_uvs(face, indoor)
        if not name or len(indices) < 3 or len(us) < len(indices) or face.get('is_portal'):
            continue
        points = np.array([[vertices[i][k] for k in 'xyz'] for i in indices], float)
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        if np.linalg.norm(normal) < 1e-6:
            continue
        normal /= np.linalg.norm(normal)
        if normal[np.argmax(np.abs(normal))] < 0:
            normal = -normal
        key = (tuple(np.round(normal, 1)), round(float(np.dot(normal, points[0])) / 4))
        planes.setdefault(key, []).append((name, points, np.asarray(us, float), np.asarray(vs, float), normal))
    for group in planes.values():
        for ia, ib in touching_pairs(group):
            abut_pair(group[ia], group[ib], abutments)


ABUT_CELL = 256.0


def touching_pairs(group):
    """The (ia, ib) pairs, ia < ib in order, whose boxes come within a unit and a half of each other: only they can
    share an edge (abut_pair needs both ends of an edge within a unit of the other's edge line). Testing every pair
    took a minute on one MM9 city, whose street level is one plane of thousands of faces."""
    if len(group) < 64:
        return [(ia, ib) for ia in range(len(group)) for ib in range(ia + 1, len(group))]
    low = np.array([face[1].min(0) for face in group]) - 1.5
    high = np.array([face[1].max(0) + 1.5 for face in group])
    cells = {}
    for index in range(len(group)):
        first = np.floor(low[index] / ABUT_CELL).astype(int)
        last = np.floor(high[index] / ABUT_CELL).astype(int)
        for cx in range(first[0], last[0] + 1):
            for cy in range(first[1], last[1] + 1):
                for cz in range(first[2], last[2] + 1):
                    cells.setdefault((cx, cy, cz), []).append(index)
    pairs = set()
    for members in cells.values():
        for position, ia in enumerate(members):
            for ib in members[position + 1:]:
                if np.all(low[ia] <= high[ib]) and np.all(low[ib] <= high[ia]):
                    pairs.add((ia, ib) if ia < ib else (ib, ia))
    return sorted(pairs)


def abut_pair(face_a, face_b, abutments):
    name_a, pa, us_a, vs_a, normal_a = face_a
    name_b, pb, us_b, vs_b, normal_b = face_b
    if name_a == name_b or abs(float(np.dot(normal_a, normal_b))) < 0.98:
        return
    na, nb = len(pa), len(pb)
    for a1 in range(na):
        a2 = (a1 + 1) % na
        da = pa[a2] - pa[a1]
        length_a = np.linalg.norm(da)
        if length_a < 1:
            continue
        direction = da / length_a
        for b1 in range(nb):
            b2 = (b1 + 1) % nb
            # Both ends of B's edge on A's edge line (within a unit).
            ok = True
            params = []
            for point in (pb[b1], pb[b2]):
                offset = point - pa[a1]
                along = float(np.dot(offset, direction))
                if np.linalg.norm(offset - along * direction) > 1.0:
                    ok = False
                    break
                params.append(along)
            if not ok:
                continue
            low, high = max(0.0, min(params)), min(length_a, max(params))
            if high - low < 4:
                continue
            span_b = params[1] - params[0]
            if abs(span_b) < 1e-6:
                continue
            def at(values, i, j, t):
                return values[i] + (values[j] - values[i]) * t
            samples = []
            for along in (low, high):
                ta = along / length_a
                tb = (along - params[0]) / span_b
                samples.append((at(us_a, a1, a2, ta), at(vs_a, a1, a2, ta), at(us_b, b1, b2, tb), at(vs_b, b1, b2, tb)))
            (ua1, va1, ub1, vb1), (ua2, va2, ub2, vb2) = samples
            for axis, ca1, ca2, cb1, cb2, oa1, oa2, ob1, ob2, ca, cb in (
                    ('u', ua1, ua2, ub1, ub2, va1, va2, vb1, vb2, us_a, us_b),
                    ('v', va1, va2, vb1, vb2, ua1, ua2, ub1, ub2, vs_a, vs_b)):
                if abs(ca1 - ca2) > 0.5 or abs(cb1 - cb2) > 0.5:
                    continue
                side_a = 'max' if ca.mean() < ca1 else 'min'
                side_b = 'max' if cb.mean() < cb1 else 'min'
                if side_a == side_b:
                    continue
                # Perpendicular coordinates must continue along the edge (rows/columns line up).
                if abs((oa1 - ob1) - (oa2 - ob2)) > 0.5:
                    continue
                edge_a, edge_b, offset = round(ca1), round(cb1), round(oa1 - ob1)
                abutments.setdefault(name_a, []).append(
                    {'other': name_b, 'axis': axis, 'side': side_a, 'edge': float(edge_a),
                     'other_edge': float(edge_b), 'offset': float(offset)})


def continuous_links(textures, world, by_name):
    """Abutments (entry['abutments'], consumed) that join two textures at their borders with the native pixels
    continuing across: {(first, second, axis): count} for all, and the continuous subset."""
    links = {}
    for entry in by_name.values():
        if entry.get('exclude') or entry.get('canonical') != entry['id'] or 'size' not in entry:
            continue
        for abut in entry.pop('abutments', []):
            other = by_name.get(abut['other'])
            if not other or other.get('exclude') or 'size' not in other or other.get('canonical') != other['id']:
                continue
            axis = abut['axis']
            length = 0 if axis == 'u' else 1
            cross = 1 - length
            if entry['size'][cross] != other['size'][cross] or abut['offset'] % entry['size'][cross]:
                continue
            if abut['edge'] % entry['size'][length] or abut['other_edge'] % other['size'][length]:
                continue
            first, second = (entry, other) if abut['side'] == 'max' else (other, entry)
            key = (first['id'], second['id'], axis)
            links[key] = links.get(key, 0) + 1
    for entry in by_name.values():
        entry.pop('abutments', None)
    excluded = {frozenset(pair) for pair in load_json(LINK_EXCLUSIONS, []) or []}
    links = {key: count for key, count in links.items() if frozenset(key[:2]) not in excluded}
    # Native continuity across each joint, relative to the texture's own column/row steps.
    good = []
    for (first, second, axis), count in links.items():
        a = luma(native_rgba(open_native(world, textures[first]['name'])).astype(float))
        b = luma(native_rgba(open_native(world, textures[second]['name'])).astype(float))
        if axis == 'v':
            a, b = a.T, b.T
        joint = np.abs(a[:, -1] - b[:, 0]).mean()
        interior = np.abs(np.diff(np.concatenate([a, b], axis=1), axis=1)).mean()
        # The pixel profile along the joint must continue (planks, bands, rivets line up), not merely be two
        # dark borders: real splits correlate at 0.74-0.99, unrelated neighbours at -0.4..0.2.
        edge_a, edge_b = a[:, -1], b[:, 0]
        structured = edge_a.std() > 3 and edge_b.std() > 3
        if structured and joint <= 1.5 * interior and np.corrcoef(edge_a, edge_b)[0, 1] >= 0.6:
            good.append((first, second, axis))
    return links, good


def set_neighbors(textures, by_name, links, good, world=None):
    """Every abutment at texture borders becomes a neighbour link (used as reference context and joint check)."""
    for entry in by_name.values():
        entry.pop('neighbors', None)
    if world in TILED_MATERIAL_WORLDS:
        # MM9 faces are mapped in world space on a 128-unit grid, so different materials often meet exactly at
        # texture borders by coincidence (beams beside bricks, floor slabs beside ceiling panels). As context such a
        # neighbour replaced the texture's own wrap margin and skipped its seam splice; only joints whose native
        # pixels really continue are neighbours there.
        links = {key: count for key, count in links.items() if key in set(good)}
    # Every border-to-border abutment counts, not only the pixel-continuous ones that make assemblies: facade
    # pieces (wall | post | door) join only approximately in the natives (thatch line and stone courses at the same
    # heights, pixels not equal; MM8 t14a06|t14a03 correlate at 0.26), and generated apart they jumped at every joint.
    for (first, second, axis), count in sorted(links.items()):
        textures[first].setdefault('neighbors', []).append({'id': second, 'axis': axis, 'side': 'max',
                                                             'count': count})
        textures[second].setdefault('neighbors', []).append({'id': first, 'axis': axis, 'side': 'min',
                                                              'count': count})


def find_assemblies(textures, worlds=WORLDS):
    """Strips of different textures painted as one picture and split at their borders (chest front = left edge |
    body | right edge). Members abut in the maps exactly at texture borders, rows aligned, and the native pixels
    continue across the joint. Each assembly is generated as one canvas and cut back into its members."""
    for world in worlds:
        by_name = {entry['name']: entry for entry in textures.values() if entry['world'] == world}
        links, good = continuous_links(textures, world, by_name)
        set_neighbors(textures, by_name, links, good, world)
        # Keep simple chains: one neighbour per side per axis, no self repeats, no family relatives.
        for axis in 'uv':
            nexts, prevs = {}, {}
            for first, second, link_axis in good:
                if link_axis != axis:
                    continue
                nexts.setdefault(first, set()).add(second)
                prevs.setdefault(second, set()).add(first)
            def ok(entry_id):
                return (len(nexts.get(entry_id, ())) <= 1 and len(prevs.get(entry_id, ())) <= 1
                        and not textures[entry_id].get('relatives') and 'assembly' not in textures[entry_id])
            starts = [entry_id for entry_id in nexts if entry_id not in prevs and ok(entry_id)]
            for start in starts:
                chain = [start]
                while chain[-1] in nexts and ok(chain[-1]):
                    following = next(iter(nexts[chain[-1]]))
                    if following in chain or not ok(following):
                        break
                    chain.append(following)
                if not 2 <= len(chain) <= 5:
                    continue
                along = 0 if axis == 'u' else 1
                size = [textures[chain[0]]['size'][0], textures[chain[0]]['size'][1]]
                size[along] = sum(textures[member]['size'][along] for member in chain)
                if scale_for(*size) < SCALE:
                    continue
                head = max(chain, key=lambda entry_id: (textures[entry_id]['area'], entry_id))
                for member in chain:
                    textures[member]['assembly'] = {'head': head, 'axis': axis, 'members': chain}


def generation_entry(member, textures):
    """The entry actually generated for `member`: its assembly canvas when it heads one, else itself."""
    entry = textures[member]
    spec = entry.get('assembly')
    if not spec or spec['head'] != member:
        return entry
    image = assembly_image(entry['world'], entry['name'])
    members = [textures[m] for m in spec['members']]
    virtual = {**entry, 'id': f"{entry['world']}/@{entry['name']}", 'name': '@' + entry['name'],
               'size': [image.width, image.height], 'wrap': '', 'relatives': [], 'shared_px': 0,
               # Only the chain's outer neighbours: the head's own links name its members (inside the canvas), and
               # on the canvas those made it wait on its own members.
               'neighbors': assembly_end_neighbors(spec, textures),
               'cutout': any(m['cutout'] for m in members), 'esrgan_x4': None}
    virtual['predicted_scale'] = round(predicted_scale(virtual), 2)
    return virtual


def assembly_end_neighbors(spec, textures):
    """Neighbours beyond the first and last member along the assembly axis (context for the whole canvas)."""
    first, last = spec['members'][0], spec['members'][-1]
    ends = [neighbor for neighbor in textures[first].get('neighbors', [])
            if neighbor['axis'] == spec['axis'] and neighbor['side'] == 'min' and neighbor['id'] not in spec['members']]
    ends += [neighbor for neighbor in textures[last].get('neighbors', [])
             if neighbor['axis'] == spec['axis'] and neighbor['side'] == 'max' and neighbor['id'] not in spec['members']]
    return ends


def assembly_prefill(entry, textures, state, source_ids=None):
    """Family prefill of an assembly canvas: each member's own prefill placed at its cut."""
    spec = textures[entry['id'].replace('/@', '/')]['assembly']
    height, width = native_rgba(open_native(entry['world'], entry['name'])).shape[:2]
    channels = 4 if entry['cutout'] else 3
    fill = np.zeros((height, width), bool)
    canvas = np.zeros((height * SCALE, width * SCALE, channels), float)
    used = []
    for member, x0, y0, x1, y1 in assembly_cuts(spec, textures):
        if source_ids is None:
            sources = [relation['id'] for relation in family_relatives(textures[member])
                       if relation['id'] not in spec['members'] and state.get(relation['id'], {}).get('status') == 'accepted']
        else:
            sources = [source for source in source_ids if source not in spec['members']]
        member_fill, member_canvas, member_used = prefill(textures[member], textures, state, sources)
        if not member_fill.any():
            continue
        fill[y0 // SCALE:y1 // SCALE, x0 // SCALE:x1 // SCALE] = member_fill
        common = min(channels, member_canvas.shape[2])
        canvas[y0:y1, x0:x1, :common] = member_canvas[..., :common]
        used += [source for source in member_used if source not in used]
    return fill, canvas, used


def wait_priority(entry_id, textures):
    """Generation order key; assembly members share their canvas's key so waits never cross into a deadlock."""
    spec = textures[entry_id].get('assembly')
    if spec:
        return priority(generation_entry(spec['head'], textures))
    return priority(textures[entry_id])


def quiet_offset(native, axis):
    """Native line in the middle half along `axis` with the least luma gradient energy (no joints or edges)."""
    lum = luma(native[..., :3].astype(float))
    if axis == 'v':
        lum = lum.T
    energy = (np.abs(np.diff(lum, axis=1, append=lum[:, :1])) + np.abs(np.diff(lum, axis=0, append=lum[:1]))).sum(0)
    size = len(energy)
    smooth = np.convolve(np.r_[energy, energy[:4]], np.ones(5) / 5, 'valid')[:size]
    low, high = size // 4, 3 * size // 4
    return low + int(np.argmin(smooth[low:high]))


def rolled_entry(entry, roll):
    """The texture generated rolled by (ox, oy) native pixels: its own edges sit inside the picture.

    The model paints a groove wherever the reference shows the tile boundary (a mirror fold, a joint sitting on the
    edge, or the opposite edge wrapped against it). Rolled, the boundary falls on a quiet interior line and the real
    edges are painted as ordinary content; the rolled axes wrap and get `quilt_wrap`, and `check` rolls the master
    back (whole master pixels, no resampling)."""
    ox, oy = roll
    axes = ('u' if ox else '') + ('v' if oy else '')
    wrap = ''.join(axis for axis in 'uv' if axis in entry['wrap'] or axis in axes)
    return {**entry, 'name': f"{entry['name']}%{ox},{oy}", 'wrap': wrap}


def version_entry(member, textures, request, version):
    """Generation entry of one requested version (rolled when the version asks for it)."""
    entry = generation_entry(member, textures)
    pad = (request.get('pad') or {}).get(str(version))
    if pad:
        entry = {**entry, '_pad': pad}
    sides = sorted((request.get('context') or {}).get(str(version)) or {})
    if sides:
        entry = {**entry, '_context_sides': sides}
    roll = (request.get('roll') or {}).get(str(version))
    return rolled_entry(entry, roll) if roll else entry


CONTEXT_PAD = 32  # native pixels of a finished neighbour shown on each context side (16 was too little to follow)


def context_pad(entry, context):
    """Wider margins on axes with neighbour context, when one return still holds the canvas at 4x; else None."""
    layout = layout_for(entry)
    if layout['copies'] > 1 or layout.get('fixed') or not context:
        return None
    pad = list(layout['pad'])
    width, height = entry['size']
    if {'left', 'right'} & set(context):
        pad[0] = max(pad[0], min(CONTEXT_PAD, width // 2))
    if {'top', 'bottom'} & set(context):
        pad[1] = max(pad[1], min(CONTEXT_PAD, height // 2))
    total = (width + 2 * pad[0], height + 2 * pad[1])
    if pad == layout['pad'] or not 0.5 <= total[0] / total[1] <= 2.0 or scale_for(*total) < SCALE:
        return None
    return pad


def roll_context(context, roll):
    """Neighbour margins kept for a rolled version: sides along a non-rolled axis, their strips rolled to match."""
    ox, oy = roll
    kept = {}
    for side, item in context.items():
        if side in ('left', 'right') and not ox:
            kept[side] = {**item, 'master': np.roll(item['master'], -oy * SCALE, 0)}
        elif side in ('top', 'bottom') and not oy:
            kept[side] = {**item, 'master': np.roll(item['master'], -ox * SCALE, 1)}
    return kept


def neighbor_axes(entry):
    """Axes along which the texture abuts other textures in the map (never rolled: the real neighbour is context)."""
    return {neighbor['axis'] for neighbor in entry.get('neighbors', [])}


def roll_fill(fill, filled, roll):
    """Family prefill of the unrolled texture moved into a rolled version's frame."""
    if fill is None:
        return fill, filled
    ox, oy = roll
    return np.roll(fill, (-oy, -ox), (0, 1)), np.roll(filled, (-oy * SCALE, -ox * SCALE), (0, 1))


def assembly_cuts(spec, textures):
    """(member id, x0, y0, x1, y1) of each member inside the assembly canvas, in 4x pixels."""
    cuts, offset = [], 0
    for member in spec['members']:
        width, height = textures[member]['size']
        if spec['axis'] == 'u':
            cuts.append((member, offset * SCALE, 0, (offset + width) * SCALE, height * SCALE))
            offset += width
        else:
            cuts.append((member, 0, offset * SCALE, width * SCALE, (offset + height) * SCALE))
            offset += height
    return cuts


FAMILY_SOURCES = HERE / 'family_sources.json'  # {member: [{id, dx, dy}]}: reviewer-chosen extra copy sources


@functools.lru_cache(maxsize=None)
def family_sources():
    return load_json(FAMILY_SOURCES, {}) or {}


COMPOSE = HERE / 'compose.json'  # {piece: {base, dx, dy, features, refine, tol, keep}}: wall from one base


@functools.lru_cache(maxsize=None)
def compose_specs():
    return load_json(COMPOSE, {}) or {}


COMPOSE_DIFF = 22.0  # blurred native difference from the base above which a box pixel is feature (refine: diff)


def compose_wall(entry):
    """Native mask of the wall a composed piece copies from its base: everything outside its feature boxes.

    With `refine: diff` (uniform walls such as plaster) a box keeps only the pixels that differ from the base at the
    same place, so a diagonal brace gets a diagonal mask instead of a rectangle whose generated shading steps against
    the copied wall (MM6 pxstrle)."""
    spec = compose_specs()[entry['id']]
    width, height = entry['size']
    feature = np.zeros((height, width), bool)
    for x0, y0, x1, y1 in spec['features']:
        feature[y0:y1, x0:x1] = True
    if spec.get('mask'):
        # A reviewer-made native-resolution mask (white = feature) for shapes boxes cannot follow: the diagonal beams
        # over the MM9 ceiling lattice, the crack in a brick wall. It restricts the boxes like `refine: diff`.
        feature &= np.asarray(Image.open(HERE / spec['mask']).convert('L')) > 127
    if spec.get('refine') == 'diff':
        base_world, base_name = spec['base'].split('/')
        native = native_rgba(open_native(entry['world'], entry['name']))[..., :3].astype(float)
        source = shifted(native_rgba(open_native(base_world, base_name))[..., :3].astype(float),
                         spec.get('dx', 0), spec.get('dy', 0), height, width)
        diff = np.abs(ndimage.gaussian_filter(native, (1.5, 1.5, 0), mode='nearest')
                      - ndimage.gaussian_filter(source, (1.5, 1.5, 0), mode='wrap')).mean(-1)
        differs = ndimage.binary_dilation(ndimage.binary_opening(diff > spec.get('tol', COMPOSE_DIFF), np.ones((2, 2))),
                                          np.ones((3, 3)))
        feature = ndimage.binary_fill_holes(differs & feature)
    for x0, y0, x1, y1 in spec.get('keep', []):  # always generated whole (a post crossing the beams)
        feature[y0:y1, x0:x1] = True
    return ~feature


def family_relatives(entry):
    """Relatives whose exact shared pixels this texture copies (none for independently generated textures).

    Reviewer-chosen sources (`family_sources.json`) come first, so their pixels win where they overlap: used for a
    small repeating motif (a frieze tile) that the generator cannot read inside the large pieces cut from it; the
    motif is generated once on its own and every piece copies it (it is below the automatic 15% share threshold)."""
    if entry['id'].startswith(NO_FAMILY_PREFIXES):
        return []
    forced = [{**source, 'forced': True} for source in family_sources().get(entry['id'], [])]
    return forced + entry.get('relatives', [])


def priority(entry):
    """Generation order inside a family or between neighbours: the piece sharing most pixels (the plain wall) goes
    first, then the one covering most wall area."""
    return (-entry.get('shared_px', 0), -entry.get('area', 0), entry['id'])


SEAM_TRIM = 2  # native rows/columns at a repeating source's seam that a non-repeating piece does not copy


def prefill(entry, textures, state, source_ids=None):
    """Native pixels identical to accepted relatives, filled from those relatives' 4x masters.

    Returns the native-resolution fill mask, the 4x canvas holding the copied master pixels and the source ids."""
    if entry['name'].startswith('@'):
        return assembly_prefill(entry, textures, state, source_ids)
    keys = native_keys(entry['world'], entry['name'])
    height, width = keys.shape
    channels = 4 if entry['cutout'] else 3
    fill = np.zeros((height, width), bool)
    canvas = np.zeros((height * SCALE, width * SCALE, channels), float)
    used = []
    # A composed piece takes its whole wall from one base master (the natives repaint the wall in every piece, so
    # exact matching finds little and independently painted walls step at every joint); only its door, window or
    # trim boxes are generated, on that wall. Every composed piece then meets the base and the others continuously.
    spec = compose_specs().get(entry['id'])
    record = state.get(spec['base'], {}) if spec else {}
    if (spec and record.get('status') == 'accepted' and record.get('master')
            and (source_ids is None or spec['base'] in source_ids)):
        wall = compose_wall(entry) & (native_rgba(open_native(entry['world'], entry['name']))[..., 3] > 127)
        master = np.asarray(Image.open(ROOT / record['master']).convert('RGBA' if channels == 4 else 'RGB'))
        moved = shifted(master.astype(float), spec.get('dx', 0) * SCALE, spec.get('dy', 0) * SCALE,
                        height * SCALE, width * SCALE)
        wall4 = np.kron(wall, np.ones((SCALE, SCALE), bool))
        canvas[wall4] = moved[wall4]
        fill |= wall
        used.append(spec['base'])
    for relation in family_relatives(entry):
        record = state.get(relation['id'], {})
        if source_ids is not None:
            if relation['id'] not in source_ids:
                continue
        elif record.get('status') != 'accepted':
            continue
        if not record.get('master'):
            continue
        other = textures[relation['id']]
        equal = keys == shifted(native_keys(other['world'], other['name']), relation['dx'], relation['dy'],
                                height, width)
        # A source that repeats on an axis may straddle a joint across its own seam (half on each edge), harmless
        # there; a piece that does not repeat on that axis would get that half joint as an edge line. Those
        # rows/columns are generated instead (MM7 hep1b -> hep1bs/bs1/bw, hwm1bs1 -> hwm1bsw).
        seam = np.zeros(other['size'][::-1], bool)
        if 'v' in other['wrap'] and 'v' not in entry['wrap']:
            seam[:SEAM_TRIM] = seam[-SEAM_TRIM:] = True
        if 'u' in other['wrap'] and 'u' not in entry['wrap']:
            seam[:, :SEAM_TRIM] = seam[:, -SEAM_TRIM:] = True
        if seam.any():
            equal &= ~shifted(seam, relation['dx'], relation['dy'], height, width)
        equal = wrap_morphology(ndimage.binary_opening, equal)  # drop coincidental single-pixel matches
        labels, count = ndimage.label(equal)
        if count:
            # Small islands are coincidental colour matches (a dark pixel cluster inside a light tile), not shared art.
            sizes = ndimage.sum(equal, labels, range(1, count + 1))
            equal = np.isin(labels, 1 + np.nonzero(sizes >= BLOCK * BLOCK)[0])
        new = equal & ~fill
        if new.sum() < BLOCK * BLOCK:
            continue
        master = np.asarray(Image.open(ROOT / record['master']).convert('RGBA' if channels == 4 else 'RGB'))
        moved = shifted(master.astype(float), relation['dx'] * SCALE, relation['dy'] * SCALE,
                        height * SCALE, width * SCALE)
        new4 = np.kron(new, np.ones((SCALE, SCALE), bool))
        canvas[new4] = moved[new4]
        fill |= new
        if relation['id'] not in used:
            used.append(relation['id'])
    return fill, canvas, used


def shared_core(fill):
    """4x mask of the copied region: the native fill eroded by one pixel, with its stair-stepped native-pixel
    outline smoothed into a contour (blocky outlines showed as faint square patches where art differs). The erosion
    does not cross the tile edge: a copied edge column stays copied (a wrapped erosion handed the outermost column to
    the generator, which painted its boundary groove there: MM7 t4s1er)."""
    padded = np.pad(fill, 1, mode='edge')
    eroded = ndimage.binary_erosion(padded, np.ones((3, 3), bool))[1:-1, 1:-1].astype(float)
    height, width = eroded.shape
    smooth = np.asarray(Image.fromarray((eroded * 255).astype(np.uint8)).resize((width * SCALE, height * SCALE),
                                                                                Image.BILINEAR)).astype(float)
    return smooth >= 128


def paste_shared(master, filled, core4, fill=None, feather=2.0):
    """Copy relative pixels inside core4 exactly; fade them out over a few pixels into the generated art."""
    channels = filled.shape[2]
    weight = np.clip(ndimage.gaussian_filter(core4.astype(float), feather, mode='wrap') * 2, 0, 1)
    weight[core4] = 1.0
    if fill is not None:
        weight *= np.kron(fill, np.ones((SCALE, SCALE)))  # only where relative pixels exist
    weight = weight[..., None]
    master[..., :channels] = weight * filled + (1 - weight) * master[..., :channels]


def coverage(entry, fill):
    native = native_rgba(open_native(entry['world'], entry['name']))
    opaque = native[..., 3] > 127
    return float((fill & opaque).sum() / max(1, opaque.sum()))


def derivable(entry, fill):
    """Covered so completely by accepted relatives that the master is cut from them instead of generated.

    The few uncovered pixels are filled from the nearest copied ones, which is invisible for scattered dither
    differences but smears real content: a 2-row plank shadow missing from MM6 whend became 8 repeated master rows,
    then whft and whcntr copied the smear. Any uncovered patch larger than a few native pixels is generated."""
    if coverage(entry, fill) < FULL_COVERAGE:
        return False
    opaque = native_rgba(open_native(entry['world'], entry['name']))[..., 3] > 127
    labels, count = ndimage.label(~fill & opaque)
    return not count or ndimage.sum(np.ones_like(labels), labels, range(1, count + 1)).max() <= MAX_DERIVED_GAP


def waiting_for(entry, textures, state):
    """An in-progress texture this one must follow: a higher-priority relative that would still add shared pixels,
    or a higher-priority neighbour whose finished edge becomes this texture's context. Assembly canvases wait for
    their members' relatives and the chain's outer neighbours; members are ordered by their canvas."""
    own = wait_priority(entry['id'].replace('/@', '/'), textures)
    members = [entry['id']]
    if entry['name'].startswith('@'):
        members = textures[entry['id'].replace('/@', '/')]['assembly']['members']
    for member in members:
        piece = textures[member]
        base = compose_specs().get(member, {}).get('base')
        if base and state.get(base, {}).get('status') in ('claimed', 'candidate'):
            return base
        fill, _, _ = prefill(piece, textures, state)
        keys = native_keys(piece['world'], piece['name'])
        for relation in family_relatives(piece):
            other = textures[relation['id']]
            if other['id'] in members or state.get(other['id'], {}).get('status') not in ('claimed', 'candidate'):
                continue
            if wait_priority(other['id'], textures) >= own and not relation.get('forced'):
                continue
            equal = keys == shifted(native_keys(other['world'], other['name']), relation['dx'], relation['dy'],
                                    *keys.shape)
            if (equal & ~fill).mean() >= 0.05:
                return other['id']
    for neighbor in entry.get('neighbors', []):
        other = textures.get(neighbor['id'])
        if (other and other['id'] not in members and state.get(other['id'], {}).get('status') in ('claimed', 'candidate')
                and wait_priority(other['id'], textures) < own):
            return other['id']
    return None


SIDES = {('u', 'max'): 'right', ('u', 'min'): 'left', ('v', 'max'): 'bottom', ('v', 'min'): 'top'}


def neighbor_context(entry, textures, state):
    """Per side, the accepted neighbour (most frequent abutment) whose master continues across that edge."""
    context = {}
    for neighbor in sorted(entry.get('neighbors', []), key=lambda n: -n.get('count', 1)):
        side = SIDES[(neighbor['axis'], neighbor['side'])]
        record = state.get(neighbor['id'], {})
        if side in context or record.get('status') != 'accepted' or not record.get('master'):
            continue
        other = textures[neighbor['id']]
        if other['size'][1 if neighbor['axis'] == 'u' else 0] != entry['size'][1 if neighbor['axis'] == 'u' else 0]:
            continue
        master = np.asarray(Image.open(ROOT / record['master']).convert('RGB')).astype(float)
        context[side] = {'id': neighbor['id'], 'master': master}
    return context


JOINT_BAND = 2  # native pixels on each side of a joint used to match a piece's colour to its neighbour


JOINT_TONE_BAND = 2      # native pixels at the edge whose low-pass tone is compared with the neighbour's edge
JOINT_TONE_FEATHER = 20  # native pixels over which the correction fades to nothing


def joint_tone_field(pixels, entry, context, textures):
    """Smooth per-channel gain field that makes a master's edge tone continue its accepted neighbours' edges the way
    the natives continue (the native's own step across the joint is kept), fading out over JOINT_TONE_FEATHER native
    pixels. Only low frequencies change: detail, joints and edges stay exactly where they were.

    For a narrow wall strip beside a door or pilaster the generator shades the strip as one flat block, so a brick or
    plaster patch that crosses the joint changes tone half way (user review 2026-10-10: MM8 Fellburn door `t19b03b`,
    Clan Leader's Hall plaster `t02a06`/`t02a08a`). Regeneration keeps reproducing it; this is the deterministic fix."""
    native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)[..., :3]
    height, width = pixels.shape[:2]
    band, feather = JOINT_TONE_BAND * SCALE, JOINT_TONE_FEATHER * SCALE
    linear = srgb_to_linear(pixels[..., :3])
    gain = np.ones_like(linear)
    for side, item in context.items():
        other = textures[item['id']]
        theirs_native = native_rgba(open_native(other['world'], other['name'])).astype(float)[..., :3]
        theirs = srgb_to_linear(item['master'][..., :3])
        vertical_joint = side in ('left', 'right')
        if vertical_joint:
            if theirs.shape[0] != height:
                continue
            mine_strip = linear[:, :band] if side == 'left' else linear[:, -band:]
            their_strip = theirs[:, -band:] if side == 'left' else theirs[:, :band]
            mine_nat = native[:, :JOINT_TONE_BAND] if side == 'left' else native[:, -JOINT_TONE_BAND:]
            their_nat = (theirs_native[:, -JOINT_TONE_BAND:] if side == 'left' else theirs_native[:, :JOINT_TONE_BAND])
            axis = 1
        else:
            if theirs.shape[1] != width:
                continue
            mine_strip = linear[:band] if side == 'top' else linear[-band:]
            their_strip = theirs[-band:] if side == 'top' else theirs[:band]
            mine_nat = native[:JOINT_TONE_BAND] if side == 'top' else native[-JOINT_TONE_BAND:]
            their_nat = theirs_native[-JOINT_TONE_BAND:] if side == 'top' else theirs_native[:JOINT_TONE_BAND]
            axis = 0
        sigma = 6 * SCALE
        mine_profile = ndimage.gaussian_filter1d(mine_strip.mean(axis=axis), sigma, axis=0, mode='nearest')
        their_profile = ndimage.gaussian_filter1d(their_strip.mean(axis=axis), sigma, axis=0, mode='nearest')
        ratio = (ndimage.gaussian_filter1d(srgb_to_linear(mine_nat).mean(axis=axis), 6, axis=0, mode='nearest') /
                 np.maximum(ndimage.gaussian_filter1d(srgb_to_linear(their_nat).mean(axis=axis), 6, axis=0,
                                                      mode='nearest'), 1e-4))
        ratio = np.repeat(np.clip(ratio, 0.5, 2.0), SCALE, axis=0)[:len(mine_profile)]
        profile_gain = np.clip(their_profile * ratio / np.maximum(mine_profile, 1e-4), 0.6, 1.6)
        size = width if vertical_joint else height
        span = min(feather, size // 2)
        distance = np.arange(size) if side in ('left', 'top') else np.arange(size)[::-1]
        ramp = np.where(distance < span, 0.5 * (1 + np.cos(np.pi * distance / span)), 0.0)
        if vertical_joint:
            field = 1 + (profile_gain[:, None, :] - 1) * ramp[None, :, None]
        else:
            field = 1 + (profile_gain[None, :, :] - 1) * ramp[:, None, None]
        gain *= field
    out = pixels.copy()
    out[..., :3] = linear_to_srgb(linear * gain)
    return out


def apply_joint_tone(candidate, entry, textures, state, fill=None, filled=None):
    """Reviewer option `retry --joint-tone` / `tex.py joint-tone`: the joint_tone_field correction against the accepted
    neighbours (neighbour_context), with pixels copied from relatives pasted back so families stay exact."""
    context = neighbor_context(entry, textures, state)
    if not context:
        return candidate
    pixels = np.asarray(candidate).astype(float)
    pixels = joint_tone_field(pixels, entry, context, textures)
    if fill is not None and fill.any():
        paste_shared(pixels, filled, shared_core(fill), fill)
    return Image.fromarray(np.clip(pixels + 0.5, 0, 255).astype(np.uint8), candidate.mode)


def match_neighbor_gain(candidate, entry, textures, state, metrics, fill=None, filled=None):
    """Reviewer option for pieces whose native-mean gain leaves a tone step at a continuous joint (MM7 banwiz-a):
    one more per-channel linear gain, so the strip along each joint matches the accepted neighbour's strip with the
    difference the natives have there kept. Pixels copied from relatives are pasted back unchanged."""
    context = neighbor_context(entry, textures, state)
    if not context:
        return candidate
    native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
    pixels = np.asarray(candidate).astype(float)
    band = JOINT_BAND * SCALE
    strips = {'right': (np.s_[:, -band:], np.s_[:, :band], np.s_[:, -JOINT_BAND:], np.s_[:, :JOINT_BAND]),
              'left': (np.s_[:, :band], np.s_[:, -band:], np.s_[:, :JOINT_BAND], np.s_[:, -JOINT_BAND:]),
              'bottom': (np.s_[-band:], np.s_[:band], np.s_[-JOINT_BAND:], np.s_[:JOINT_BAND]),
              'top': (np.s_[:band], np.s_[-band:], np.s_[:JOINT_BAND], np.s_[-JOINT_BAND:])}
    parts = [[], [], [], []]
    for side, item in context.items():
        other = textures[item['id']]
        their_native = native_rgba(open_native(other['world'], other['name'])).astype(float)
        mine, theirs, mine_native, theirs_native = strips[side]
        for index, values in enumerate((pixels[mine], item['master'][theirs], native[mine_native],
                                        their_native[theirs_native])):
            parts[index].append(srgb_to_linear(values[..., :3]).reshape(-1, 3))
    mine, theirs, mine_native, theirs_native = (np.concatenate(part).mean(axis=0) for part in parts)
    gains = np.clip(theirs * (mine_native / np.maximum(theirs_native, 1e-6)) / np.maximum(mine, 1e-6), 0.5, 2.0)
    for channel in range(3):
        pixels[..., channel] = linear_to_srgb(srgb_to_linear(pixels[..., channel]) * gains[channel])
    if fill is not None and fill.any():
        paste_shared(pixels, filled, shared_core(fill), fill)
    metrics['neighbor_gain'] = [round(float(gain), 3) for gain in gains]
    return Image.fromarray(np.clip(pixels + 0.5, 0, 255).astype(np.uint8), candidate.mode)


def joint_ratios(master, native, context, textures):
    """Per side with neighbour context: step across the joint relative to the interior step (master vs native)."""
    out = {}
    height, width = native.shape[:2]
    def reduce(image, size):
        return luma(np.asarray(Image.fromarray(np.clip(image[..., :3] + 0.5, 0, 255).astype(np.uint8))
                               .resize(size, Image.BOX)).astype(float))
    mine = reduce(master, (width, height))
    original = luma(native[..., :3])
    for side, item in context.items():
        other = textures[item['id']]
        theirs = reduce(item['master'], tuple(other['size']))
        their_native = luma(native_rgba(open_native(other['world'], other['name'])).astype(float))
        pairs = {'right': (mine[:, -1], theirs[:, 0], original[:, -1], their_native[:, 0], 1),
                 'left': (mine[:, 0], theirs[:, -1], original[:, 0], their_native[:, -1], 1),
                 'bottom': (mine[-1], theirs[0], original[-1], their_native[0], 0),
                 'top': (mine[0], theirs[-1], original[0], their_native[-1], 0)}
        a, b, na, nb, axis = pairs[side]
        step = np.abs(np.diff(mine, axis=axis)).mean() + 1e-6
        native_step = np.abs(np.diff(original, axis=axis)).mean() + 1e-6
        out[side] = (float(np.abs(a - b).mean() / step), float(np.abs(na - nb).mean() / native_step))
    return out


def inventory():
    data = load_json(INVENTORY)
    if not data:
        sys.exit('inventory.json missing: run `tex.py inventory` first')
    return {entry['id']: entry for entry in data['textures']}


def effective_status(entry, state):
    """Duplicates follow their canonical texture."""
    if entry.get('exclude'):
        return 'excluded'
    canonical = entry.get('canonical', entry['id'])
    return state.get(canonical, {}).get('status', 'pending')


def cmd_status(args):
    textures = inventory()
    state = ledger_state()
    counts = {}
    for entry in textures.values():
        status = effective_status(entry, state)
        counts.setdefault(entry['world'], {}).setdefault(status, 0)
        counts[entry['world']][status] += 1
    for world in WORLDS:
        row = counts.get(world, {})
        print(world, ' '.join(f'{key}={row[key]}' for key in sorted(row)), f'total={sum(row.values())}')
    jobs = sorted(path.name for path in JOBS.glob('*') if (path / 'job.json').exists())
    open_jobs = [job for job in jobs
                 if any(state.get(t, {}).get('status') in ('claimed', 'candidate') and state[t].get('job') == job
                        for t in load_json(JOBS / job / 'job.json')['textures'])]
    print('open jobs:', ' '.join(open_jobs) or '-')
    sectioned = [entry['id'] for entry in textures.values() if entry.get('predicted_scale', SCALE) < SCALE
                 and not entry.get('exclude') and effective_status(entry, state) != 'accepted']
    print(f'generated in sections: {" ".join(sectioned) or "-"}')


# ------------------------------------------------------------------------------------------------ next

def cmd_next(args):
    # Hold one lock from reading the ledger until the claims are written, so parallel sessions never share work.
    with open(HERE / '.claim.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        claim_next(args)


def claim_next(args):
    textures = inventory()
    state = ledger_state()
    worlds = args.world or WORLDS
    pending = {entry_id: entry for entry_id, entry in textures.items()
               if entry['world'] in worlds and not entry.get('exclude')
               and entry.get('canonical') == entry_id and effective_status(entry, state) == 'pending'}
    done = {entry_id for entry_id, entry in textures.items() if effective_status(entry, state) == 'accepted'}
    # Group by map; a texture belongs to its first map in the chosen order.
    maps = {}
    for entry in textures.values():
        if entry['world'] not in worlds or entry.get('exclude'):
            continue
        for map_name in entry['maps']:
            maps.setdefault((entry['world'], map_name), set()).add(entry['id'])
    def map_key(key):
        names = maps[key]
        fraction = len(names & done) / max(1, len(names))
        area = sum(textures[name]['area'] for name in names if textures[name].get('canonical', name) in pending)
        indoor = key[1].endswith('.blv')
        return (-fraction, WORLDS.index(key[0]), not indoor if args.indoor_first else 0, -area)
    if args.map:
        order = [key for key in maps if key[1] in args.map]
    else:
        order = sorted(maps, key=map_key)
    # Walk maps in order, taking all their pending textures; pack consecutive maps into jobs of <= JOB_SIZE.
    chosen, jobs, current = set(), [], ([], [])
    for key in order:
        if len(chosen) >= args.count:
            break
        members = sorted({textures[name].get('canonical', name) for name in maps[key]} & set(pending) - chosen,
                         key=lambda name: -textures[name]['area'])
        if args.names:
            # A named set (door pilot): only these, plus the relatives and assembly pieces they bring below.
            members = [name for name in members if name in args.names or textures[name]['name'] in args.names]
        # Keep families together: a piece brings its pending higher-priority relatives (the plain wall it was cut
        # from) into the same claim, so the family base is generated first instead of the piece becoming the base.
        with_family = []
        for member in list(members):
            for piece in (textures[member].get('assembly') or {}).get('members', []):
                if piece in pending and piece not in chosen and piece not in members:
                    members.append(piece)  # assembly pieces are generated together
        for member in members:
            for relation in family_relatives(textures[member]):
                relative = relation['id']
                if (relative in pending and relative not in chosen and relative not in with_family
                        and priority(textures[relative]) < priority(textures[member])):
                    with_family.append(relative)
            if member not in with_family:
                with_family.append(member)
        members = sorted(with_family, key=lambda name: priority(textures[name]))
        for member in members[:args.count - len(chosen)]:
            if len(current[1]) >= JOB_SIZE:
                jobs.append(current)
                current = ([], [])
            if key not in current[0]:
                current[0].append(key)
            current[1].append(member)
            chosen.add(member)
    if current[1]:
        jobs.append(current)
    if not jobs:
        print('nothing pending in scope')
        return
    stamp = datetime.now().strftime('%Y%m%d-%H%M')
    created = []
    for index, (keys, members) in enumerate(jobs):
        world, first_map = keys[0]
        job_id = f'{stamp}-{world}-{Path(first_map).stem}-{index:02d}'
        map_names = [map_name for _, map_name in keys]
        if args.dry_run:
            print(job_id, len(members), ','.join(map_names), ' '.join(textures[m]['name'] for m in members))
            continue
        create_job(job_id, world, map_names, members, textures)
        created.append(job_id)
    if not args.dry_run:
        ledger_append([{'event': 'claim', 'id': member, 'job': job_id}
                       for job_id, (_, members) in zip(created, jobs) for member in members])
        print('created', len(created), 'jobs,', len(chosen), 'textures:')
        for job_id in created:
            print(' ', job_id)


PROMPT_TEMPLATE = """Use case: precise-object-edit.
Asset: {kind} for {era}, native {width}x{height} pixels{wrap_text}.
Reference 1 is a soft enlargement of the original low-resolution texture{pad_text}. It is a guide for layout,
colours and materials only and contains no real fine detail. Reproduce EXACTLY its layout:
every block, plank, joint, ornament, figure and border at the same positions and proportions, the same colours,
palette and overall brightness. Do not add, remove, move or resize anything.
Redraw it as new clean high-definition artwork at 4x the original resolution: {material}
continuous crisp edges and fine natural surface detail invented anew, everything in sharp focus, even diffuse
lighting.
Keep the full canvas{pad_keep}, flat orthographic view, full bleed{alpha_text}.
No perspective, vignette, baked highlights or cast shadows, frame, text or watermark.
Avoid enlarged pixel blocks, dithering, stippled noise, crunchy grain and sharpening halos.
No dark outline, frame line, vignette or shadow along the outer edges of the canvas: every edge row and column keeps
the brightness and material of the reference's edge, because the texture is tiled and its edges touch other faces.
{artefacts}"""


MAX_ASPECT = 2.0
GAP_GREY = (128, 128, 128, 255)


LAYOUT_OVERRIDES = HERE / 'layout_overrides.json'  # {generation id: {"pad": [u, v]}}


@functools.lru_cache(maxsize=None)
def layout_overrides():
    return load_json(LAYOUT_OVERRIDES, {}) or {}


def layout_for(entry):
    """Reference layout: wrap margins, and for narrow strips either more wrap context or stacked copies.

    Imagegen returns roughly 1:2..2:1 images, so a 256x16 trim cannot be sent as is. If the strip repeats across its
    short side, extra wrap context makes it squarer; otherwise identical copies are stacked with grey gaps and the
    best redraw is kept."""
    width, height = entry['size']
    # Every side gets a margin, also on axes that do not repeat: the generator tends to paint a dark or light rim
    # at the canvas border, which then bleeds into the opposite edge in game (the sampler repeats). The rim lands
    # in the margin and is cropped away; wrap axes additionally get their seam joined (quilt_wrap).
    if entry.get('_pad'):
        # Margin recorded with this version's reference (wider on sides with neighbour context).
        return {'pad': list(entry['_pad']), 'copies': 1, 'gap': 0, 'stack_axis': None, 'fixed': True}
    override = layout_overrides().get(entry['id'])
    if override:
        # Reviewer-set frame for a texture that only fits one return exactly (e.g. a 384-tall assembly: 4x is the
        # full 1536-pixel height of a 2:3 return, so no vertical margin and a mirrored side margin to reach 2:3).
        return {'pad': list(override['pad']), 'copies': 1, 'gap': 0, 'stack_axis': None, 'fixed': True}
    pad_u = max(4, min(width // 8, 16))
    pad_v = max(4, min(height // 8, 16))
    layout = {'pad': [pad_u, pad_v], 'copies': 1, 'gap': 0, 'stack_axis': None}
    for long_axis, short_axis in (('u', 'v'), ('v', 'u')):
        long_size = width + 2 * pad_u if long_axis == 'u' else height + 2 * pad_v
        short_size = height + 2 * pad_v if long_axis == 'u' else width + 2 * pad_u
        if long_size / short_size <= MAX_ASPECT:
            continue
        short_native = height if long_axis == 'u' else width
        if short_axis in entry['wrap']:
            extra = math.ceil((long_size / 1.5 - short_native) / 2)
            layout['pad'][1 if long_axis == 'u' else 0] = extra
        else:
            gap = max(2, short_size // 4)
            copies = max(2, round((long_size / 1.5 + gap) / (short_size + gap)))
            layout.update(copies=copies, gap=gap, stack_axis=short_axis)
    if layout['copies'] > 1 and scale_for(*copy_boxes(entry, layout)[1]) < SCALE:
        # Stacked copies too large for one return: widen the short axis with mirrored margin instead, so the
        # picture is one copy at 1:2 and still fits one return. Generating it in sections misaligned plank and block
        # rows across the joins (mm8/t68a13l* crate assembly).
        short = layout['stack_axis']
        index = 0 if short == 'u' else 1
        long_size = (height if short == 'u' else width) + 2 * layout['pad'][1 - index]
        native_short = width if short == 'u' else height
        layout.update(copies=1, gap=0, stack_axis=None)
        layout['pad'][index] = max(layout['pad'][index], math.ceil((long_size / MAX_ASPECT - native_short) / 2))
    return layout


def predicted_scale(entry):
    """Expected source pixels per native pixel, assuming ~1.57 MP returns between 1:2 and 2:1."""
    _, total = copy_boxes(entry, layout_for(entry))
    aspect = min(max(total[0] / total[1], 0.5), 2.0)
    width = math.sqrt(1.57e6 * aspect)
    return min(width / total[0], width / aspect / total[1])


def copy_boxes(entry, layout):
    """Native-pixel boxes (x0, y0, x1, y1) of each copy, including its margins, inside the reference."""
    width, height = entry['size']
    pad_u, pad_v = layout['pad']
    copy_w, copy_h = width + 2 * pad_u, height + 2 * pad_v
    boxes = []
    for index in range(layout['copies']):
        if layout['stack_axis'] == 'u':
            x0 = index * (copy_w + layout['gap'])
            boxes.append((x0, 0, x0 + copy_w, copy_h))
        else:
            y0 = index * (copy_h + layout['gap'])
            boxes.append((0, y0, copy_w, y0 + copy_h))
    total = (max(box[2] for box in boxes), max(box[3] for box in boxes))
    return boxes, total


def border_modes(entry):
    """np.pad modes for (v, u): repeating axes wrap; the other sides mirror their own edge.

    A wrapped border on a side that does not repeat shows the opposite edge (often a dark post or frame) right at the
    tile boundary, and the model carries it into the crop as a dark rim. (Repeating the edge column instead was tried
    on MM7 and MM8 and broke the layout: the model rescales the picture to fill the streaked margin.)"""
    return tuple('wrap' if axis in entry['wrap'] else 'symmetric' for axis in ('v', 'u'))


def pad_borders(array, entry, pad_v, pad_u):
    """Pad the first two axes by (pad_v, pad_u) with each axis's border mode."""
    mode_v, mode_u = border_modes(entry)
    extra = [(0, 0)] * (array.ndim - 2)
    array = np.pad(array, [(pad_v, pad_v), (0, 0)] + extra, mode=mode_v)
    return np.pad(array, [(0, 0), (pad_u, pad_u)] + extra, mode=mode_u)


def blur_native(rgba, entry, blur):
    """Gaussian blur of the colour channels in place, wrapping only across repeating edges."""
    modes = ['wrap' if mode == 'wrap' else 'reflect' for mode in border_modes(entry)]
    for channel in range(3):
        rgba[..., channel] = np.clip(ndimage.gaussian_filter(rgba[..., channel].astype(float), blur, mode=modes)
                                     + 0.5, 0, 255).astype(np.uint8)


JOINT_OVERLAP = 4  # native pixels of a context strip next to the joint shown as the neighbour's blurred native


def soften_joint(strip, neighbor_id, side, blur):
    """The context strip with its first JOINT_OVERLAP native pixels (next to the joint) replaced by the neighbour's
    blurred native, enlarged like the core.

    Sharp neighbour art directly against the blurred core is a visible edge exactly on the crop line, and the model
    painted it as a 2-3 master-pixel groove inside the crop (MM8 Ravenshore `t14a07|t14a01`, user 2026-10-10). With the
    overlap the joint sits inside continuous blurred content and the sharp-to-soft step lands in the discarded margin.
    Geometry is unchanged: the replaced pixels are the same neighbour pixels, only at reference sharpness."""
    world, name = neighbor_id.split('/')
    native = native_rgba(open_native(world, name)).copy()
    blur_native(native, textures_entry(neighbor_id), blur)
    height, width = native.shape[:2]
    soft = np.asarray(Image.fromarray(native, 'RGBA').resize((width * SCALE, height * SCALE), Image.LANCZOS))[..., :3]
    band = JOINT_OVERLAP * SCALE
    if side == 'right':
        n = min(band, strip.shape[1]); strip[:, :n] = soft[:strip.shape[0], :n]
    elif side == 'left':
        n = min(band, strip.shape[1]); strip[:, -n:] = soft[:strip.shape[0], -n:]
    elif side == 'bottom':
        n = min(band, strip.shape[0]); strip[:n] = soft[:n, :strip.shape[1]]
    elif side == 'top':
        n = min(band, strip.shape[0]); strip[-n:] = soft[-n:, :strip.shape[1]]
    return strip.astype(float)


def textures_entry(entry_id):
    return inventory()[entry_id]


def make_reference(entry, path, smooth=True, blur=DEFAULT_REF_BLUR, fill=None, filled=None, context=None):
    """Reference image: the blurred native (layout guide), with finished master pixels wherever `fill` is set and,
    on sides with an accepted neighbour, that neighbour's real edge pixels in the margin (`context`)."""
    rgba = native_rgba(open_native(entry['world'], entry['name'])).copy()
    if smooth:
        # Palette dither is a one-pixel checker; a slight blur at native resolution keeps it out of the reference.
        blur_native(rgba, entry, blur)
    scale = 1
    tile = rgba
    if (fill is not None and fill.any()) or context:
        scale = SCALE
        height, width = rgba.shape[:2]
        tile = np.asarray(Image.fromarray(rgba, 'RGBA').resize((width * SCALE, height * SCALE), Image.LANCZOS)).copy()
    if fill is not None and fill.any():
        fill4 = np.kron(fill, np.ones((SCALE, SCALE), bool))
        tile[fill4, :filled.shape[2]] = np.clip(filled[fill4] + 0.5, 0, 255).astype(np.uint8)
        if filled.shape[2] == 3:
            tile[fill4, 3] = 255
    layout = layout_for(entry)
    pad_u, pad_v = layout['pad']
    padded = pad_borders(tile, entry, pad_v * scale, pad_u * scale)
    if context:
        core_h, core_w = tile.shape[:2]
        pu, pv = pad_u * scale, pad_v * scale
        for side, item in context.items():
            other = item['master']
            strip = None
            if side == 'right' and pu:
                strip, rows, cols = other[:, :pu], slice(pv, pv + core_h), slice(pv * 0 + pu + core_w, pu + core_w + pu)
            elif side == 'left' and pu:
                strip, rows, cols = other[:, -pu:], slice(pv, pv + core_h), slice(0, pu)
            elif side == 'bottom' and pv:
                strip, rows, cols = other[:pv], slice(pv + core_h, pv + core_h + pv), slice(pu, pu + core_w)
            elif side == 'top' and pv:
                strip, rows, cols = other[-pv:], slice(0, pv), slice(pu, pu + core_w)
            if strip is not None and strip.shape[:2] == padded[rows, cols].shape[:2]:
                strip = soften_joint(strip[..., :3].copy(), item['id'], side, blur)
                padded[rows, cols, :3] = np.clip(strip + 0.5, 0, 255).astype(np.uint8)
                padded[rows, cols, 3] = 255
    boxes, total = copy_boxes(entry, layout)
    canvas = np.zeros((total[1] * scale, total[0] * scale, 4), np.uint8)
    canvas[:] = GAP_GREY
    for x0, y0, x1, y1 in boxes:
        canvas[y0 * scale:y1 * scale, x0 * scale:x1 * scale] = padded
    sheet = Image.fromarray(canvas, 'RGBA')
    # A smooth enlargement gives the layout and colours without hard pixel blocks the model would copy.
    factor = 1024 / max(sheet.size) if smooth else max(1, 1024 // max(sheet.size))
    reference = sheet.resize((round(sheet.width * factor), round(sheet.height * factor)),
                             Image.LANCZOS if smooth else Image.NEAREST)
    if not entry['cutout']:
        reference = reference.convert('RGB')
    reference.save(path)
    return {**layout, 'size': list(reference.size), 'smooth': smooth}


SECTION_OVERLAP = 12   # native pixels each section reaches into its earlier neighbours
SECTION_MIN_SCALE = 4.25


def scale_for(width, height):
    """Expected source pixels per native pixel for a width x height reference (~1.57 MP, 1:2..2:1 returns)."""
    aspect = min(max(width / height, 0.5), 2.0)
    side = math.sqrt(1.57e6 * aspect)
    return min(side / width, side / aspect / height)


def section_plan(entry):
    """Overlapping boxes (native padded coordinates) for textures too large for one 4x generation, else None."""
    layout = layout_for(entry)
    if layout.get('fixed'):
        return None
    _, (width, height) = copy_boxes(entry, layout)
    if entry.get('predicted_scale', SCALE) >= SCALE and 0.5 <= width / height <= 2.0:
        return None
    options = sorted(((kx, ky) for kx in range(1, 5) for ky in range(1, 5)), key=lambda k: (k[0] * k[1], k))
    for kx, ky in options:
        section_w = math.ceil(width / kx) + (SECTION_OVERLAP if kx > 1 else 0)
        section_h = math.ceil(height / ky) + (SECTION_OVERLAP if ky > 1 else 0)
        if 0.5 <= section_w / section_h <= 2.0 and scale_for(section_w, section_h) >= SECTION_MIN_SCALE:
            break
    boxes = []
    for iy in range(ky):
        for ix in range(kx):
            x0, x1 = round(ix * width / kx), round((ix + 1) * width / kx)
            y0, y1 = round(iy * height / ky), round((iy + 1) * height / ky)
            boxes.append([max(0, x0 - (SECTION_OVERLAP if ix else 0)), max(0, y0 - (SECTION_OVERLAP if iy else 0)),
                          x1, y1])
    return boxes


def padded_prefill(entry, fill, filled):
    """Family prefill mapped into the wrap-padded canvas used by sections (native mask, 4x pixels)."""
    pad_u, pad_v = layout_for(entry)['pad']
    mask = pad_borders(fill, entry, pad_v, pad_u)
    pixels = pad_borders(filled, entry, pad_v * SCALE, pad_u * SCALE)
    return mask, pixels


def assemble_sections(entry, job_dir, name, version, upto, fill, filled):
    """Canvas (4x, padded) of finished pixels from family prefill and sections < upto, plus its 4x mask."""
    boxes = section_plan(entry)
    _, (width, height) = copy_boxes(entry, layout_for(entry))
    channels = 4 if entry['cutout'] else 3
    canvas = np.zeros((height * SCALE, width * SCALE, channels), float)
    assigned = np.zeros((height * SCALE, width * SCALE), bool)
    prefilled = np.zeros((height * SCALE, width * SCALE), bool)
    if fill is not None and fill.any():
        mask, pixels = padded_prefill(entry, fill, filled)
        mask4 = np.kron(mask, np.ones((SCALE, SCALE), bool))
        canvas[mask4] = pixels[mask4]
        assigned |= mask4
        prefilled |= mask4
    for index, (x0, y0, x1, y1) in enumerate(boxes[:upto]):
        raw = Image.open(job_dir / 'raw' / f'{name}_v{version}_s{index}.png')
        raw = raw.convert('RGBA' if channels == 4 else 'RGB')
        part = np.asarray(raw.resize(((x1 - x0) * SCALE, (y1 - y0) * SCALE), Image.LANCZOS)).astype(float)
        region = (slice(y0 * SCALE, y1 * SCALE), slice(x0 * SCALE, x1 * SCALE))
        overlap = assigned[region]
        if overlap.mean() >= 0.02:
            # Match the new section to the finished pixels it continues (linear-light gain per channel).
            for channel in range(3):
                have = srgb_to_linear(canvas[region][..., channel][overlap]).mean()
                got = srgb_to_linear(part[..., channel][overlap]).mean()
                part[..., channel] = linear_to_srgb(srgb_to_linear(part[..., channel]) * have / max(got, 1e-6))
        new = ~overlap
        # Join earlier sections along a minimum-error cut through the shared overlap strip instead of a straight
        # line where the strip ends: the model never repaints the overlap exactly, and the straight edge showed as
        # a rectangle in amorphous art (mm8/stormclds). Copied family pixels stay fixed.
        band = SECTION_OVERLAP * SCALE
        for strip_axis, start in (('u', x0), ('v', y0)):
            if not start:
                continue
            old = canvas[region]
            if strip_axis == 'v':
                old, new_part, take = (np.transpose(old, (1, 0, 2)), np.transpose(part, (1, 0, 2)), new.T)
            else:
                new_part, take = part, new
            error = (luma(old[:, :band]) - luma(new_part[:, :band])) ** 2
            cut = min_cut_columns(ndimage.uniform_filter(error, 3))
            take[:, :band] = np.arange(band)[None, :] >= cut[:, None]
        new &= ~prefilled[region]
        target = canvas[region]
        target[new] = part[new]
        canvas[region] = target
        assigned[region] = True
    return canvas, assigned


def make_section_reference(entry, path, box, canvas, assigned, blur):
    """Crop of the blurred padded native at `box`, with every finished pixel pasted sharp."""
    rgba = native_rgba(open_native(entry['world'], entry['name'])).copy()
    blur_native(rgba, entry, blur)
    pad_u, pad_v = layout_for(entry)['pad']
    padded = pad_borders(rgba, entry, pad_v, pad_u)
    x0, y0, x1, y1 = box
    crop = Image.fromarray(padded[y0:y1, x0:x1], 'RGBA')
    big = np.asarray(crop.resize(((x1 - x0) * SCALE, (y1 - y0) * SCALE), Image.LANCZOS)).copy()
    region = (slice(y0 * SCALE, y1 * SCALE), slice(x0 * SCALE, x1 * SCALE))
    done = assigned[region]
    big[done, :canvas.shape[2]] = np.clip(canvas[region][done] + 0.5, 0, 255).astype(np.uint8)
    big[done, 3] = 255 if canvas.shape[2] == 3 else big[done, 3]
    image = Image.fromarray(big, 'RGBA')
    factor = 1024 / max(image.size)
    image = image.resize((round(image.width * factor), round(image.height * factor)), Image.LANCZOS)
    if not entry['cutout']:
        image = image.convert('RGB')
    image.save(path)
    return float(done.mean())


def build_prompt(entry, note='', prefilled=0.0):
    width, height = entry['size']
    layout = layout_for(entry)
    pad_u, pad_v = layout['pad']
    wrap = entry['wrap']
    kind = 'flat repeating surface albedo texture' if wrap else 'flat surface albedo texture'
    wrap_text = {'u': ', repeating horizontally', 'v': ', repeating vertically',
                 'uv': ', repeating in both directions'}.get(wrap, '')
    if pad_u or pad_v:
        free = 'a mirror of the edge'
        border = {'uv': 'showing the neighbouring repeats',
                  'u': f'showing the neighbouring repeats left/right and {free} top/bottom',
                  'v': f'showing the neighbouring repeats top/bottom and {free} left/right'}.get(
                      wrap, 'showing ' + free)
        pad_text = (f', surrounded by a border ({pad_u} original pixels left/right, {pad_v} top/bottom) '
                    f'{border}; the border must continue the same layout seamlessly')
        pad_keep = ' including the border'
    else:
        pad_text, pad_keep = '', ''
    if layout['copies'] > 1:
        pad_text += (f". The reference shows {layout['copies']} identical copies of this narrow strip separated by flat "
                     'grey gaps: redraw every copy as the same strip and keep the gaps flat grey')
        pad_keep += ' and every copy'
    if note_context := entry.get('_context_sides'):
        pad_text += (f". The {' and '.join(note_context)} border of Reference 1 is finished high-resolution artwork of "
                     'the neighbouring wall piece: the texture must continue it seamlessly across that edge (same '
                     'courses, planks, joints, colours and brightness)')
    if prefilled > 0:
        pad_text += ('. Most of Reference 1 is already finished high-resolution artwork (the sharp areas); only the '
                     'soft, blurry area(s) are a low-resolution guide. Keep every finished area exactly as it is: the '
                     'same stones, joints, colours and lighting. Repaint only the soft area(s) as new high-definition '
                     'artwork that continues the finished areas seamlessly')
    alpha_text = ('. Transparent areas of the reference must stay truly transparent (PNG alpha); '
                  'opaque areas stay opaque' if entry['cutout'] else ', opaque')
    material = (entry.get('material') or 'the same materials as the reference').rstrip('.') + ';'
    era, artefacts = ERA.get(entry['world'], ERA_DEFAULT)
    prompt = PROMPT_TEMPLATE.format(kind=kind, era=era, artefacts=artefacts, width=width, height=height,
                                    wrap_text=wrap_text, pad_text=pad_text,
                                    material=material, pad_keep=pad_keep, alpha_text=alpha_text)
    if note:
        prompt += '\nCorrection for this attempt: ' + note.strip()
    return prompt


def create_job(job_id, world, map_names, members, textures):
    job_dir = JOBS / job_id
    for sub in ('refs', 'prompts', 'raw', 'candidates', 'review'):
        (job_dir / sub).mkdir(parents=True, exist_ok=True)
    requests = {}
    for member in members:
        entry = textures[member]
        requests[member] = {'name': entry['name'], 'versions': [],
                            'material': entry.get('material', ''), 'notes': {}}
    write_json(job_dir / 'job.json', {'id': job_id, 'world': world, 'maps': map_names, 'created': now(),
                                      'textures': members, 'requests': requests})
    sheet = contact_natives(job_dir, members, textures)
    print(f'{job_id}: {len(members)} textures; natives sheet {rel(sheet)}')


def contact_natives(job_dir, members, textures):
    """One labelled sheet of the job's natives so materials can be described before generation."""
    cell = 160
    columns = 6
    rows = math.ceil(len(members) / columns)
    sheet = Image.new('RGB', (columns * cell, rows * (cell + 14)), (32, 32, 32))
    draw = ImageDraw.Draw(sheet)
    for index, member in enumerate(members):
        image = open_native(textures[member]['world'], textures[member]['name']).convert('RGB')
        image.thumbnail((cell - 8, cell - 8), Image.NEAREST)
        x, y = index % columns * cell, index // columns * (cell + 14)
        sheet.paste(image, (x + 4, y + 4))
        draw.text((x + 4, y + cell - 2), f"{textures[member]['name']} {textures[member]['wrap'] or '-'}",
                  fill=(230, 230, 230))
    path = job_dir / 'review' / 'natives.png'
    sheet.save(path)
    return path


# ------------------------------------------------------------------------------------------------- gen

WORKER_PROMPT = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image as the reference image and the IMAGE PROMPT below{alpha}.
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""


def run_worker(job_dir, member, request, version, entry, section=None):
    name = request['name']
    tag = f'v{version}' if section is None else f'v{version}_s{section["index"]}'
    prefilled = request.get('prefill', {}).get(str(version), {}).get('fraction', 0.0)
    note = request['notes'].get(str(version), '')
    if section is not None:
        prefilled = section['finished']
        note = (f"This reference is section {section['index'] + 1} of {section['count']} of a larger texture and "
                'shows only that part; redraw exactly this part at the reference framing. ' + note)
    sides = sorted(request.get('context', {}).get(str(version), {})) if section is None else []
    prompt = build_prompt({**entry, 'material': request.get('material') or entry.get('material', ''),
                           '_context_sides': sides}, note, prefilled)
    (job_dir / 'prompts' / f'{name}_{tag}.txt').write_text(prompt + '\n')
    target = job_dir / 'raw' / f'{name}_{tag}.png'
    worker = WORKER_PROMPT.format(prompt=prompt, target=target,
                                  alpha=' and a transparent background' if entry['cutout'] else '')
    log = job_dir / 'raw' / f'{name}_{tag}.log'
    reference = job_dir / 'refs' / f'{name}_{tag}.png'
    started = time.time()
    with open(log, 'w') as stream:
        # The prompt goes through stdin: `-i` accepts several files and would swallow a positional prompt.
        try:
            process = subprocess.run(
                ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(job_dir), '--skip-git-repo-check',
                 '-i', str(reference)],
                input=worker, text=True, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            # One hung worker is a failed attempt, not the end of the scheduler (it retries once more).
            stream.write('\ntex.py: worker timed out after 900 s\n')
            returncode = -1
    seconds = round(time.time() - started)
    ok = target.exists() and returncode == 0
    return member, version, ok, seconds


def open_job_ids(state, worlds=None):
    """Jobs that still have claimed or candidate textures, oldest first."""
    ids = []
    for path in sorted(JOBS.glob('*/job.json')):
        job = load_json(path)
        if worlds and job['world'] not in worlds:
            continue
        if any(state.get(member, {}).get('status') in ('claimed', 'candidate')
               and state[member].get('job') == job['id'] for member in job['textures']):
            ids.append(job['id'])
    return ids


def scan_job(job_id, only, running, attempts, limit, state, textures, work):
    job_dir = JOBS / job_id
    with job_lock(job_dir):
        job = load_json(job_dir / 'job.json')
        changed = False
        for member, request in job['requests'].items():
            if len(work) >= limit:
                break
            record = state.get(member, {})
            if record.get('status') not in ('claimed', 'candidate') or record.get('job') != job_id:
                continue  # accepted, released back to pending, or claimed again by a later job
            if only and request['name'] not in only:
                continue
            spec = textures[member].get('assembly')
            if spec and spec['head'] != member:
                continue  # generated as part of its assembly head
            if request.get('rotate_from') or request.get('copy_from'):
                continue  # cut from an accepted master by `check`, never generated
            if not request.get('material'):
                continue  # materials are written per job before generation
            entry = generation_entry(member, textures)
            pending_versions = [v for v in request['versions'] or [1]
                                if not (job_dir / 'raw' / f"{request['name']}_v{v}.png").exists()]
            # Standalone pieces (reviewer's choice, e.g. chest panels that never sit beside their relatives) are
            # generated from their own native only: no waiting for, copying from or deriving from relatives.
            standalone = request.get('standalone', False)
            if not pending_versions or (not standalone and waiting_for(entry, textures, state)):
                continue
            fill, filled, used = ((None, None, []) if standalone
                                  else prefill(entry, textures, state, request.get('prefill_from')))
            if fill is not None and derivable(entry, fill):
                continue
            if not request['versions']:
                request['versions'].append(1)
                changed = True
            boxes = section_plan(entry)
            for version in pending_versions:
                if boxes:
                    item = next_section(job_dir, member, entry, request, version, boxes, fill, filled, used,
                                        running, attempts, job_id)
                    if item == 'assembled':
                        changed = True
                    elif item:
                        work.append(item)
                        changed = True
                    continue
                key = (job_id, request['name'], version)
                log = job_dir / 'raw' / f"{request['name']}_v{version}.log"
                busy_elsewhere = key not in attempts and log.exists() and time.time() - log.stat().st_mtime < 900
                if key in running or attempts.get(key, 0) >= 2 or busy_elsewhere:
                    continue
                reference = job_dir / 'refs' / f"{request['name']}_v{version}.png"
                if not reference.exists():
                    blur = request.get('ref_blur', {}).get(str(version), DEFAULT_REF_BLUR)
                    context = neighbor_context(entry, textures, state)
                    roll = (request.get('roll') or {}).get(str(version))
                    if roll:
                        # Rolled versions show the texture's own wrapped edges instead of neighbour margins.
                        rolled_fill, rolled_filled = roll_fill(fill, filled, roll)
                        context = roll_context(context, roll)
                        make_reference(rolled_entry(entry, roll), reference, blur=blur, fill=rolled_fill,
                                       filled=rolled_filled, context=context)
                    else:
                        pad = context_pad(entry, context)
                        if pad:
                            request.setdefault('pad', {})[str(version)] = pad
                        make_reference({**entry, '_pad': pad} if pad else entry, reference, blur=blur, fill=fill,
                                       filled=filled, context=context)
                    request.setdefault('prefill', {})[str(version)] = {
                        'sources': used, 'fraction': round(coverage(entry, fill), 3) if fill is not None else 0.0}
                    request.setdefault('context', {})[str(version)] = {side: item['id']
                                                                       for side, item in context.items()}
                    changed = True
                work.append((key, job_dir, member, request, version))
        if changed:
            write_json(job_dir / 'job.json', job)



def scan_work(job_ids, only, running, attempts, limit=10 ** 6, worlds=None):
    """Raw images still missing, skipping ones another process is producing right now.

    Family pieces wait for higher-priority relatives that are still in progress; pieces fully covered by accepted
    relatives need no generation (`check` derives them). References are built here, from the current masters."""
    state = ledger_state()
    textures = inventory()
    work = []
    for job_id in job_ids or open_job_ids(state, worlds):
        scan_job(job_id, only, running, attempts, limit, state, textures, work)
    return work


def next_section(job_dir, member, entry, request, version, boxes, fill, filled, used, running, attempts, job_id):
    """The next section to generate for a sectioned version, 'assembled' when all are done, else None."""
    name = request['name']
    done = [index for index in range(len(boxes)) if (job_dir / 'raw' / f'{name}_v{version}_s{index}.png').exists()]
    index = len(done)
    if done != list(range(index)):
        return None
    if index == len(boxes):
        canvas, _ = assemble_sections(entry, job_dir, name, version, index, fill, filled)
        mode = 'RGBA' if canvas.shape[2] == 4 else 'RGB'
        Image.fromarray(np.clip(canvas + 0.5, 0, 255).astype(np.uint8), mode).save(job_dir / 'raw' / f'{name}_v{version}.png')
        request.setdefault('prefill', {})[str(version)] = {
            'sources': used, 'fraction': round(coverage(entry, fill), 3) if fill is not None else 0.0}
        request.setdefault('sections', {})[str(version)] = boxes
        return 'assembled'
    key = (job_id, name, version, index)
    log = job_dir / 'raw' / f'{name}_v{version}_s{index}.log'
    if key in running or attempts.get(key, 0) >= 2 or (key not in attempts and log.exists()
                                                         and time.time() - log.stat().st_mtime < 900):
        return None
    canvas, assigned = assemble_sections(entry, job_dir, name, version, index, fill, filled)
    blur = request.get('ref_blur', {}).get(str(version), DEFAULT_REF_BLUR)
    finished = make_section_reference(entry, job_dir / 'refs' / f'{name}_v{version}_s{index}.png', boxes[index],
                                      canvas, assigned, blur)
    return key, job_dir, member, request, version, {'index': index, 'count': len(boxes), 'finished': finished}


def cmd_gen(args):
    """Keep up to --parallel codex workers busy; rescan after every completion so queued retries join in."""
    locks = gen_locks(args.world)
    textures = inventory()
    if args.jobs and args.world:
        foreign = [job_id for job_id in args.jobs if load_json(JOBS / job_id / 'job.json')['world'] not in args.world]
        if foreign:
            sys.exit(f'jobs outside --world {" ".join(args.world)}: {" ".join(foreign)}')
    running, attempts = {}, {}
    # Family pieces wait for accepted relatives; sections become ready one after another while this runs.
    done_count = failures = 0
    with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
        while True:
            if len(running) < args.parallel:
                for item in scan_work(args.jobs, args.only, set(running.values()), attempts,
                                      args.parallel - len(running), args.world):
                    key, job_dir, member, request, version = item[:5]
                    section = item[5] if len(item) > 5 else None
                    attempts[key] = attempts.get(key, 0) + 1
                    entry = generation_entry(member, textures) if section else version_entry(
                        member, textures, request, version)
                    future = pool.submit(run_worker, job_dir, member, request, version, entry, section)
                    running[future] = key
                    if len(running) >= args.parallel:
                        break
            if not running:
                if args.follow and open_job_ids(ledger_state(), args.world):
                    time.sleep(30)  # waiting for materials, accepted relatives or retries
                    continue
                break
            finished, _ = concurrent.futures.wait(running, timeout=30,
                                                  return_when=concurrent.futures.FIRST_COMPLETED)
            for future in finished:
                job_id, name, version = running.pop(future)[:3]
                _, _, ok, seconds = future.result()
                done_count += 1
                failures += not ok
                print(f"{datetime.now():%H:%M:%S} {'ok ' if ok else 'FAIL'} {job_id} {name}_v{version} {seconds}s "
                      f"[{len(running)} running]", flush=True)
    print(f'done; {done_count} generated, {failures} failures (see raw/*.log)')
    for lock in locks:
        lock.close()


def gen_locks(worlds):
    """One scheduler per world, so one session per world can run its own; a scheduler for all worlds excludes all.

    `.gen.lock` is held exclusively by an all-worlds scheduler and shared by per-world ones, which also hold their
    world's `.gen-<world>.lock` exclusively."""
    locks = []
    for name, mode in [('.gen.lock', fcntl.LOCK_SH if worlds else fcntl.LOCK_EX)] + \
            [(f'.gen-{world}.lock', fcntl.LOCK_EX) for world in worlds or []]:
        stream = open(HERE / name, 'w')
        try:
            fcntl.flock(stream, mode | fcntl.LOCK_NB)
        except BlockingIOError:
            scope = f'for {name[5:-5]}' if name != '.gen.lock' else 'for all worlds' if worlds else 'for some world'
            sys.exit(f'a `tex.py gen` scheduler {scope} is already running; it picks up new work in its scope by '
                     'itself')
        locks.append(stream)
    return locks


def cmd_materials(args):
    with job_lock(JOBS / args.job):
        materials_locked(args)


def materials_locked(args):
    """Read `name: material description` lines from stdin into the job's requests (before `gen`)."""
    job_dir = JOBS / args.job
    job = load_json(job_dir / 'job.json')
    by_name = {request['name']: request for request in job['requests'].values()}
    updated = 0
    for line in sys.stdin.read().splitlines():
        name, separator, text = line.partition(':')
        if separator and name.strip().lower() in by_name:
            request = by_name[name.strip().lower()]
            # A trailing "[standalone]" generates the piece without copying accepted relatives (see `retry`).
            standalone = re.search(r'\s*\[standalone\]\s*$', text)
            if standalone:
                text = text[:standalone.start()]
                request['standalone'] = True
            # A trailing "[blur=2.5]" sets the reference blur of the next version (random speckle materials).
            match = re.search(r'\[blur=([0-9.]+)\]\s*$', text)
            if match:
                text = text[:match.start()]
                version = max(request['versions'] or [0]) if request['versions'] and not (
                    job_dir / 'raw' / f"{request['name']}_v{max(request['versions'])}.png").exists() else \
                    max(request['versions'] or [0]) + 1
                request.setdefault('ref_blur', {})[str(version or 1)] = float(match.group(1))
            request['material'] = text.strip()
            updated += 1
    write_json(job_dir / 'job.json', job)
    missing = [name for name, request in by_name.items() if not request.get('material')]
    print(f'updated {updated}; without material: {" ".join(missing) or "-"}')


def cmd_retry(args):
    with job_lock(JOBS / args.job):
        retry_locked(args)


def retry_locked(args):
    job_dir = JOBS / args.job
    job = load_json(job_dir / 'job.json')
    member = next(m for m, r in job['requests'].items() if r['name'] == args.name)
    request = job['requests'][member]
    version = max(request['versions'] or [0]) + 1
    request['versions'].append(version)
    if args.note:
        request['notes'][str(version)] = args.note
    if args.material is not None:
        request['material'] = args.material
    if args.ref_blur is not None:
        request.setdefault('ref_blur', {})[str(version)] = args.ref_blur
    if args.standalone:
        request['standalone'] = True
    if args.prefill_from:
        world = member.split('/')[0]
        request['prefill_from'] = [f'{world}/{name}' for name in args.prefill_from.split(',')]
    if args.match_neighbor:
        request['match_neighbor'] = True
    if args.rotate_from:
        source_name, _, k = args.rotate_from.partition(':')
        world = member.split('/')[0]
        source = native_rgba(open_native(world, source_name))
        own = native_rgba(open_native(world, args.name))
        if not np.array_equal(np.rot90(source, int(k)), own):
            sys.exit(f'{args.name} is not {source_name} rotated by {k} quarter turns')
        request['rotate_from'] = {'id': f'{world}/{source_name}', 'k': int(k)}
        request['versions'].remove(version)
    if args.copy_from:
        source_name, dx, dy = (args.copy_from.split(':') + ['0', '0'])[:3]
        world = member.split('/')[0]
        source = native_rgba(open_native(world, source_name)).astype(float)
        if args.mirror:
            source = source[:, ::-1]
        own = native_rgba(open_native(world, args.name)).astype(float)
        window = np.roll(source, (-int(dy), -int(dx)), axis=(0, 1))[:own.shape[0], :own.shape[1]]
        difference = np.abs(window - own)[..., :3].mean() if window.shape == own.shape else 255.0
        if difference > COPY_TOLERANCE:
            sys.exit(f'{args.name} differs from {source_name} at {dx},{dy} by {difference:.1f} per channel')
        request['copy_from'] = {'id': f'{world}/{source_name}', 'dx': int(dx), 'dy': int(dy), 'mirror': args.mirror}
        request['versions'].remove(version)
    if args.roll:
        entry = generation_entry(member, inventory())
        if section_plan(entry) or entry.get('assembly'):
            sys.exit(f'{args.name}: sectioned or assembly textures cannot be rolled')
        blocked = neighbor_axes(entry) & set(args.roll)
        if blocked and not args.drop_context:
            sys.exit(f'{args.name}: abuts other textures along {"".join(sorted(blocked))}; roll only the other axis '
                     'or pass --drop-context (the joint check still measures those neighbours)')
        native = native_rgba(open_native(entry['world'], entry['name']))
        request.setdefault('roll', {})[str(version)] = [quiet_offset(native, 'u') if 'u' in args.roll else 0,
                                                       quiet_offset(native, 'v') if 'v' in args.roll else 0]
    write_json(job_dir / 'job.json', job)
    if args.rotate_from or args.copy_from:
        print(f'{args.name} will be cut from an accepted master; run `tex.py check {args.job}`')
    else:
        print(f'queued {args.name}_v{version}; run `tex.py gen {args.job}`')


# ----------------------------------------------------------------------------------------------- check

def srgb_to_linear(values):
    values = values / 255.0
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(values):
    values = np.clip(values, 0, 1)
    return np.clip(np.where(values <= 0.0031308, values * 12.92, 1.055 * values ** (1 / 2.4) - 0.055) * 255, 0, 255)


def luma(rgb):
    return rgb[..., :3].astype(float) @ np.array([0.2126, 0.7152, 0.0722])


def min_cut_columns(error):
    """Minimum-error vertical path through an (h, w) overlap; returns the cut column per row."""
    height, width = error.shape
    cost = error.copy()
    for y in range(1, height):
        previous = cost[y - 1]
        left = np.r_[np.inf, previous[:-1]]
        right = np.r_[previous[1:], np.inf]
        cost[y] += np.minimum(np.minimum(left, previous), right)
    path = np.zeros(height, int)
    path[-1] = int(np.argmin(cost[-1]))
    for y in range(height - 2, -1, -1):
        x = path[y + 1]
        low, high = max(0, x - 1), min(width, x + 2)
        path[y] = low + int(np.argmin(cost[y, low:high]))
    return path


def quilt_wrap(extended, core_box, axis):
    """Make the core periodic along one axis by min-cut joining the generated trailing margin onto its start.

    `extended` holds the core plus the generated wrap margins. The trailing margin continues the core across the
    tile boundary, so taking it left of a minimum-error cut through the overlap with the core's own leading strip
    makes the tile edge continuous without blending or repainting."""
    x0, y0, x1, y1 = core_box
    if axis == 'v':
        transposed = quilt_wrap(np.transpose(extended, (1, 0, 2)), (y0, x0, y1, x1), 'u')
        return np.transpose(transposed, (1, 0, 2))
    result = extended.copy()
    margin = min(x0, extended.shape[1] - x1)
    if margin < 2:
        return result
    trailing = extended[y0:y1, x1:x1 + margin].astype(float)
    leading = extended[y0:y1, x0:x0 + margin].astype(float)
    error = ((luma(trailing) - luma(leading)) ** 2)
    cut = min_cut_columns(ndimage.uniform_filter(error, 3))
    columns = np.arange(margin)[None, :]
    take_trailing = columns < cut[:, None]
    region = result[y0:y1, x0:x0 + margin]
    region[take_trailing] = extended[y0:y1, x1:x1 + margin][take_trailing]
    return result


def seam_ratio(tile, axis):
    data = luma(tile)
    if axis == 'v':
        data = data.T
    interior = np.abs(np.diff(data, axis=1)).mean()
    boundary = np.abs(data[:, 0] - data[:, -1]).mean()
    return float(boundary / max(interior, 1e-6))


def register(native_luma, candidate_luma):
    """Sub-pixel translation (native pixels) of the candidate relative to the native via phase correlation."""
    a = ndimage.gaussian_filter(native_luma, 1.0)
    b = ndimage.gaussian_filter(candidate_luma, 1.0)
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa, fb = np.fft.fft2((a - a.mean()) * window), np.fft.fft2((b - b.mean()) * window)
    product = fa * np.conj(fb)
    correlation = np.fft.ifft2(product / (np.abs(product) + 1e-9)).real
    peak = np.unravel_index(np.argmax(correlation), correlation.shape)
    shift = [p if p <= s // 2 else p - s for p, s in zip(peak, correlation.shape)]
    return float(shift[1]), float(shift[0])


def build_candidate(entry, raw_path, reference, fill=None, filled=None):
    """Candidate master from one raw return; with stacked copies, the copy with the fewest flags wins."""
    width, height = entry['size']
    raw = Image.open(raw_path)
    raw = raw.convert('RGBA') if entry['cutout'] else raw.convert('RGB')
    boxes, total = copy_boxes(entry, reference)
    sx, sy = raw.width / total[0], raw.height / total[1]
    # Resample the whole return so each core is exactly 4x native; margins and gaps scale with it.
    extended = np.asarray(raw.resize((total[0] * SCALE, total[1] * SCALE), Image.LANCZOS)).astype(float)
    native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
    best = None
    for index, (x0, y0, x1, y1) in enumerate(boxes):
        part = extended[y0 * SCALE:y1 * SCALE, x0 * SCALE:x1 * SCALE]
        image, metrics, flags = candidate_from(entry, part, reference['pad'], native, fill, filled)
        metrics.update(raw_size=list(raw.size), source_scale=round(min(sx, sy), 2))
        if min(sx, sy) < SCALE:
            flags.insert(0, f'budget {min(sx, sy):.2f}x<{SCALE}x')
        if len(boxes) > 1:
            metrics['copy'] = index
        score = (len(flags), -metrics['layout_corr'])
        if best is None or score < best[0]:
            best = (score, image, metrics, flags)
    return best[1], best[2], best[3]


def brightness_target():
    return (load_json(CONFIG, {}) or {}).get('brightness', 'native')


def target_means(entry, native, opaque):
    """Per-channel linear means a master must reproduce: the native's, or the ESRGAN baseline's."""
    source = native
    if brightness_target() == 'esrgan' and entry.get('esrgan_x4'):
        esrgan = Image.open(ROOT / entry['esrgan_x4']).convert('RGBA' if native.shape[2] == 4 else 'RGB')
        source = np.asarray(esrgan.resize((native.shape[1], native.shape[0]), Image.LANCZOS)).astype(float)
    return [float(srgb_to_linear(source[..., channel])[opaque].mean()) for channel in range(3)]


def edge_ratios(master, native):
    """Outermost native-pixel row/column brightness of the master relative to the native's (sides with light edges).

    The sampler repeats textures, so a dark rim the model added at one edge bleeds into the opposite edge in game."""
    height, width = native.shape[:2]
    reduced = luma(np.asarray(Image.fromarray(master[..., :3].astype(np.uint8)).resize((width, height), Image.BOX))
                   .astype(float))
    original = luma(native[..., :3])
    ratios = {}
    for side, a, b in (('top', original[0], reduced[0]), ('bottom', original[-1], reduced[-1]),
                       ('left', original[:, 0], reduced[:, 0]), ('right', original[:, -1], reduced[:, -1])):
        if a.mean() > 40:
            ratios[side] = float(b.mean() / a.mean())
    return ratios


RIM_LINES = 8          # master-pixel lines per side checked for thin rims (two native pixels)


BOUNDARY_FLAGS = ('seam', 'edge', 'rim')


def boundary_checks(master, native, wrap):
    """Seam, edge and rim metrics/flags of a master in its final (unrolled) frame."""
    metrics, flags = {}, []
    height, width = native.shape[:2]
    reduced = np.asarray(Image.fromarray(master.astype(np.uint8)).resize((width, height), Image.LANCZOS)).astype(float)
    for axis in wrap:
        ratio = seam_ratio(reduced, axis)
        native_ratio = seam_ratio(native, axis)
        metrics[f'seam_{axis}'] = [round(ratio, 2), round(native_ratio, 2)]
        if ratio > SEAM_TOLERANCE * native_ratio + 0.3:
            flags.append(f'seam {axis} {ratio:.1f} vs {native_ratio:.1f}')
    for side, ratio in edge_ratios(master, native).items():
        metrics[f'edge_{side}'] = round(ratio, 2)
        if not 0.6 <= ratio <= 2.2:  # dark rims bleed as dark seams; thin bright joints are harmless
            flags.append(f'edge {side} {ratio:.2f}')
    for side, (dark, bright) in rim_ratios(master, native, wrap).items():
        metrics[f'rim_{side}'] = [round(dark, 2), round(bright, 2)]
        if dark < 0.6 or bright > 1.8:
            flags.append(f'rim {side} {dark:.2f}/{bright:.2f}')
    for side, run in boundary_lines(master, native, wrap).items():
        metrics[f'line_{side}'] = run
        if run >= BOUNDARY_LINE_RUN:
            flags.append(f'line {side} {run}px')
    return metrics, flags


BOUNDARY_LINE_RUN = 8  # native pixels in a row of an off-colour boundary line before it is flagged


def boundary_lines(master, native, wrap=''):
    """Longest run per side (native pixels) where only the outermost two master pixels leave the native's edge colour.

    The generator often moves an edge joint a couple of master pixels inward and leaves a pale or dark hairline on the
    tile boundary itself; `rim` averages whole sides and misses it when it covers only part of an edge. A position
    counts when the outer two master pixels differ from the native edge pixel by more than 70 in some channel while
    master pixels 4-7 inside still match it (within 50): a line on the boundary, not a moved or redrawn feature. On a
    repeating axis the native pixel across the seam (the opposite edge) is equally valid: a joint the native draws on
    one side of the seam may land on the other."""
    runs = {}
    opaque = native[..., 3] > 127 if native.shape[2] == 4 else np.ones(native.shape[:2], bool)
    for side, flip, axis in (('top', lambda a: a, 'v'), ('bottom', lambda a: a[::-1], 'v'),
                             ('left', lambda a: a.swapaxes(0, 1), 'u'), ('right', lambda a: a.swapaxes(0, 1)[::-1], 'u')):
        rows = flip(native[..., :3].astype(float))
        edge = rows[0]
        lines = flip(master[..., :3].astype(float))
        outer = lines[:2].mean(axis=0).reshape(-1, SCALE, 3).mean(axis=1)
        inner = lines[4:8].mean(axis=0).reshape(-1, SCALE, 3).mean(axis=1)
        bad = ((np.abs(outer - edge).max(axis=1) > 70) & (np.abs(inner - edge).max(axis=1) < 50)
               & flip(opaque)[0])
        if axis in wrap:
            bad &= np.abs(outer - rows[-1]).max(axis=1) > 70
        best = current = 0
        for value in bad:
            current = current + 1 if value else 0
            best = max(best, current)
        runs[side] = best
    return runs


def rim_ratios(master, native, wrap=''):
    """Darkest and brightest of the outermost master-pixel lines per side, against the native's edge rows.

    `edge_ratios` averages a whole native-pixel row, which hides a one or two master-pixel dark (or pale) line painted
    along the crop boundary; the sampler repeats it into a hairline seam. The native reference is the darkest and
    brightest of its three outer rows, so a joint the generator moved by a native pixel is not a rim."""
    lines = luma(master[..., :3].astype(float))
    rows = luma(native[..., :3].astype(float))
    ratios = {}
    for side, flip, axis in (('top', lambda a: a, 'v'), ('bottom', lambda a: a[::-1], 'v'),
                             ('left', lambda a: a.T, 'u'), ('right', lambda a: a.T[::-1], 'u')):
        native_rows = [float(flip(rows)[k].mean()) for k in range(min(3, flip(rows).shape[0]))]
        if min(native_rows) <= 40:
            continue
        if axis in wrap:
            # On a repeating axis the game shows the opposite edge across this seam: a joint the native splits
            # between the two edges is real content on both sides, not a rim.
            native_rows += [float(flip(rows)[-1 - k].mean()) for k in range(min(3, flip(rows).shape[0]))]
        master_lines = [float(flip(lines)[k].mean()) for k in range(RIM_LINES)]
        # Added wrap rows can be pure black (a dark joint on the opposite edge); keep the ratio finite.
        ratios[side] = (min(master_lines) / max(min(native_rows), 1.0), max(master_lines) / max(max(native_rows), 1.0))
    return ratios


def traced_correlation(master, native):
    """How much of the master's finest detail follows the native's pixel staircase instead of new material.

    The staircase is the blocky (nearest) enlargement minus the smooth (Lanczos) one: it holds only the pixel-grid
    steps, not the real edges, so sharp geometric art aligned to the native (checkerboards, grooves) is not penalised
    while a traced raster is."""
    height, width = master.shape[:2]
    source = Image.fromarray(native.astype(np.uint8))
    blocky = luma(np.asarray(source.resize((width, height), Image.NEAREST)).astype(float))
    smooth = luma(np.asarray(source.resize((width, height), Image.LANCZOS)).astype(float))
    staircase = blocky - smooth
    detail = luma(master)
    detail -= ndimage.gaussian_filter(detail, 1.2)
    if detail.std() < 1e-6 or staircase.std() < 1e-6:
        return 0.0
    return float(np.corrcoef(detail.ravel(), staircase.ravel())[0, 1])


def candidate_from(entry, extended, pad, native, fill=None, filled=None):
    width, height = entry['size']
    target = (width * SCALE, height * SCALE)
    pad_u, pad_v = pad
    metrics, flags = {}, []
    # Registration of the core against the native at native resolution.
    core_box = (pad_u * SCALE, pad_v * SCALE, pad_u * SCALE + target[0], pad_v * SCALE + target[1])
    core = extended[core_box[1]:core_box[3], core_box[0]:core_box[2]]
    reduced = np.asarray(Image.fromarray(core.astype(np.uint8)).resize((width, height), Image.LANCZOS)).astype(float)
    dx, dy = register(luma(native), luma(reduced))
    metrics['shift_native_px'] = [round(dx, 2), round(dy, 2)]
    if abs(dx) <= MAX_REGISTRATION_SHIFT * 2 and abs(dy) <= MAX_REGISTRATION_SHIFT * 2 and (dx or dy):
        # Small drift: move the crop by the measured offset (whole master pixels) inside the generated margins.
        ox = int(round(-dx * SCALE)) if pad_u else 0
        oy = int(round(-dy * SCALE)) if pad_v else 0
        ox = max(-core_box[0], min(ox, extended.shape[1] - core_box[2]))
        oy = max(-core_box[1], min(oy, extended.shape[0] - core_box[3]))
        core_box = (core_box[0] + ox, core_box[1] + oy, core_box[2] + ox, core_box[3] + oy)
        core = extended[core_box[1]:core_box[3], core_box[0]:core_box[2]]
        reduced = np.asarray(Image.fromarray(core.astype(np.uint8)).resize((width, height), Image.LANCZOS)).astype(float)
        residual = register(luma(native), luma(reduced))
        metrics['shift_after_crop'] = [round(residual[0], 2), round(residual[1], 2)]
        dx, dy = residual
    if max(abs(dx), abs(dy)) > MAX_REGISTRATION_SHIFT:
        flags.append(f'shift {dx:+.1f},{dy:+.1f}px')
    # Brightness/colour calibration: per-channel linear gain matching the shared target's opaque mean.
    opaque = native[..., 3] > 127 if native.shape[2] == 4 else np.ones(native.shape[:2], bool)
    # With copied master pixels, calibrate on the newly painted part only.
    region = opaque & ~fill if fill is not None and (opaque & ~fill).mean() >= 0.03 else opaque

    targets = target_means(entry, native, region)
    gains = []
    for channel in range(3):
        candidate_mean = srgb_to_linear(reduced[..., channel])[region].mean()
        gains.append(float(targets[channel] / max(candidate_mean, 1e-6)))
    metrics['gain'] = [round(g, 3) for g in gains]
    overall = float(np.dot(gains, [0.2126, 0.7152, 0.0722]))
    if not MIN_GAIN <= overall <= MAX_GAIN:
        flags.append(f'brightness {overall:.2f}')
    significant = [math.log(g) for channel, g in enumerate(gains)
                   if srgb_to_linear(native[..., channel])[region].mean() > 0.03]
    if significant and max(significant) - min(significant) > MAX_HUE_SPREAD:
        flags.append('colour ' + '/'.join(f'{g:.2f}' for g in gains))
    calibrated = extended.copy()
    for channel in range(3):
        calibrated[..., channel] = linear_to_srgb(srgb_to_linear(extended[..., channel]) * gains[channel])
    # Seamless wrap by minimum-error cuts through the generated margins.
    context_sides = set(entry.get('_context_sides') or ())
    for axis in entry['wrap']:
        if context_sides & ({'left', 'right'} if axis == 'u' else {'top', 'bottom'}):
            # These margins hold the neighbour's finished art, not this texture's own repeat: quilting them in
            # would paste the neighbour onto the opposite edge (MM8 gtempdor1). The crop stays exact.
            continue
        calibrated = quilt_wrap(calibrated, core_box, axis)
    master = calibrated[core_box[1]:core_box[3], core_box[0]:core_box[2]].copy()
    if fill is not None and fill.any():
        # Exact relative pixels wherever the natives are identical; the generated art keeps a one-native-pixel
        # band inside the shared area so its own edges meet the copied pixels.
        core4 = shared_core(fill)
        paste_shared(master, filled, core4, fill)
        metrics['prefilled'] = round(float(fill.mean()), 3)
    if entry['cutout'] and master.shape[2] == 4:
        native_alpha = np.asarray(Image.fromarray(native[..., 3].astype(np.uint8)).resize(target, Image.NEAREST))
        alpha_iou = float(((master[..., 3] > 127) & (native_alpha > 127)).sum()
                          / max(1, ((master[..., 3] > 127) | (native_alpha > 127)).sum()))
        metrics['alpha_iou'] = round(alpha_iou, 3)
        if alpha_iou < 0.9:
            flags.append(f'alpha {alpha_iou:.2f}')
    reduced = np.asarray(Image.fromarray(master.astype(np.uint8)).resize((width, height), Image.LANCZOS)).astype(float)
    boundary_metrics, boundary_flags = boundary_checks(master, native, entry['wrap'])
    metrics.update(boundary_metrics)
    flags += boundary_flags
    traced = traced_correlation(master, native)
    metrics['traced'] = round(traced, 3)
    if traced > MAX_TRACED:
        flags.append(f'traced {traced:.2f}')
    a = ndimage.gaussian_filter(luma(native), 1.5)[opaque]
    b = ndimage.gaussian_filter(luma(reduced), 1.5)[opaque]
    layout = float(np.corrcoef(a, b)[0, 1]) if a.std() > 1e-6 and b.std() > 1e-6 else 1.0
    metrics['layout_corr'] = round(layout, 3)
    if layout < MIN_LAYOUT_CORRELATION:
        flags.append(f'layout {layout:.2f}')
    mode = 'RGBA' if master.shape[2] == 4 else 'RGB'
    return Image.fromarray(np.clip(master + 0.5, 0, 255).astype(np.uint8), mode), metrics, flags


def cmd_check(args):
    job_dir = JOBS / args.job
    job = load_json(job_dir / 'job.json')
    textures = inventory()
    state = ledger_state()
    results = load_json(job_dir / 'results.json', {})
    events = []
    for member, request in job['requests'].items():
        spec = textures[member].get('assembly')
        if spec and spec['head'] != member:
            continue  # results come from the head's cut
        if state.get(member, {}).get('status', 'pending') == 'pending' or state[member].get('job') != args.job:
            continue  # released (it stays on ESRGAN until claimed again), or owned by a later job
        entry = generation_entry(member, textures)
        rotation = request.get('rotate_from')
        if rotation and state.get(member, {}).get('status') != 'accepted':
            # The native is an exact rotation of another texture's native: its master is the same rotation of that
            # texture's accepted master (whole master pixels, nothing generated).
            key = f"{request['name']}_r"
            source = state.get(rotation['id'], {})
            if source.get('status') == 'accepted' and (key not in results or args.force):
                native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
                master = cut_master(request, state, native)
                metrics, flags = boundary_checks(master[..., :3].astype(float), native, textures[member]['wrap'])
                metrics.update(rotated_from=rotation['id'], k=rotation['k'])
                path = job_dir / 'candidates' / f'{key}.png'
                Image.fromarray(master).save(path)
                results[key] = {'member': member, 'version': 1001, 'flags': flags, 'candidate': rel(path),
                                'metrics': metrics}
                events.append({'event': 'candidate', 'id': member, 'job': args.job, 'version': 1001,
                               'pass': not flags, 'flags': flags})
            continue
        copy = request.get('copy_from')
        if copy and state.get(member, {}).get('status') != 'accepted':
            # The native is a near-copy (re-dithered) of a window of another texture's native: its master is the same
            # window of that texture's accepted master, so the two can never disagree.
            key = f"{request['name']}_c"
            source = state.get(copy['id'], {})
            if source.get('status') == 'accepted' and (key not in results or args.force):
                native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
                master = cut_master(request, state, native)
                metrics, flags = boundary_checks(master[..., :3].astype(float), native, textures[member]['wrap'])
                metrics.update(copied_from=copy['id'], dx=copy['dx'], dy=copy['dy'], mirror=bool(copy.get('mirror')))
                path = job_dir / 'candidates' / f'{key}.png'
                Image.fromarray(master).save(path)
                results[key] = {'member': member, 'version': 1002, 'flags': flags, 'candidate': rel(path),
                                'metrics': metrics}
                events.append({'event': 'candidate', 'id': member, 'job': args.job, 'version': 1002,
                               'pass': not flags, 'flags': flags})
            continue
        if state.get(member, {}).get('status') != 'accepted' and not spec and not request.get('standalone'):
            fill, filled, used = prefill(entry, textures, state, request.get('prefill_from'))
            covered = coverage(entry, fill)
            key = f"{request['name']}_d"
            # Re-derive when a source was re-accepted since: the old cut would carry the replaced master's pixels.
            source_masters = [state[source]['master'] for source in used]
            stale = results.get(key, {}).get('metrics', {}).get('source_masters') != source_masters
            if derivable(entry, fill) and (key not in results or stale or args.force):
                # Entirely cut from accepted relatives: the master is their exact pixels, nothing is generated.
                missing = np.kron(~fill, np.ones((SCALE, SCALE), bool))
                if missing.any():
                    nearest = ndimage.distance_transform_edt(missing, return_distances=False, return_indices=True)
                    filled = filled[tuple(nearest)]
                mode = 'RGBA' if filled.shape[2] == 4 else 'RGB'
                path = job_dir / 'candidates' / f'{key}.png'
                Image.fromarray(np.clip(filled + 0.5, 0, 255).astype(np.uint8), mode).save(path)
                results[key] = {'member': member, 'version': 1000, 'flags': [], 'candidate': rel(path),
                                'metrics': {'derived_from': used, 'coverage': round(covered, 4),
                                            'source_masters': source_masters}}
                events.append({'event': 'candidate', 'id': member, 'job': args.job, 'version': 1000, 'pass': True,
                               'flags': []})
        for version in request['versions']:
            key = f"{request['name']}_v{version}"
            raw = job_dir / 'raw' / f'{key}.png'
            if not raw.exists() or (key in results and not args.force):
                continue
            sources = request.get('prefill', {}).get(str(version), {}).get('sources')
            fill = filled = None
            if sources:
                fill, filled, _ = prefill(entry, textures, state, sources)
            roll = (request.get('roll') or {}).get(str(version))
            built = version_entry(member, textures, request, version)
            if roll:
                fill, filled = roll_fill(fill, filled, roll)
            try:
                candidate, metrics, flags = build_candidate(built, raw, layout_for(built), fill, filled)
            except Exception as error:  # noqa: BLE001 - one broken return must not stop the job
                results[key] = {'member': member, 'version': version, 'flags': [f'error {error}'], 'metrics': {}}
                continue
            if roll:
                # Back to the texture's own frame; the boundary checks only mean something there.
                ox, oy = roll
                rolled_back = np.roll(np.asarray(candidate), (oy * SCALE, ox * SCALE), (0, 1))
                candidate = Image.fromarray(rolled_back, candidate.mode)
                native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
                metrics = {k: v for k, v in metrics.items() if not k.startswith(('seam_', 'edge_', 'rim_'))}
                flags = [flag for flag in flags if not flag.startswith(BOUNDARY_FLAGS)]
                boundary_metrics, boundary_flags = boundary_checks(rolled_back.astype(float), native, entry['wrap'])
                metrics.update(boundary_metrics, roll=list(roll))
                flags += boundary_flags
            pieces = [(member, candidate)]
            if spec:
                whole = np.asarray(candidate)
                candidate.save(job_dir / 'candidates' / f"{request['name']}_v{version}_assembly.png")
                pieces = [(piece, Image.fromarray(whole[y0:y1, x0:x1], candidate.mode))
                          for piece, x0, y0, x1, y1 in assembly_cuts(spec, textures)]
            if request.get('match_neighbor') and not spec and not roll:
                candidate = match_neighbor_gain(candidate, entry, textures, state, metrics, fill, filled)
            if request.get('joint_tone') and not spec and not roll:
                candidate = apply_joint_tone(candidate, entry, textures, state, fill, filled)
                metrics['joint_tone'] = True
            if not roll:
                context = neighbor_context(entry, textures, state)
                if context:
                    native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
                    master_pixels = np.asarray(candidate.convert('RGB')).astype(float)
                    for side, (ratio, native_ratio) in joint_ratios(master_pixels, native, context, textures).items():
                        metrics[f'joint_{side}'] = [round(ratio, 2), round(native_ratio, 2)]
                        if ratio > max(2.0, 1.5 * native_ratio):
                            flags.append(f'joint {side} {ratio:.1f} vs {native_ratio:.1f}')

            for piece, image in pieces:
                piece_name = textures[piece]['name']
                piece_key = f'{piece_name}_v{version}'
                path = job_dir / 'candidates' / f'{piece_key}.png'
                image.save(path)
                piece_metrics = dict(metrics)
                if spec:
                    piece_metrics['assembly'] = spec['head']
                results[piece_key] = {'member': piece, 'version': version, 'flags': flags,
                                      'metrics': piece_metrics, 'candidate': rel(path)}
                if state.get(piece, {}).get('status') != 'accepted':
                    events.append({'event': 'candidate', 'id': piece, 'job': args.job, 'version': version,
                                   'pass': not flags, 'flags': flags})
    write_json(job_dir / 'results.json', results)
    if events:
        ledger_append(events)
    review_sheets(job_dir, job, results, textures)
    review_page(job_dir, job, results, textures)
    retried = sorted({result['member'] for result in results.values() if result['version'] > 1
                      and state.get(result['member'], {}).get('status') != 'accepted'})
    if retried:
        review_sheets(job_dir, job, results, textures, {textures[member]['name'] for member in retried})
    passing = sum(1 for r in results.values() if not r['flags'])
    print(f'{len(results)} candidates, {passing} pass automatic checks')
    print('review:', rel(job_dir / 'review' / 'index.html'))
    for sheet in sorted((job_dir / 'review').glob('sheet_*.png')) + sorted((job_dir / 'review').glob('retry_*.png')):
        print('sheet :', rel(sheet))


def latest_results(job, results):
    latest = {}
    for key, result in results.items():
        member = result['member']
        if member not in latest or result['version'] > latest[member]['version']:
            latest[member] = {**result, 'key': key}
    return [latest[m] for m in job['textures'] if m in latest]


def review_sheets(job_dir, job, results, textures, names=None):
    """Compact sheets for the reviewing agent: native, ESRGAN x4, candidate, 1:1 crop, 2x2 repeat."""
    prefix = 'retry' if names else 'sheet'
    for old in (job_dir / 'review').glob(f'{prefix}_*.png'):
        old.unlink()
    rows = [row for row in latest_results(job, results) if not names or textures[row['member']]['name'] in names]
    cell = 256
    per_sheet = 6
    for page in range(0, len(rows), per_sheet):
        chunk = rows[page:page + per_sheet]
        sheet = Image.new('RGB', (cell * 5, len(chunk) * (cell + 16)), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for row, result in enumerate(chunk):
            entry = textures[result['member']]
            y = row * (cell + 16)
            tiles = [open_native(entry['world'], entry['name']).convert('RGB')]
            tiles.append(Image.open(ROOT / entry['esrgan_x4']).convert('RGB') if entry.get('esrgan_x4')
                         else Image.new('RGB', (8, 8)))
            if 'candidate' in result:
                candidate = Image.open(ROOT / result['candidate']).convert('RGB')
                tiles.append(candidate)
                cx, cy = candidate.width // 2, candidate.height // 2
                tiles.append(candidate.crop((cx - cell // 2, cy - cell // 2, cx + cell // 2, cy + cell // 2)))
                repeat = Image.new('RGB', (candidate.width * 2, candidate.height * 2))
                for dx in (0, 1):
                    for dy in (0, 1):
                        repeat.paste(candidate, (dx * candidate.width, dy * candidate.height))
                tiles.append(repeat)
            for column, tile in enumerate(tiles):
                view = tile if column == 3 else tile.copy()
                if column != 3:
                    view.thumbnail((cell, cell), Image.NEAREST if column == 0 else Image.LANCZOS)
                sheet.paste(view, (column * cell + (cell - view.width) // 2, y))
            label = f"{result['key']}  {' | '.join(result['flags']) or 'PASS'}  gain {result['metrics'].get('gain')}"
            draw.text((4, y + cell + 2), label, fill=(255, 120, 120) if result['flags'] else (160, 255, 160))
        sheet.save(job_dir / 'review' / f'{prefix}_{page // per_sheet + 1:02d}.png')


def review_page(job_dir, job, results, textures):
    def link(path):
        return os.path.relpath(ROOT / path, job_dir / 'review')
    rows = []
    for result in latest_results(job, results):
        entry = textures[result['member']]
        native = job_dir / 'review' / f"native_{entry['name']}.png"
        if not native.exists():
            image = open_native(entry['world'], entry['name']).convert('RGBA')
            image.resize((image.width * SCALE, image.height * SCALE), Image.NEAREST).save(native)
        images = [f'<figure><img src="{native.name}"><figcaption>native (nearest)</figcaption></figure>']
        if entry.get('esrgan_x4'):
            images.append(f'<figure><img src="{link(entry["esrgan_x4"])}"><figcaption>ESRGAN x4</figcaption></figure>')
        if 'candidate' in result:
            images.append(f'<figure><img src="{link(result["candidate"])}"><figcaption>{result["key"]}</figcaption>'
                          '</figure>')
            images.append(f'<figure><div class="rep" style="background-image:url({link(result["candidate"])})">'
                          '</div><figcaption>repeat</figcaption></figure>')
        status = ' | '.join(result['flags']) or 'pass'
        rows.append(f'<section><h2>{entry["name"]} <small>{entry["size"][0]}x{entry["size"][1]} wrap '
                    f'{entry["wrap"] or "-"} · {len(entry["maps"])} maps · {status}</small></h2>'
                    f'<div class="row">{"".join(images)}</div><pre>{json.dumps(result["metrics"])}</pre></section>')
    html = f"""<!doctype html><meta charset="utf-8"><title>{job['id']}</title>
<style>body{{background:#161616;color:#ddd;font:14px system-ui;margin:16px}}h2 small{{color:#999;font-weight:400}}
.row{{display:flex;gap:8px;flex-wrap:wrap}}figure{{margin:0}}img,.rep{{width:384px;height:384px;object-fit:contain;
image-rendering:auto;background:#000}}.rep{{background-size:50% 50%}}figcaption{{color:#aaa}}pre{{color:#8a8}}</style>
<h1>{job['id']} — {', '.join(job['maps'])}</h1>{''.join(rows)}"""
    (job_dir / 'review' / 'index.html').write_text(html)


# ----------------------------------------------------------------------------------- accept / reject

def cmd_accept(args):
    job_dir = JOBS / args.job
    job = load_json(job_dir / 'job.json')
    results = load_json(job_dir / 'results.json', {})
    textures = inventory()
    latest = {r['member']: r for r in latest_results(job, results)}
    picks = []
    if args.names:
        for spec in args.names:
            name, _, version = spec.partition('@v')
            member = next(m for m, r in job['requests'].items() if r['name'] == name)
            if version in ('d', '1000'):
                result = results[f'{name}_d']  # derived from accepted relatives
            elif version in ('r', '1001'):
                result = results[f'{name}_r']  # rotated from another accepted master
            elif version in ('c', '1002'):
                result = results[f'{name}_c']  # cut from a near-identical accepted master
            elif version:
                result = results[f'{name}_v{version}']
            else:
                result = latest[member]
            picks.append((member, result))
    else:
        state = ledger_state()
        picks = [(member, result) for member, result in latest.items()
                 if not result['flags'] and state.get(member, {}).get('status') != 'accepted']
    events = []
    for member, result in picks:
        if 'candidate' not in result:
            print('no candidate for', member)
            continue
        if any(flag.startswith('traced') for flag in result['flags']):
            # A traced master is an enlarged original, not new 4x art; this flag cannot be overridden.
            print(f'refused {member}: {result["flags"]}; retry it')
            continue
        entry = textures[member]
        target = MASTERS / entry['world'] / f"{entry['name']}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.stem + '.tmp.png')
        shutil.copyfile(ROOT / result['candidate'], temporary)
        os.replace(temporary, target)  # new inode: staged runs hard-link the previous master
        events.append({'event': 'accept', 'id': member, 'job': args.job, 'version': result['version'],
                       'master': rel(target), 'flags_overridden': result['flags']})
    ledger_append(events)
    print(f'accepted {len(events)}')


def cmd_reject(args):
    job = load_json(JOBS / args.job / 'job.json')
    member = next(m for m, r in job['requests'].items() if r['name'] == args.name)
    ledger_append([{'event': 'reject', 'id': member, 'job': args.job, 'reason': args.reason}])
    print('rejected', args.name, '- queue a retry with `tex.py retry` or release it')


def cmd_release(args):
    job = load_json(JOBS / args.job / 'job.json')
    state = ledger_state()
    members = [m for m, r in job['requests'].items() if not args.names or r['name'] in args.names]
    members = [m for m in members if state.get(m, {}).get('status') in ('claimed', 'candidate')]
    ledger_append([{'event': 'release', 'id': m, 'job': args.job} for m in members])
    print('released', len(members))


def cut_master(request, state, native):
    """The master of a texture whose native is a rotation or a re-dithered window of another accepted native."""
    rotation, copy = request.get('rotate_from'), request.get('copy_from')
    master = np.asarray(Image.open(ROOT / state[(rotation or copy)['id']]['master']))
    if rotation:
        return np.rot90(master, rotation['k']).copy()
    if copy.get('mirror'):
        master = master[:, ::-1]
    master = np.roll(master, (-copy['dy'] * SCALE, -copy['dx'] * SCALE), axis=(0, 1))
    return master[:native.shape[0] * SCALE, :native.shape[1] * SCALE].copy()


def accepted_sources(entry_id, state):
    """Relatives whose master pixels the accepted master copies (recorded when it was built)."""
    record = state.get(entry_id, {})
    job_dir = JOBS / str(record.get('job'))
    if not (job_dir / 'job.json').exists():
        return []
    if record.get('version') == 1000:
        result = (load_json(job_dir / 'results.json', {}) or {}).get(f"{entry_id.split('/')[1]}_d", {})
        return result.get('metrics', {}).get('derived_from', [])
    request = load_json(job_dir / 'job.json')['requests'].get(entry_id, {})
    if record.get('version') in (1001, 1002):
        return [(request.get('rotate_from') or request.get('copy_from'))['id']]
    return request.get('prefill', {}).get(str(record.get('version')), {}).get('sources', [])


def family_order(ids, state):
    """Sources before the masters that copy them."""
    ordered, seen = [], set()

    def visit(entry_id, stack=()):
        if entry_id in seen or entry_id in stack:
            return
        for source in accepted_sources(entry_id, state):
            if source in ids:
                visit(source, stack + (entry_id,))
        seen.add(entry_id)
        ordered.append(entry_id)

    for entry_id in sorted(ids):
        visit(entry_id)
    return ordered


def cmd_calibrate(args):
    """Set the shared brightness target and re-gain every accepted master to it (idempotent).

    Family pieces are re-gained on their own painted region only and then take the shared pixels again from
    their (already re-gained) sources, so identical native pixels stay identical master pixels."""
    if args.target:
        write_json(CONFIG, {**(load_json(CONFIG, {}) or {}), 'brightness': args.target})
    textures = inventory()
    state = ledger_state()
    ids = {entry_id for entry_id, record in state.items() if record.get('master') and entry_id in textures}
    changed = 0
    for entry_id in family_order(ids, state):
        entry = textures[entry_id]
        path = ROOT / state[entry_id]['master']
        image = Image.open(path)
        mode = image.mode if image.mode in ('RGB', 'RGBA') else 'RGB'
        master = np.asarray(image.convert(mode)).astype(float)
        original = master.copy()
        native = native_rgba(open_native(entry['world'], entry['name'])).astype(float)
        opaque = native[..., 3] > 127
        sources = accepted_sources(entry_id, state)
        fill = filled = None
        if sources:
            fill, filled, _ = prefill(entry, textures, state, sources)
        region = opaque & ~fill if fill is not None else opaque
        if region.mean() >= 0.03:
            size = (native.shape[1], native.shape[0])
            reduced = np.asarray(Image.fromarray(master.astype(np.uint8), mode).resize(size, Image.LANCZOS)).astype(float)
            targets = target_means(entry, native, region)
            gains = [targets[c] / max(float(srgb_to_linear(reduced[..., c])[region].mean()), 1e-6) for c in range(3)]
            if max(abs(g - 1) for g in gains) >= 0.02:  # Lanczos reduction drifts by ~1% per pass
                for channel in range(3):
                    master[..., channel] = linear_to_srgb(srgb_to_linear(master[..., channel]) * gains[channel])
        if fill is not None and fill.any():
            core4 = shared_core(fill)
            paste_shared(master, filled, core4, fill)
        if np.abs(master - original).max() < 1:
            continue
        # Write a new file and rename it: staged runs hard-link masters and must not change underneath.
        temporary = path.with_name(path.stem + '.tmp.png')
        Image.fromarray(np.clip(master + 0.5, 0, 255).astype(np.uint8), mode).save(temporary)
        os.replace(temporary, path)
        changed += 1
    print(f'brightness target {brightness_target()}; updated {changed} masters')


def cmd_rebuild(args):
    """Rebuild accepted family masters from their unchanged raw returns with the current recipe (no generation).

    Sources go first, so every piece copies the rebuilt pixels of its relatives; used after a change to how shared
    pixels are pasted (e.g. the smooth copy boundary that replaced native-pixel stair steps)."""
    textures = inventory()
    state = ledger_state()
    worlds = args.world or WORLDS
    ids = {entry_id for entry_id, record in state.items() if record.get('status') == 'accepted'
           and record.get('master') and entry_id in textures and textures[entry_id]['world'] in worlds}
    if args.only:
        ids = {entry_id for entry_id in ids if textures[entry_id]['name'] in args.only}
    rebuilt = 0
    for entry_id in family_order(ids, state):
        record = state[entry_id]
        version = record.get('version')
        sources = accepted_sources(entry_id, state)
        if not sources or version is None or textures[entry_id].get('assembly'):
            continue
        if version == 1000:
            # Derived pieces are pure copies of their relatives: copy the rebuilt pixels again.
            fill, filled, _ = prefill(textures[entry_id], textures, state, sources)
            missing = np.kron(~fill, np.ones((SCALE, SCALE), bool))
            if missing.any():
                nearest = ndimage.distance_transform_edt(missing, return_distances=False, return_indices=True)
                filled = filled[tuple(nearest)]
            mode = 'RGBA' if filled.shape[2] == 4 else 'RGB'
            path = ROOT / record['master']
            temporary = path.with_name(path.stem + '.tmp.png')
            Image.fromarray(np.clip(filled + 0.5, 0, 255).astype(np.uint8), mode).save(temporary)
            os.replace(temporary, path)
            rebuilt += 1
            continue
        job_dir = JOBS / record['job']
        request = load_json(job_dir / 'job.json')['requests'].get(entry_id)
        if version in (1001, 1002):
            native = native_rgba(open_native(textures[entry_id]['world'], textures[entry_id]['name']))
            path = ROOT / record['master']
            temporary = path.with_name(path.stem + '.tmp.png')
            Image.fromarray(cut_master(request, state, native)).save(temporary)
            os.replace(temporary, path)
            rebuilt += 1
            continue
        raw = job_dir / 'raw' / f"{textures[entry_id]['name']}_v{version}.png"
        if not request or not raw.exists():
            continue
        entry = generation_entry(entry_id, textures)
        fill, filled, _ = prefill(entry, textures, state, sources)
        roll = (request.get('roll') or {}).get(str(version))
        built = version_entry(entry_id, textures, request, version)
        if roll:
            fill, filled = roll_fill(fill, filled, roll)
        candidate, _, _ = build_candidate(built, raw, layout_for(built), fill, filled)
        if roll:
            ox, oy = roll
            candidate = Image.fromarray(np.roll(np.asarray(candidate), (oy * SCALE, ox * SCALE), (0, 1)), candidate.mode)
        elif request.get('match_neighbor'):
            candidate = match_neighbor_gain(candidate, entry, textures, state, {}, fill, filled)
        if request.get('joint_tone') and not roll:
            candidate = apply_joint_tone(candidate, entry, textures, state, fill, filled)
        path = ROOT / record['master']
        temporary = path.with_name(path.stem + '.tmp.png')
        candidate.save(temporary)
        os.replace(temporary, path)
        rebuilt += 1
    print(f'rebuilt {rebuilt} family masters')


def cmd_neighbors(args):
    """Refresh one world's neighbour links from its maps (T-junction aware), without a full inventory rebuild.

    Runs under the claim lock and only rewrites that world's `neighbors`; relatives, assemblies, materials and every
    other world stay as they are."""
    from map_export import parse_blv_file, parse_odm_file
    with open(HERE / '.claim.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = load_json(INVENTORY)
        textures = {entry['id']: entry for entry in data['textures']}
        abutments = {}
        for map_path in world_map_paths(args.world, (data.get('map_scope') or {}).get(args.world)):
            indoor = map_path.suffix == '.blv'
            payload = (parse_blv_file if indoor else parse_odm_file)(map_path)['payload']
            groups = ([(payload['vertices'], payload['faces'])] if indoor
                      else [(model['vertices'], model['faces']) for model in payload['bmodels']])
            for vertices, faces in groups:
                collect_abutments(vertices, faces, indoor, abutments)
        by_name = {entry['name']: entry for entry in textures.values() if entry['world'] == args.world}
        for name, entry in by_name.items():
            entry['abutments'] = abutments.get(name, [])
        before = {entry_id: len(entry.get('neighbors', [])) for entry_id, entry in textures.items()
                  if entry['world'] == args.world}
        links, good = continuous_links(textures, args.world, by_name)
        set_neighbors(textures, by_name, links, good, args.world)
        write_json(INVENTORY, data)
    after = sum(len(entry.get('neighbors', [])) for entry in by_name.values())
    print(f'{args.world}: {len(good)} continuous joints, neighbour links {sum(before.values())} -> {after}')


def cmd_joint_tone(args):
    """Apply the joint tone correction to accepted masters in place (write-and-rename) and record it on the request,
    so `check` and `rebuild` re-apply it. Afterwards rebuild the copiers (`accepted_sources`) of corrected masters."""
    textures = inventory()
    state = ledger_state()
    for name in args.names:
        member = f'{args.world}/{name}'
        record = state.get(member, {})
        if record.get('status') != 'accepted':
            print(f'{name}: not accepted, skipped')
            continue
        job_dir = JOBS / record['job']
        with job_lock(job_dir):
            job = load_json(job_dir / 'job.json')
            request = job['requests'].get(member)
            if request is None or request.get('joint_tone'):
                print(f'{name}: no request or already corrected, skipped')
                continue
            entry = textures[member]
            sources = accepted_sources(member, state)
            fill = filled = None
            if sources:
                fill, filled, _ = prefill(entry, textures, state, sources)
            path = ROOT / record['master']
            image = Image.open(path)
            corrected = apply_joint_tone(image.convert('RGBA' if image.mode == 'RGBA' else 'RGB'), entry, textures, state,
                                         fill, filled)
            temporary = path.with_name(path.stem + '.tmp.png')
            corrected.save(temporary)
            os.replace(temporary, path)
            request['joint_tone'] = True
            write_json(job_dir / 'job.json', job)
        print(f'{name}: joint tone corrected')


def cmd_alpha_from_native(args):
    """Accepted masters drawn opaque for natives with real alpha (MM9 32-bit BMPs read as RGB before 2026-11-01): the
    native alpha, enlarged to the master (Lanczos), becomes the master's alpha. Mostly binary natives (cut-out crowds,
    bars, chains, ladders) get a one-texel feather around the half level so the edge stays crisp at 4x; translucent
    natives (glass, ice, web, blood) and partial native levels keep their smooth values. The RGB of the accepted master is unchanged."""
    textures, state = inventory(), ledger_state()
    events = []
    for name in args.ids:
        entry_id = name if '/' in name else f'mm9/{name}'
        entry, record = textures[entry_id], state.get(entry_id, {})
        if record.get('status') != 'accepted' or not entry.get('cutout'):
            print(f'{entry_id}: skipped ({record.get("status")}, cutout={entry.get("cutout")})')
            continue
        native = native_rgba(open_native(entry['world'], entry['name']))[..., 3].astype(float)
        path = ROOT / record['master']
        master = Image.open(path)
        rgb = np.asarray(master.convert('RGB'))
        alpha = np.asarray(Image.fromarray(native.astype(np.uint8)).resize(master.size, Image.LANCZOS)).astype(float)
        semi = float(((native > 8) & (native < 247)).mean())
        if semi < 0.3:
            # Feather only where the native texel is fully clear or fully solid; partial native levels stay as they
            # are (the faint smoke of `refikpbanj`, 97 % clear, would otherwise vanish).
            nearest = np.asarray(Image.fromarray(native.astype(np.uint8)).resize(master.size, Image.NEAREST))
            hard = (nearest <= 8) | (nearest >= 247)
            alpha = np.where(hard, np.clip((alpha - 96) / 64, 0, 1) * 255, np.clip(alpha, 0, 255))
            # Near the silhouette, black the model painted as background (a figure a little narrower than the native
            # one) is cut away: dark master over a light native pixel within 12 master pixels of native transparency.
            from scipy import ndimage
            native_rgb = np.asarray(open_native(entry['world'], entry['name']).convert('RGB').resize(master.size,
                                                                                                   Image.NEAREST))
            near_edge = ndimage.binary_dilation(nearest < 128, iterations=12) & (nearest >= 128)
            background = near_edge & (rgb.max(axis=2) < 30) & (native_rgb.max(axis=2) > 45)
            background = ndimage.binary_opening(background, iterations=1)
            labels, count = ndimage.label(background)
            if count:
                sizes = ndimage.sum(background, labels, range(1, count + 1))
                # Strips of painted background, not the dark rim shading of chains and bars (scattered dots).
                background = np.isin(labels, 1 + np.flatnonzero(sizes >= 60))
            alpha = np.where(ndimage.binary_dilation(background, iterations=1), 0, alpha)
        alpha = np.clip(alpha + 0.5, 0, 255).astype(np.uint8)
        Image.fromarray(np.dstack([rgb, alpha]), 'RGBA').save(path)
        events.append({'event': 'alpha', 'id': entry_id, 'master': record['master'], 'source': 'native',
                       'mode': 'binary' if semi < 0.3 else 'smooth'})
        print(f'{entry_id}: {"binary" if semi < 0.3 else "smooth"} alpha, '
              f'{float((alpha < 128).mean()):.2f} transparent (native {float((native < 128).mean()):.2f})')
    ledger_append(events)


def cmd_verify_families(args):
    """Shared native pixels must be (nearly) identical master pixels between a master and its sources."""
    textures = inventory()
    state = ledger_state()
    checked = mismatched = 0
    for entry_id, record in sorted(state.items()):
        if not record.get('master') or entry_id not in textures:
            continue
        sources = accepted_sources(entry_id, state)
        if not sources:
            continue
        entry = textures[entry_id]
        fill, filled, _ = prefill(entry, textures, state, sources)
        core4 = shared_core(fill)
        if not core4.any():
            continue
        master = np.asarray(Image.open(ROOT / record['master']).convert('RGB')).astype(float)
        difference = float(np.abs(master[core4] - filled[core4, :3]).mean())
        checked += 1
        if difference > 1.0:
            mismatched += 1
            print(f'{entry_id}: shared pixels differ by {difference:.1f} from {sources}')
    print(f'{checked} family masters checked, {mismatched} mismatched')


def cmd_redo(args):
    """Reopen accepted textures for regeneration with the current recipe; old masters stay staged meanwhile."""
    textures = inventory()
    state = ledger_state()
    by_job = {}
    for entry_id, record in state.items():
        if record.get('status') != 'accepted' or entry_id not in textures:
            continue
        entry = textures[entry_id]
        if args.names and entry['name'] not in args.names:
            continue
        if args.world and entry['world'] not in args.world:
            continue
        if args.job and record.get('job') not in args.job:
            continue
        if args.families and not any(state.get(relation['id'], {}).get('status') == 'accepted'
                                     and priority(textures[relation['id']]) < priority(entry)
                                     for relation in family_relatives(entry)):
            continue
        if args.assemblies and not entry.get('assembly'):
            continue
        job_id = record.get('job')
        if not job_id or not (JOBS / job_id / 'job.json').exists():
            job_id = f"{datetime.now():%Y%m%d-%H%M}-{entry['world']}-redo"
        by_job.setdefault(job_id, []).append(entry_id)
    # Assembly pieces are regenerated together, in the head's job.
    for job_id in list(by_job):
        for entry_id in list(by_job[job_id]):
            spec = textures[entry_id].get('assembly')
            if not spec:
                continue
            for piece in spec['members']:
                if piece in by_job[job_id] or state.get(piece, {}).get('status') not in ('accepted', None, 'pending'):
                    continue
                for other in by_job.values():
                    if piece in other:
                        other.remove(piece)
                by_job[job_id].append(piece)
    by_job = {job_id: members for job_id, members in by_job.items() if members}
    if args.dry_run:
        for job_id, members in sorted(by_job.items()):
            print(job_id, len(members), ' '.join(textures[m]['name'] for m in members))
        return
    events = []
    for job_id, members in sorted(by_job.items()):
        if not (JOBS / job_id / 'job.json').exists():
            create_job(job_id, textures[members[0]]['world'], sorted({m for e in members for m in textures[e]['maps']}),
                       members, textures)
        job_dir = JOBS / job_id
        job = load_json(job_dir / 'job.json')
        for member in members:
            request = job['requests'].setdefault(member, {'name': textures[member]['name'], 'versions': [],
                                                          'material': textures[member].get('material', ''),
                                                          'notes': {}})
            if member not in job['textures']:
                job['textures'].append(member)
            accepted_version = str(state.get(member, {}).get('version') or max(request['versions'] or [0]))
            version = max(request['versions'] or [0]) + 1
            request['versions'].append(version)
            # Corrections that produced the accepted version carry forward.
            note = args.note or request['notes'].get(accepted_version, '')
            if note:
                request['notes'][str(version)] = note
            blur = request.get('ref_blur', {}).get(accepted_version)
            if blur is not None and blur > DEFAULT_REF_BLUR:
                request['ref_blur'][str(version)] = blur
            kind = 'reopen' if state.get(member, {}).get('status') == 'accepted' else 'claim'
            events.append({'event': kind, 'id': member, 'job': job_id, 'reason': args.reason})
        write_json(job_dir / 'job.json', job)
    ledger_append(events)
    print(f'reopened {len(events)} textures in {len(by_job)} jobs; run `tex.py gen`')


def cmd_import_codex_mm6(args):
    textures = inventory()
    state = ledger_state()
    source = ROOT / 'level_generation/terrain/mm6_textures_x4/exports_x4'
    events = []
    for path in sorted(source.glob('*.png')):
        member = f'mm6/{path.stem.lower()}'
        entry = textures.get(member)
        if not entry or entry.get('exclude') or state.get(member, {}).get('status') == 'accepted':
            continue
        if list(Image.open(path).size) != [entry['size'][0] * SCALE, entry['size'][1] * SCALE]:
            print('size mismatch, skipped', path.name)
            continue
        target = MASTERS / 'mm6' / path.name.lower()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        canonical = entry.get('canonical', member)
        events.append({'event': 'accept', 'id': canonical, 'master': rel(target), 'job': 'codex-mm6-x4-20261009',
                       'source': rel(path)})
        if canonical != member:
            print(f'{member} accepted through canonical {canonical}')
    ledger_append(events)
    print('imported', len(events))


# ------------------------------------------------------------------------------------------------ stage

def master_for(entry, textures, state):
    canonical = entry.get('canonical', entry['id'])
    record = state.get(canonical, {})
    # A reopened texture keeps its previous master in staged runs until a new one is accepted.
    if record.get('master'):
        return ROOT / record['master']
    return None


FRAME_TABLES = (ROOT / 'assets_dev/engine/data_tables/texture_frame_data.txt',
                REVIEW_ROOT / 'engine/data_tables/texture_frame_data.txt')
FRAME_NOISE = 6           # per-channel change against the first frame below which a texel is unchanged (DXT re-encoding)
MAX_FRAME_CHANGE = 0.10   # share of changed texels up to which a frame is a variant of the first (a glint), not new art


def frame_sequences():
    """The texture frame tables' animated sequences: lower-case frame names in order, the first frame first."""
    sequences = {}
    for table in FRAME_TABLES:
        if not table.exists():
            continue
        frames = None
        for line in table.read_text().splitlines()[1:]:
            fields = line.split('\t')
            if len(fields) < 5:
                continue
            flags = int(fields[4], 16)
            if flags & 0x2:
                frames = []
            if frames is None:
                continue
            frames.append(fields[0].lower())
            if not flags & 0x1:
                if len(frames) > 1:
                    sequences.setdefault(frames[0], frames)
                frames = None
    return list(sequences.values())


def frame_masters(world, heads):
    """{frame name: derived master} for the later frames of animated surfaces whose first frame has a master
    (`heads`, {name: master path}) and they do not: the head master plus each frame's own change against the first
    native frame, upscaled (MM9's Thjorad ore walls: one glint moving over an unchanged wall). Faces name only the
    first frame, so the inventory never sees the others; left at x1 they made the animation alternate between the x4
    head and the x1 frames, and the wall flickered (Thjorad Mine, 2026-11-08). A frame that redraws more than
    MAX_FRAME_CHANGE of the first is different art, not a variant: reported and left as it is. Written to
    masters/<world>/frames/ only when the bytes change, so the cook's staleness check stays quiet."""
    sources = NativeSources(world)
    derived = {}
    for frames in frame_sequences():
        head = heads.get(frames[0])
        if head is None:
            continue
        head_native = sources.image(frames[0])
        if head_native is None:
            print(f'{world}/{frames[0]}: animated head without a native; its frames stay x1', file=sys.stderr)
            continue
        base = native_rgba(head_native).astype(np.float32)
        master = None
        for name in frames[1:]:
            if name == frames[0] or name in heads or name in derived:
                continue
            native = sources.image(name)
            if native is None or native.size != head_native.size:
                print(f'{world}/{name}: frame of {frames[0]} without a native of its size; left x1', file=sys.stderr)
                continue
            change = native_rgba(native).astype(np.float32)[..., :3] - base[..., :3]
            changed = np.abs(change).max(axis=2) > FRAME_NOISE
            if changed.mean() > MAX_FRAME_CHANGE:
                print(f'{world}/{name}: redraws {changed.mean():.0%} of {frames[0]}, not a variant; left as it is',
                      file=sys.stderr)
                continue
            if master is None:
                image = Image.open(head)
                master = np.asarray(image.convert('RGBA' if 'A' in image.getbands() else 'RGB')).astype(np.float32)
            change[~changed] = 0
            size = (master.shape[1], master.shape[0])
            delta = np.stack([np.asarray(Image.fromarray(change[..., c]).resize(size, Image.BICUBIC))
                              for c in range(3)], axis=2)
            frame = master.copy()
            frame[..., :3] = np.clip(master[..., :3] + delta, 0, 255)
            buffer = io.BytesIO()
            Image.fromarray(np.round(frame).astype(np.uint8)).save(buffer, format='PNG')
            target = MASTERS / world / 'frames' / f'{name}.png'
            if not (target.exists() and target.read_bytes() == buffer.getvalue()):
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + '.tmp')
                temporary.write_bytes(buffer.getvalue())
                os.replace(temporary, target)
            derived[name] = target
    return derived


def tier_plan(world, tier, baseline, textures, state):
    """{file name: (source path, scale)} for one world's textures_<tier> folder (scale 1: link the source as is,
    otherwise resize it by that factor), with counts by kind. Accepted masters where they exist; at x4 ESRGAN for the
    rest, then a 2x carrier of the x2 file."""
    x2_dir = ROOT / 'assets_source/worlds' / world / 'textures_x2'
    by_name = {(entry['world'], entry['name']): entry for entry in textures.values()}
    plan, counts = {}, {'master': 0, 'esrgan_x4': 0, 'x2_carrier': 0, 'x2': 0}
    for source in sorted(x2_dir.glob('*.png')):
        name = source.stem.lower()
        entry = by_name.get((world, name))
        master = master_for(entry, textures, state) if entry else None
        if master and not baseline:
            plan[source.name] = (master, 1 if tier == 'x4' else 0.5)
            counts['master'] += 1
        elif tier == 'x4' and esrgan_x4(world, name):
            plan[source.name] = (esrgan_x4(world, name), 1)
            counts['esrgan_x4'] += 1
        elif tier == 'x4':
            plan[source.name] = (source, 2)
            counts['x2_carrier'] += 1
        else:
            plan[source.name] = (source, 1)
            counts['x2'] += 1
    # Face textures without a textures_x2 file: terrain tiles that also cover faces (`also_terrain`; the face lookup
    # finds them in the textures tier before its terrain fallback) and the names excluded from generation (sky
    # ceilings, water, lava). At x4 every face texture of the world gets a file, so no face falls back to x1.
    staged = {path.stem.lower() for path in x2_dir.glob('*.png')}
    for entry in textures.values():
        if entry['world'] != world or entry['name'] in staged or entry.get('base_of'):
            continue  # periodic bases have no faces
        master = master_for(entry, textures, state)
        if master and not baseline:
            plan[f"{entry['name']}.png"] = (master, 1 if tier == 'x4' else 0.5)
            counts['master'] += 1
        elif tier == 'x4' and esrgan_x4(world, entry['name']):
            plan[f"{entry['name']}.png"] = (esrgan_x4(world, entry['name']), 1)
            counts['esrgan_x4'] += 1
        elif tier == 'x4' and entry.get('native'):
            plan[f"{entry['name']}.png"] = (ROOT / entry['native'], 'nearest4')
            counts['x1_carrier'] = counts.get('x1_carrier', 0) + 1
    # The later frames of an animated surface follow their first frame's master (see frame_masters).
    if not baseline:
        heads = {Path(name).stem.lower(): Path(source) for name, (source, scale) in plan.items()
                 if Path(source).resolve().is_relative_to(MASTERS.resolve())}
        for name, master in frame_masters(world, heads).items():
            plan[f'{name}.png'] = (master, 1 if tier == 'x4' else 0.5)
            counts['frame'] = counts.get('frame', 0) + 1
    return plan, counts


def place_tier_file(source, scale, target):
    """Hard-link (no data duplication) or write a resized copy; never writes through an existing link."""
    temporary = target.with_name(target.name + '.tmp')
    temporary.unlink(missing_ok=True)
    if scale == 1:
        os.link(source, temporary)
    elif scale == 'nearest4':
        # An original with no generated or ESRGAN art: its texels repeated, keeping the native look and the magenta key.
        image = Image.open(source).convert('RGBA' if Image.open(source).mode in ('RGBA', 'P') else 'RGB')
        image.resize((image.width * 4, image.height * 4), Image.NEAREST).save(temporary, format='PNG')
    else:
        image = Image.open(source)
        image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS).save(temporary,
                                                                                                    format='PNG')
    os.replace(temporary, target)


def cmd_stage(args):
    textures = inventory()
    state = ledger_state()
    run_root = RUNS / args.run
    assets = run_root / 'assets_dev'
    if run_root.exists():
        if not (run_root / 'run.json').exists():
            sys.exit(f'{run_root} exists and is not a textures_x4 run; refusing to delete it')
        shutil.rmtree(run_root)
    run_root.mkdir(parents=True)
    # Hard links: no data duplication. New tier directories below are replaced, never written through.
    subprocess.run(['cp', '-al', str(ROOT / 'assets_dev'), str(assets)], check=True)
    receipt = {'run': args.run, 'tier': args.tier, 'created': now(), 'worlds': {}}
    for world in WORLDS:
        tier_dir = assets / 'worlds' / world / f'textures_{args.tier}'
        if tier_dir.exists():
            shutil.rmtree(tier_dir)
        tier_dir.mkdir(parents=True)
        plan, counts = tier_plan(world, args.tier, args.baseline, textures, state)
        for name, (source, scale) in plan.items():
            place_tier_file(source, scale, tier_dir / name)
        # Images the runtime reads as images (the blood splat) stay in the assets_dev tier folders.
        for kept in (ROOT / 'assets_dev/worlds' / world / f'textures_{args.tier}').glob('*.png'):
            if kept.name not in plan:
                os.link(kept, tier_dir / kept.name)
        receipt['worlds'][world] = counts
        print(world, counts)
    write_json(run_root / 'run.json', receipt)
    print('staged', rel(assets))
    print(f'play: python3 {rel(Path(__file__))} play {args.run} --world mm6 --map 6d01.blv')


def cmd_install(args):
    """The accepted masters as the game's textures_<tier> sources in assets_source (the stage's rules), synced in
    place: unchanged files stay, so the build's surface cook (tools/cook_surface_textures.py, into assets_dev) only
    redoes what changed."""
    textures = inventory()
    state = ledger_state()
    for world in args.world or WORLDS:
        if world in WORLD_CONTENT:
            install_review_root(world, textures, state)
            continue
        tier_dir = ROOT / 'assets_source/worlds' / world / f'textures_{args.tier}'
        tier_dir.mkdir(parents=True, exist_ok=True)
        plan, counts = tier_plan(world, args.tier, False, textures, state)
        changed = 0
        for name, (source, scale) in plan.items():
            target = tier_dir / name
            if scale == 1 and target.exists() and os.path.samefile(source, target):
                continue
            if scale != 1 and target.exists() and target.stat().st_mtime_ns >= Path(source).stat().st_mtime_ns:
                continue
            place_tier_file(source, scale, target)
            changed += 1
        removed = 0
        for path in tier_dir.iterdir():
            if path.suffix.lower() in ('.png', '.bmp') and path.name not in plan:
                path.unlink()
                removed += 1
        print(world, counts, f'{changed} written, {removed} removed')
    if set(args.world or WORLDS) - set(WORLD_CONTENT):
        print('installed; build openyamm (or run tools/cook_surface_textures.py) to cook them, '
              f'then set [video_quality] texture={args.tier}')


INSTALL_WORK = HERE / 'install'  # per-world cook inputs/outputs of review-root installs (masters hard-linked)


def install_review_root(world, textures, state):
    """A review-root world's tiers, mirroring the MM6-MM8 runtime layout inside that root only: the accepted masters
    cooked to BC7 `.oytex` in worlds/<w>/textures_x4 (the desktop cook's exact job settings), and the x2 reduction as
    PNG in worlds/<w>/textures_x2. Written through review_root.install() (temporary file, then rename), never through
    a hard link to assets_dev. Textures without an accepted master get no file and keep drawing their x1 native."""
    sys.path.insert(0, str(ROOT / 'tools'))
    sys.path.insert(0, str(ROOT / 'level_generation/projects/mm9r_common'))
    import cook_surface_textures as cook
    import review_root
    cooker = ROOT / 'build/game/openyamm_model_texture_cook'
    if not cooker.is_file():
        sys.exit(f'missing {rel(cooker)}: cmake --build build --target openyamm_model_texture_cook')
    plan, counts = tier_plan(world, 'x4', False, textures, state)
    masters = {Path(name).stem: Path(source) for name, (source, scale) in plan.items() if scale == 1
               and Path(source).resolve().is_relative_to(MASTERS.resolve())}
    work = INSTALL_WORK / world
    jobs = []
    for stem, master in sorted(masters.items()):
        source = work / 'sources' / f'{stem}.png'
        source.parent.mkdir(parents=True, exist_ok=True)
        if not (source.exists() and os.path.samefile(source, master)):
            source.unlink(missing_ok=True)
            os.link(master, source)
        target = work / 'cooked' / f'{stem}.oytex'
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            continue
        jobs.append('\t'.join((str(source), str(target), 'bc7', *cook.job_settings(cook.FULL_SIZE),
                               cook.sha256(source)[:16], 'surface')) + '\n')
    if jobs:
        job_file = work / 'jobs.tsv'
        job_file.write_text(''.join(jobs))
        result = subprocess.run([str(cooker), str(job_file)], text=True, capture_output=True)
        cooked = sum(line.startswith('cooked\t') for line in result.stdout.splitlines())
        if cooked != len(jobs):
            sys.exit(f'{world}: cooked {cooked} of {len(jobs)}\n{result.stderr}')
    written = removed = 0
    for tier, wanted in (('x4', {f'{stem}.oytex' for stem in masters}), ('x2', {f'{stem}.png' for stem in masters})):
        relative_dir = Path('worlds') / world / f'textures_{tier}'
        for stem, master in sorted(masters.items()):
            if tier == 'x4':
                data = (work / 'cooked' / f'{stem}.oytex').read_bytes()
                name = f'{stem}.oytex'
            else:
                data, name = x2_reduction(master), f'{stem}.png'
            target = review_root.mirror_path(relative_dir / name)
            if target.exists() and target.read_bytes() == data:
                continue
            review_root.install(relative_dir / name, data)
            written += 1
        directory = review_root.mirror_path(relative_dir)
        for path in sorted(directory.iterdir()) if directory.is_dir() else []:
            # Opaque variants (`<first seven>opq`) belong to mm9r_common/opaque_textures.py, not to a master.
            if (path.name not in wanted and path.suffix.lower() in ('.oytex', '.png')
                    and not path.stem.endswith('opq')):
                review_root.remove(relative_dir / path.name)
                removed += 1
    print(world, f'{len(masters)} masters -> {rel(review_root.ASSETS)}/worlds/{world}/textures_x4 (BC7) and '
          f'textures_x2 (PNG); {written} written, {removed} removed')
    sync_world_sources(world, masters)


def x2_reduction(master):
    """The x2 tier of a review-root world's master: its Lanczos half as PNG bytes."""
    image = Image.open(master)
    buffer = io.BytesIO()
    image.resize((image.width // 2, image.height // 2), Image.LANCZOS).save(buffer, format='PNG')
    return buffer.getvalue()


def sync_world_sources(world, masters):
    """A review-root world's tier sources in assets_source, as for MM6-MM8: textures_x4/<stem>.png hard-linked to the
    accepted master and textures_x2/<stem>.png its x2 reduction (the bytes the review roots get). The build's surface
    cook (tools/cook_surface_textures.py) cooks the x4 sources into assets_dev, so the game no longer depends on the
    review roots' promotion for them. Opaque variants (`<first seven>opq`, mm9r_common/opaque_textures.py) are written
    by that script and kept here."""
    changed = removed = 0
    for tier in ('x4', 'x2'):
        tier_dir = ROOT / 'assets_source/worlds' / world / f'textures_{tier}'
        tier_dir.mkdir(parents=True, exist_ok=True)
        for stem, master in sorted(masters.items()):
            target = tier_dir / f'{stem}.png'
            if tier == 'x4':
                if target.exists() and os.path.samefile(master, target):
                    continue
                place_tier_file(master, 1, target)
            else:
                data = x2_reduction(master)
                if target.exists() and target.read_bytes() == data:
                    continue
                temporary = target.with_name(target.name + '.tmp')
                temporary.write_bytes(data)
                os.replace(temporary, target)
            changed += 1
        for path in sorted(tier_dir.iterdir()):
            if path.suffix.lower() == '.png' and path.stem not in masters and not path.stem.endswith('opq'):
                path.unlink()
                removed += 1
    print(world, f'{len(masters)} masters -> assets_source/worlds/{world}/textures_x4 and textures_x2 (PNG sources); '
          f'{changed} written, {removed} removed; cook: tools/cook_surface_textures.py --world {world}')


def cmd_play(args):
    run_root = RUNS / args.run
    receipt = load_json(run_root / 'run.json')
    if not receipt:
        sys.exit('unknown run; stage it first')
    command = [str(ROOT / 'tools/run_game.sh'), '--isolated', f'tex-{args.run}', '--world', args.world,
               '--map', args.map, '--assets', str(run_root / 'assets_dev'),
               '--set', f"video_quality.texture={receipt['tier']}", '--seconds', str(args.seconds)]
    command += sum((['--set', value] for value in args.set), [])
    print(' '.join(command))
    if not args.print_only:
        os.execv(command[0], command)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inventory')
    p.add_argument('--world', action='append', choices=WORLDS, help='rebuild only these worlds (others are kept)')
    p.add_argument('--map', action='append', help='add a map to a scoped world\'s map_scope (MM9: anskramkeep.blv)')
    sub.add_parser('status')
    p = sub.add_parser('next')
    p.add_argument('--count', type=int, required=True)
    p.add_argument('--world', action='append', choices=WORLDS)
    p.add_argument('--map', action='append', help='map filename(s), e.g. 6d01.blv')
    p.add_argument('--indoor-first', action='store_true')
    p.add_argument('--names', nargs='+', help='claim only these textures (ids or names) and what they bring along')
    p.add_argument('--dry-run', action='store_true')
    p = sub.add_parser('gen')
    p.add_argument('jobs', nargs='*', help='default: every job with claimed or candidate textures')
    p.add_argument('--parallel', type=int, default=10)
    p.add_argument('--world', action='append', choices=WORLDS, help='serve only these worlds\' jobs')
    p.add_argument('--follow', action='store_true', help='keep polling while open jobs remain (runs until stopped)')
    p.add_argument('--only', nargs='*')
    p = sub.add_parser('materials')
    p.add_argument('job')
    p = sub.add_parser('retry')
    p.add_argument('job')
    p.add_argument('name')
    p.add_argument('--note', default='')
    p.add_argument('--material')
    p.add_argument('--drop-context', action='store_true',
                   help='with --roll: roll an axis that has neighbours anyway; their margins are dropped for that '
                        'version (a free edge on the other side keeps painting a rim)')
    p.add_argument('--match-neighbor', action='store_true',
                   help='match the colour along continuous joints to the accepted neighbours (sticks to the texture)')
    p.add_argument('--standalone', action='store_true',
                   help='generate from the own native only, without copying accepted relatives (sticks to the texture)')
    p.add_argument('--ref-blur', type=float, help='native-pixel blur of the reference (default 1.2); larger values '
                   'keep only colour and large shapes, for random speckle materials')
    p.add_argument('--rotate-from', metavar='NAME:K', help='the native is NAME rotated by K quarter turns '
                   '(np.rot90): cut the master from NAME\'s accepted master instead of generating')
    p.add_argument('--copy-from', metavar='NAME:DX[:DY]', help='the native is a re-dithered copy of NAME\'s native '
                   'shifted by DX,DY native pixels: cut the master from NAME\'s accepted master instead of generating')
    p.add_argument('--prefill-from', metavar='NAME[,NAME]', help='copy shared pixels (or derive) only from these '
                   'accepted relatives, e.g. when another relative draws a joint inside the shared region (sticks)')
    p.add_argument('--mirror', action='store_true', help='with --copy-from: NAME is mirrored left to right first')
    p.add_argument('--roll', choices=['u', 'v', 'uv'], help='generate rolled along these axes so the texture edges '
                   'sit inside the picture (fixes rims the model paints on the tile boundary)')
    p = sub.add_parser('check')
    p.add_argument('job')
    p.add_argument('--force', action='store_true')
    p = sub.add_parser('accept')
    p.add_argument('job')
    p.add_argument('names', nargs='*')
    p = sub.add_parser('reject')
    p.add_argument('job')
    p.add_argument('name')
    p.add_argument('--reason', required=True)
    p = sub.add_parser('release')
    p.add_argument('job')
    p.add_argument('names', nargs='*')
    sub.add_parser('import-codex-mm6')
    p = sub.add_parser('calibrate')
    p.add_argument('--target', choices=['native', 'esrgan'])
    sub.add_parser('verify-families')
    p = sub.add_parser('alpha-from-native')
    p.add_argument('ids', nargs='+')
    p = sub.add_parser('joint-tone')
    p.add_argument('names', nargs='+')
    p.add_argument('--world', required=True, choices=WORLDS)
    p = sub.add_parser('neighbors')
    p.add_argument('--world', required=True, choices=WORLDS)
    p = sub.add_parser('rebuild')
    p.add_argument('--world', action='append', choices=WORLDS)
    p.add_argument('--only', nargs='+', help='rebuild only these texture names (family order is kept)')
    p = sub.add_parser('redo')
    p.add_argument('names', nargs='*')
    p.add_argument('--job', action='append')
    p.add_argument('--world', action='append', choices=WORLDS)
    p.add_argument('--note', default='')
    p.add_argument('--reason', required=True)
    p.add_argument('--assemblies', action='store_true', help='only pieces of detected assemblies')
    p.add_argument('--families', action='store_true',
                   help='only pieces with an accepted higher-priority relative: rebuild them on its exact pixels')
    p.add_argument('--dry-run', action='store_true')
    p = sub.add_parser('stage')
    p.add_argument('run')
    p.add_argument('--tier', choices=['x4', 'x2'], default='x4')
    p.add_argument('--baseline', action='store_true', help='stage ESRGAN only, for before/after comparisons')
    p = sub.add_parser('install')
    p.add_argument('--tier', choices=['x4'], default='x4')
    p.add_argument('--world', action='append', choices=WORLDS)
    p = sub.add_parser('play')
    p.add_argument('run')
    p.add_argument('--world', required=True)
    p.add_argument('--map', required=True)
    p.add_argument('--seconds', type=int, default=0)
    p.add_argument('--set', action='append', default=[])
    p.add_argument('--print-only', action='store_true')
    args = parser.parse_args()
    globals()['cmd_' + args.command.replace('-', '_')](args)


if __name__ == '__main__':
    main()
