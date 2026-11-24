"""The classic Clouds town kit: Clouds of Xeen's own half-timbered town walls on the houses of a Cloudside map, in
place of MM7's Harmondale half-timber kits (the user's choice of 2026-11-24, after a Discord request for the original
building textures; variant A of level_generation/xeen_art/kit_textures/vertigo_classic, composed so every bay meets
every other: compose.py there).

Every part of a building whose kit (its own, else its building's, else the MM7 default `plaster`) is one of MM7's
half-timber kits (plaster, timber, grey, rich, poor) takes the kit's textures by role. A part that names a wall of
its own (a wreck's planks, a pagoda, a machine of gongs) stays as its generator made it: the kit's bays carry their
own timber frame and would not fit its wall. A door or window the part names itself stays too, except MM7's carved
double-door wings (the Vertigo Town Hall's 7hhr1d1), which become the kit's wing of the original's double door. Its
roof, when it is one of the MM7 half-timber roofs or not named, becomes shingle, or thatch where the house had thatch
(the poor kit, hhp2rf): the original's town well and straw hut. The gable is the wall itself, so the posts and beams
run on up the gable end. The building gets the stone footing `base: cwb1` (as X1's plaster houses had, merge point
16): the bays are storey modules, and the base course falls back to the wall, which would show one and a half
storeys of timber up a wall of one.

Roof edges (the user, 2026-11-24: "the roof outlines deserve some more work"): a box part's gable roof runs on
VERGE past each gable end with a barge board under its edge (Map Studio `verge`; the board in the kit's beam), and
its gable or hip roof reaches EAVES out over the walls, where the part names neither itself. Each gable end and each
side on its own: where a wing, a shed or a tower of the same building stands against it as high as the roof, that end
stays flush (`verge_walls` names the free one) or the part keeps no eaves; a part standing wholly inside the
footprint (a chimney) does not count.

The stone buildings (2026-11-24, after the Vertigo pilot): a part of a district plot (the towns' temples, guilds,
banks, stone farmhouses; not the out-of-town structures) built of MM7's `stone` kit (chb1 fieldstone, the hhm1d door)
takes the classic stone kit, Clouds of Xeen's castle walls (fcstl1/fcstl2: sandstone slabs between courses of dressed
blocks, quoins at the corners, the arched iron-banded door), with the same roof edges, shingle roofs, oak trim and
footing. Textures xvswall, xvswin, xvsdoor, xvscornl, xvscornr (kit royal_castle).

The tower kit (2026-11-24): the dark places (the evil towers, Castle Blackfang, Necropolis) in Clouds of Xeen's
tower walls (ftowr1/ftowr2: big dark blocks, the plank door with its iron ring), dark slate roofs (xtslate). Textures
xvtwall, xvtwin, xvtdoor (kit towers).

Which building takes which kit beyond the rules above, and the rules for Darkside's towns (MM8 stand-ins named at the
building level), are data: classic_kit.yml beside this file. apply(sketch, key) with the map key (x1 ... d6).

Textures (assets_dev/worlds/xeen/textures_x4, registered in source/textures.yml, family cloudside_town):
xvwall, xvwin, xvdoor, xvdoorw, xvcornl, xvcornr, xvbeam, xvridge, xvshgl, xvthat.
"""
import os

import yaml

CONFIG = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'classic_kit.yml')))

KIT = {'wall': 'xvwall', 'window': 'xvwin', 'door': 'xvdoor', 'post_left': 'xvcornl', 'post_right': 'xvcornr',
       'trim': 'xvbeam', 'gable': 'xvwall', 'ridge': 'xvridge'}
STONE_KIT = {'wall': 'xvswall', 'window': 'xvswin', 'door': 'xvsdoor', 'post_left': 'xvscornl',
             'post_right': 'xvscornr', 'trim': 'xvbeam', 'gable': 'xvswall', 'ridge': 'xvridge'}
