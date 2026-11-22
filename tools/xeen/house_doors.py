"""House doors for the Xeen outdoor generators (F2, 2026-11-21; A6's kits): a door is one leaf with a single door's
picture, or a double door of two leaves.

The shipped house kits the Xeen towns are built of hang wings (one half of a double door) as their door picture:
MM7's rich 7hhr1d2, MM8's t06a03/t06b03 (Ravenshore's boulder houses), t09a03a (Regna's ashlar), t07b03c (Alvar's
adobe). The shipped maps always hang them in pairs; one alone shows half a door beside blank wall (Vertigo Town Hall,
the user 2026-11-21). `double_doors(plot)` turns every such door of a plot into a double door: `leaves: 2` on a bay
256 wide in the middle of the door's wall (each leaf 128, the wing's own width; the second leaf mirrored), the left
wing as the picture, the wall's other bays listed round it (and the rows above with a window over each leaf).

A generator calls it on each plot it writes; `tools/xeen/door_check.py` checks the built map.
"""

# A wing and its left twin (the picture the first leaf shows; the second leaf shows it mirrored).
LEFT_WING = {
    '7hhr1d1': '7hhr1d1', '7hhr1d2': '7hhr1d1',
    't06a03': 't06a03', 't06b03': 't06a03', 't06c03': 't06c03', 't06d03': 't06c03',
    't07a03c': 't07a03c', 't07a03d': 't07a03c', 't07b03c': 't07b03c', 't07b03d': 't07b03c',
    't07c03c': 't07c03c', 't07c03d': 't07c03c', 't09a03a': 't09a03a', 't09a03b': 't09a03a',
    'chb1dl': 'chb1dl', 'chb1dr': 'chb1dl', 'hkm1dl': 'hkm1dl', 'hkm1dr': 'hkm1dl',
}
# The studio's kit doors (openyamm-studio/core/OutdoorBuildings.cpp kits(), MM7 style for Xeen).
KIT_DOOR = {'plaster': 'hhm2d', 'timber': 'hhm1d', 'grey': 'hhm3d', 'poor': 'hhp1d', 'rich': '7hhr1d2',
            'stone': 'hhm1d', 'castle': 'hhm1d'}
KIT_POSTS = {'plaster', 'timber', 'grey', 'poor', 'rich', 'stone'}
PAIR = 256


def _door_texture(plot, part):
    for source in (part.get('textures') or {}, plot.get('textures') or {}):
        if 'door' in source:
            value = source['door']
            return value.get('texture') if isinstance(value, dict) else value
    return KIT_DOOR.get(part.get('kit', plot.get('kit', '')), '')


def _wall_length(plot, part, wall, extent):
    if part.get('shape', 'box') != 'box':
        return None
    size = part.get('size') or list(extent)
    return size[0] if wall in ('n', 's') else size[1]