TOWER_KIT = {'wall': 'xvtwall', 'window': 'xvtwin', 'door': 'xvtdoor', 'post_left': 'xvtwall',
             'post_right': 'xvtwall', 'trim': 'xvbeam', 'gable': 'xvtwall', 'ridge': 'xvridge'}
KITS = {'house': KIT, 'stone': STONE_KIT, 'tower': TOWER_KIT}
# A two-leaf door (`door: {leaves: 2}`) hangs its picture on each leaf, the second mirrored: each kit's wing of the
# original's double door, not its door bay (whose frame and wall would show twice, with a gap between: the user,
# 2026-11-24, on Necropolis).
WINGS = {'house': 'xvdoorw', 'stone': 'xvsdoorw', 'tower': 'xvtdoorw'}
SHINGLE, THATCH, SLATE = 'xvshgl', 'xvthat', 'xtslate'
HALF_TIMBER_KITS = {'plaster', 'timber', 'grey', 'rich', 'poor'}
HALF_TIMBER_ROOFS = {'hhm1rf', 'hhm2rf', 'hhm3rf', 'hhp2rf', '7hhr1rf'}
DEFAULT_KIT = 'plaster'    # MM7's first kit: what a part of a building that names none is built of
OWN_ROLES = ('wall', 'door', 'window')
# MM7's double-door wings on a kit house: one wing of the original's double door (the second leaf hangs it mirrored)
DOOR_WINGS = {'7hhr1d1': 'xvdoorw', '7hhr1d2': 'xvdoorw'}
STOREY = 256           # a kit bay's height: the studio lays walls in rows of it
FOOTING = 'cwb1'
VERGE = 40                 # how far a gable's slopes run past its ends (map units); the barge board is 24 high
EAVES = 24                 # how far a gable's or hip's roof reaches out over the walls
WALL_HEIGHT = 256          # Map Studio's part defaults
ROOF_ROOM = 512            # how high a roof may stand over its walls, for the overlap test
DEFAULT_ROOF = 'gable'     # MM7's ordinary house roof


def _extent(part):
    """A part's footprint (x0, y0, x1, y1) in its plot's map units and its height range (z0, z1), or None."""
    bottom = part.get('bottom', 0)
    top = bottom + part.get('wall_height', WALL_HEIGHT) + (0 if part.get('roof') == 'none' else ROOF_ROOM)
    if part.get('shape') == 'round' and 'radius' in part:
        cx, cy = part.get('at', [0, 0])
        r = part['radius']
        return (cx - r, cy - r, cx + r, cy + r), (bottom, top)
    if part.get('shape', 'box') == 'box' and 'size' in part:
        x, y = part.get('at', [0, 0])
        return (x, y, x + part['size'][0], y + part['size'][1]), (bottom, top)
    return None


def _blocked(part, others, strip):
    """True when a strip next to the part (x0, y0, x1, y1) meets another part of its building that stands as high as
    the part's roof (a part standing wholly inside the part's own footprint, a chimney, does not count)."""
    own = _extent(part)
    (px0, py0, px1, py1), _ = own
    foot = part.get('bottom', 0) + part.get('wall_height', WALL_HEIGHT)
    sx0, sy0, sx1, sy1 = strip
    for other in others:
        extent = _extent(other)
        if extent is None:
            return True
        (ox0, oy0, ox1, oy1), (oz0, oz1) = extent
        if oz1 <= foot or oz0 >= foot + ROOF_ROOM:
            continue
        if px0 <= ox0 and ox1 <= px1 and py0 <= oy0 and oy1 <= py1:
            continue
        if ox0 < sx1 and ox1 > sx0 and oy0 < sy1 and oy1 > sy0:
            return True
    return False


def _roof_edges(building, part, parts):
    """The eaves and the verge on a box part's gable or hip roof where it names none: the eaves where both eaves
    sides are free (all four sides on a hip), the verge at each gable end that is free; what it did."""
    roof = part.get('roof') or building.get('roof') or DEFAULT_ROOF
    if part.get('shape', 'box') != 'box' or roof not in ('gable', 'hip') or 'eaves_walls' in part or 'posts' in part \
            or 'eaves_walls' in building or _extent(part) is None:
        return ''
    others = [other for other in parts if other is not part]
    (x0, y0, x1, y1), _ = _extent(part)
    along = part.get('ridge_along') or building.get('ridge_along')
    # Map Studio: the ridge runs along the box's first side (east-west) when it is the longer, or as `ridge_along` says.
    east_west = along == 'ew' or (along != 'ns' and (x1 - x0) >= (y1 - y0))
    strips = {'s': (x0, y1, x1, y1 + EAVES), 'n': (x0, y0 - EAVES, x1, y0),
              'w': (x0 - EAVES, y0, x0, y1), 'e': (x1, y0, x1 + EAVES, y1)}
    sides = ('s', 'n') if east_west else ('w', 'e')
    if roof == 'hip':
        sides = ('s', 'n', 'w', 'e')
    done = ''
    eaves = 0
    if 'eaves' not in part and 'eaves' not in building \
            and not any(_blocked(part, others, strips[side]) for side in sides):
        part['eaves'] = eaves = EAVES
        done += 'e'
    elif isinstance(part.get('eaves', building.get('eaves')), (int, float)):
        eaves = part.get('eaves', building.get('eaves'))
    if roof != 'gable' or any(key in part or key in building for key in ('verge', 'half_hip')):
        return done
    # The gable ends: beyond each, a strip as deep as the verge and as wide as the roof with its eaves.
    if east_west:
        ends = {'w': (x0 - VERGE, y0 - eaves, x0, y1 + eaves), 'e': (x1, y0 - eaves, x1 + VERGE, y1 + eaves)}
    else:
        ends = {'n': (x0 - eaves, y0 - VERGE, x1 + eaves, y0), 's': (x0 - eaves, y1, x1 + eaves, y1 + VERGE)}
    free = [wall for wall, strip in ends.items() if not _blocked(part, others, strip)]
    if free:
        part['verge'] = VERGE
        if len(free) < 2:
            part['verge_walls'] = free
        done += 'v'
    return done


PEN = {'sill': 'xvbeam', 'post': 'xvbeam', 'trim': 'xvbeam'}
OFFICE = 512               # the stables office along its door wall (four bays: the door and the sign)
GAP = 4                    # between a stables' parts, so no two faces lie in one plane