def _side(length, posts, windows, left):
    """The bays of one side of the door, [role, width] from the wall's end to the door: bays of 128 (the panels'
    own width, so no picture is stretched or repeated), a window next to the door and every second bay out from it
    (as the studio lays a wall round its door), the post at the end, what is left over a plain wall piece by the
    door."""
    if length < 16:
        return None
    count = int(length // 128)
    rest = length - count * 128
    roles = []
    for index in range(count):
        role = 'window' if index % 2 == 0 and windows else 'wall'
        if index == count - 1 and posts and count >= 2:
            role = 'post_left' if left else 'post_right'
        roles.append([role, 128])
    if rest >= 16 or not roles:
        roles.insert(0, ['wall', round(rest if roles else length, 3)])
    elif rest > 0:
        plain = next((r for r in roles if r[0] == 'wall'), roles[0])
        plain[1] = round(plain[1] + rest, 3)
    return list(reversed(roles)) if left else roles


def double_doors(plot, extent):
    """Make the plot's wing doors double doors. `extent`: the plot's [width, depth] in map units (the size of a part
    that names none). Returns a list of notes (empty when nothing changed); raises ValueError where a wing door
    cannot be made a pair (a round part, a wall too short, a listed wall without a 256 door bay)."""
    notes = []
    doors = []
    if plot.get('door') not in (None, 'none'):
        doors.append(plot['door'])
    doors += plot.get('doors') or []
    parts = plot.get('parts') or []
    for door in doors:
        if not isinstance(door, dict) or 'same_event_as' in door:
            continue
        name = door.get('part')
        part = next((p for p in parts if p.get('id') == name), parts[0] if parts else None)
        if part is None:
            continue
        texture = _door_texture(plot, part)
        left = LEFT_WING.get(str(texture).lower())
        if not left:
            continue
        wall = door.get('wall', plot.get('facing', 's'))
        walls = part.setdefault('walls', {})
        if wall in walls:
            if not any(isinstance(b, list) and b[0] == 'door' and b[1] >= PAIR for b in walls[wall]):
                raise ValueError('%s: the listed wall %s has no door bay %d wide' % (plot.get('building'), wall, PAIR))
        else:
            length = _wall_length(plot, part, wall, extent)
            if length is None:
                raise ValueError('%s: a wing door on a part that is no box' % plot.get('building'))
            side = (length - PAIR) / 2.0
            kit = part.get('kit', plot.get('kit', ''))
            textures = dict(plot.get('textures') or {})
            textures.update(part.get('textures') or {})
            posts = ('post_left' in textures and 'post_right' in textures) or kit in KIT_POSTS
            windows = part.get('windows', 'alternate') != 'none'
            lefts, rights = _side(side, posts, windows, True), _side(side, posts, windows, False)
            if lefts is None:
                raise ValueError('%s: the door wall is %s long, too short for a double door' % (plot.get('building'),
                                                                                                 length))
            walls[wall] = lefts + [['door', PAIR]] + rights
            upper = part.setdefault('upper_walls', {})
            listed = [b if isinstance(b, str) else b[0] for b in upper.get(wall) or []]
            if listed and len(set(listed)) == 1:
                # the rows above listed in one plain texture (Sandcaster's t07a01 over the t07b01 band): its bays on
                # the edges of the row below, so no piece of the lower row reaches up through them
                upper[wall] = [[listed[0], b[1]] for b in lefts] + [[listed[0], PAIR]] + [[listed[0], b[1]] for b in rights]
            elif wall not in upper:
                # as the studio does over a door: a window (one, over the middle of the pair) where the kit has one
                upper[wall] = lefts + [['wall', 64], ['window', 128], ['wall', 64]] + rights
        door['leaves'] = 2
        if left != str(texture).lower():
            part.setdefault('textures', {})['door'] = left
        notes.append('%s#%s: %s -> double door %s (wall %s)' % (plot.get('building'), plot.get('index', ''), texture,
                                                               left, wall))
    return notes


def double_doors_sketch(sketch):
    """double_doors() on every plot of the sketch's districts and every `building` structure; the notes."""
    notes = []
    for district in sketch.get('districts') or []:
        for plot in district.get('plots') or []:
            notes += double_doors(plot, None)
    for structure in sketch.get('structures') or []:
        if structure.get('kind') == 'building':
            notes += double_doors(structure, None)
    return notes


# ---- Cave mouths (F8, 2026-11-21) ----------------------------------------------------------------------------------
# The studio's cave mouth is a shell as wide as its footprint (1024 when not given) round a mouth of 448-512: the shell
# between the mouth's rim and the footprint's sides stands as two rock wings beside the arch, and the land under the
# footprint's side edges is set to the floor, so no hill hides them (Mount Firestone, the user 2026-11-21). A mouth
# into a hillside is only its rim: the footprint as wide as the mouth and a rim of 64, so the hill beside it (the
# nodes outside the footprint) covers the shell's sides. A barrow on level land (`free: true`) stays a mound.
# A mouth that leads nowhere (no `into`: Sablewing's cave, the orc pickets' den, the werewolves' den, the fallen adit)
# says so when clicked (its dark mouth stays: a rock back a short way in read as a solid lump).
DARK = {'7solid01', 'solid01', 'solid10'}
RIM = 64


def _mouth_numbers(structure):
    mouth = structure.get('mouth') or {}
    door = mouth.get('form', 'arch') == 'door'
    return mouth, door, mouth.get('width', 192 if door else 512), mouth.get('rim', 128 if door else 72)


def bury_mouths_sketch(sketch):
    notes = []
    for structure in sketch.get('structures') or []:
        if structure.get('kind') != 'cave_mouth' or structure.get('free'):
            continue
        mouth, door, width, rim = _mouth_numbers(structure)
        size = list(structure.get('size') or [1024, 1024])
        if size[0] <= width + 2 * min(rim, RIM) + 0.5:
            continue
        rim = min(rim, RIM)
        structure['size'] = [width + 2 * rim, size[1]]
        structure.setdefault('mouth', {})['rim'] = rim
        notes.append('%s: footprint %s -> %s wide (mouth %s, rim %s)' % (structure.get('id'), size[0], width + 2 * rim,
                                                                       width, rim))
    return notes


def blind_mouths_sketch(sketch):
    """A mouth with no `into` says so when clicked: the dark mouth stays (a rock back read as a solid lump, F8's
    preview), the click tells the player the cave ends a few paces in."""
    notes = []
    for structure in sketch.get('structures') or []:
        if structure.get('kind') != 'cave_mouth' or structure.get('into') or structure.get('effects') \
                or structure.get('lua') or structure.get('lua_before'):
            continue
        structure['effects'] = [{'text': 'The cave ends a few paces in, in bare rock. There is no way on.'}]
        notes.append('%s: no way in, says so when clicked' % structure.get('id'))
    return notes


def check_sketch(sketch):
    """The cave-mouth and door rules a sketch can show before a build: errors as lines."""
    errors = []
    for structure in sketch.get('structures') or []:
        if structure.get('kind') != 'cave_mouth':
            continue
        mouth, door, width, rim = _mouth_numbers(structure)
        size = structure.get('size') or [1024, 1024]
        if not structure.get('free') and size[0] > width + 2 * rim + 0.5:
            errors.append('error caves.wings: %s is %s wide round a mouth of %s with a rim of %s: the shell beside the '
                          'rim stands as rock wings; a mouth into a hill is as wide as its rim' % (structure.get('id'),
                                                                                                 size[0], width, rim))
        if not any(structure.get(key) for key in ('into', 'effects', 'lua', 'lua_before')):
            errors.append('error caves.blind_mouth: %s shows a dark way in, leads nowhere and says nothing when '
                          'clicked: give it `into` or a line' % structure.get('id'))
    return errors