def stables(plot):
    """A stables plot rebuilt as MM8's stables are (Ravenshore's, Shadowspire's): the door part's footprint becomes a
    small closed office on the door wall (the door, the sign) and beside it an open pen on posts with a low plank
    fence and a roof; the plot's `shed` becomes a fenced paddock without a roof. True when it rebuilt the plot."""
    door = plot.get('door') if isinstance(plot.get('door'), dict) else None
    parts = plot.get('parts') or []
    body = next((p for p in parts if door and p.get('id') == door.get('part')), None)
    if body is None or 'size' not in body or door.get('wall') not in ('n', 's', 'e', 'w'):
        return False
    (x, y), (w, h) = body.get('at', [0, 0]), body['size']
    wall = door['wall']
    along_x = wall in ('n', 's')
    length, depth = (w, h) if along_x else (h, w)
    office_long = min(OFFICE, length // 2)
    office_deep = min(OFFICE, depth)
    keep = {k: v for k, v in body.items() if k not in ('id', 'at', 'size', 'walls', 'upper_walls', 'verge',
                                                         'verge_walls', 'ridge_along', 'eaves')}
    # The pen stands GAP clear of the office (no face of its posts in the office's wall) and has no fence on that
    # side, which is the office's wall.
    if along_x:
        oy = y if wall == 'n' else y + h - office_deep
        office = dict(keep, id='office', at=[x, oy], size=[office_long, office_deep])
        pen = {'at': [x + office_long + GAP, y], 'size': [w - office_long - GAP, h], 'ridge_along': 'ew',
               'sill_walls': ['s', 'e', 'n']}
    else:
        ox = x if wall == 'w' else x + w - office_deep
        office = dict(keep, id='office', at=[ox, y], size=[office_deep, office_long])
        pen = {'at': [x, y + office_long + GAP], 'size': [w, h - office_long - GAP], 'ridge_along': 'ns',
               'sill_walls': ['s', 'e', 'w']}
    office.setdefault('roof', 'gable')
    pen.update({'id': 'pen', 'posts': 24, 'post_every': 256, 'sill': 96, 'wall_height': 256, 'windows': 'none',
                'roof': 'gable', 'roof_pitch': 30, 'textures': dict(PEN, roof=SHINGLE)})
    rebuilt = [office, pen]
    for part in parts:
        if part is body:
            continue
        if part.get('id') == 'shed' and 'size' in part:
            # The old lean-to shed behind: a fenced paddock open to the sky, trimmed to start GAP clear of the pen,
            # its fence open on the pen's side (the horses walk out).
            (sx, sy), (sw, sh) = part.get('at', [0, 0]), part['size']
            sx1, sy1 = sx + sw, sy + sh
            if sx >= x + w - sw:                      # beyond the east wall
                sx, side = max(sx, x + w + GAP), 'w'
            elif sx1 <= x + sw:                       # beyond the west wall
                sx1, side = min(sx1, x - GAP), 'e'
            elif sy >= y + h - sh:                    # beyond the south wall
                sy, side = max(sy, y + h + GAP), 'n'
            else:                                     # beyond the north wall
                sy1, side = min(sy1, y - GAP), 's'
            part = {'id': 'shed', 'at': [sx, sy], 'size': [sx1 - sx, sy1 - sy], 'posts': 16, 'post_every': 256,
                    'sill': 112, 'sill_walls': [wall_ for wall_ in 'senw' if wall_ != side], 'wall_height': 144,
                    'windows': 'none', 'roof': 'none', 'textures': dict(PEN)}
        rebuilt.append(part)
    plot['parts'] = rebuilt
    door['part'] = 'office'
    return True


def _wall(textures):
    wall = (textures or {}).get('wall')
    return wall.get('texture') if isinstance(wall, dict) else wall


def _rule(key, building, is_plot):
    """The kit a building takes and how: {'kit': house | stone | tower | default, 'walls': [...]} or None."""
    names = CONFIG.get('buildings', {}).get(key) or {}
    entry = names.get(building.get('title')) or names.get(building.get('id')) or names.get(building.get('building'))
    if entry:
        return entry if isinstance(entry, dict) else {'kit': entry}
    wall = _wall(building.get('textures'))
    if not wall:
        return {'kit': 'default'}
    if not is_plot or wall in CONFIG['leave_walls']:
        return None
    town = (CONFIG.get('towns') or {}).get(key)
    if town:
        return {'kit': town}
    civic = any(word in (building.get('building') or '') for word in CONFIG['civic_words'])
    return {'kit': 'stone' if civic else 'house'}


def _fit(building, part, own, is_plot, counts):
    """The kits' bays are one storey (256) high pictures, and the studio lays walls in rows of 256 from the foot, a
    top row that is lower showing the lower part of its panels (`oymap audit`'s textures.feature_repeated and
    feature_cut, 2026-11-24): a window or a corner quoin then shows one and a part, the posts end in stubs under the
    roof. A district house's walls are a whole number of storeys (the nearest, a half storey up); a ruin, a wall lower
    than a storey and a structure's walls of any other height show the kit's wall in place of its windows and posts."""
    height = float(part.get('wall_height', building.get('wall_height', STOREY)))
    ruin = part.get('ruin') or building.get('ruin')
    if not ruin and height % STOREY == 0:
        return
    if not ruin and is_plot and height > STOREY:
        part['wall_height'] = max(STOREY, int(height / STOREY + 0.5) * STOREY)
        counts['storeys'] = counts.get('storeys', 0) + 1
        return
    for role in ('window', 'post_left', 'post_right'):
        if role in own:
            own[role] = own['wall']
    counts['plain'] = counts.get('plain', 0) + 1


def apply(sketch, key=None):
    """Put the classic kits on the sketch's buildings (district plots and building structures), as the rules and
    classic_kit.yml say for map `key`."""
    plots = [plot for district in sketch.get('districts') or [] for plot in district.get('plots') or []]
    buildings = [(s, False) for s in sketch.get('structures') or [] if s.get('kind') == 'building']
    buildings += [(plot, True) for plot in plots]
    counts = {'buildings': 0, 'parts': 0, 'house': 0, 'stone': 0, 'tower': 0, 'shingle': 0, 'thatch': 0,
              'verges': 0, 'eaves': 0}
    special = set(CONFIG['special_walls'])
    for plot in plots if key in (CONFIG.get('stables_maps') or []) else []:
        if any(word in (plot.get('building') or '') for word in CONFIG['stables_words']) and stables(plot):
            counts['stables'] = counts.get('stables', 0) + 1
    for building, is_plot in buildings:
        rule = _rule(key, building, is_plot)
        if rule is None:
            continue
        building_wall = _wall(building.get('textures'))
        changed = False
        for part in building.get('parts') or []:
            kit = part.get('kit') or building.get('kit') or DEFAULT_KIT
            own = dict(part.get('textures') or {})
            own_wall = _wall(own)
            if rule['kit'] == 'default':
                name = 'house' if kit in HALF_TIMBER_KITS else 'stone' if kit == 'stone' and is_plot else None
                if name is None or (own_wall and own_wall not in KITS[name].values()):
                    continue
            else:
                name = rule['kit']
                if own_wall in special or (rule.get('walls') and (own_wall or building_wall) not in rule['walls']):
                    continue
            textures = KITS[name]
            if own.get('door') in DOOR_WINGS:
                own['door'] = DOOR_WINGS[own['door']]
            for role, texture in textures.items():
                # A door or window of the part's own stays on the kits' houses (the town hall's double door).
                if rule['kit'] == 'default' and role in own and role in OWN_ROLES and role != 'wall':
                    continue
                # A special door (a portcullis over a castle's wide gateway) stays on every kit: the kits' doors are one
                # 128 bay, tiled over a wider doorway (D1's Kalindra gate, doors.tiled, 2026-11-24)
                if role == 'door' and (own.get('door') or (building.get('textures') or {}).get('door')) \
                        in (CONFIG.get('keep_doors') or []):
                    own['door'] = own.get('door') or building['textures']['door']
                    continue
                own[role] = texture
            door = building.get('door') if isinstance(building.get('door'), dict) else {}
            if door.get('leaves') == 2 and door.get('part') == part.get('id'):
                own['door'] = WINGS[name]
            roof = own.get('roof') or (building.get('textures') or {}).get('roof')
            if roof is None or roof in HALF_TIMBER_ROOFS:
                if name == 'tower':
                    own['roof'] = SLATE
                else:
                    thatch = name == 'house' and (kit == 'poor' or roof == 'hhp2rf')
                    own['roof'] = THATCH if thatch else SHINGLE
                    counts['thatch' if thatch else 'shingle'] += 1
            if key in (CONFIG.get('fit_maps') or []):
                _fit(building, part, own, is_plot, counts)
            part['textures'] = own
            counts[name] += 1
            counts['parts'] += 1
            changed = True
            edges = _roof_edges(building, part, building.get('parts') or [])
            counts['verges'] += 'v' in edges
            counts['eaves'] += 'e' in edges
        if changed:
            if rule['kit'] != 'tower':
                building.setdefault('textures', {}).setdefault('base', FOOTING)
            counts['buildings'] += 1
    return ['classic kit: %(buildings)d buildings, %(parts)d parts (house %(house)d, stone %(stone)d, tower %(tower)d; '
            '%(shingle)d shingle roofs, %(thatch)d thatch), %(verges)d verges, %(eaves)d eaves, %(stables)d stables, '
            '%(storeys)d heights in whole storeys, %(plain)d parts without windows or posts'
            % dict(counts, stables=counts.get('stables', 0), storeys=counts.get('storeys', 0),
                   plain=counts.get('plain', 0))]
