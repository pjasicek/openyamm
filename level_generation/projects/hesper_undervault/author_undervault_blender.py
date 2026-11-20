"""Author the Undervault (hes_undervault.blv) in Blender, with its houses built into the walls.

Run headless:  blender --background --factory-startup --python author_undervault_blender.py
The rooms, links, markers and lights are the lh plan of design/kreegan_world/zone1/dungeons/make_dungeon_plans.py and
the heights UNDERVAULT.md and its sections give; this script adds the walls, the vault, the shop bays and façades (each
house front one fitted picture cut round a recessed door, its sign plaque on a little box above), the galleries with
their parapets and stairs, the stairs of the Chapel and the Deep Stair, the fountain, the pillars and the
decorations. Textures are the Hesper sets in design/kreegan_world/art (4x masters; native = 1/4).

Writes source/hes_undervault.glb, hes_undervault.geometry.yml, hes_undervault.semantic.json and hes_undervault.blend.
"""
import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path('/home/pjasicek/github/OpenYAMM')
PROJECT = ROOT / 'level_generation/projects/hesper_undervault'
OUTPUT = PROJECT / 'source'
OUTPUT.mkdir(exist_ok=True)
SCALE = 128
spec = importlib.util.spec_from_file_location('make_dungeon_plans',
                                              ROOT / 'design/kreegan_world/zone1/dungeons/make_dungeon_plans.py')
plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plans)
PLAN = plans.lh
HALL_W, HALL_D = plans.HALL_W, plans.HALL_D
BAYS, HOME_DOORS = plans.BAYS, plans.HOME_DOORS
DECORATION_IDS = json.loads((ROOT / 'output/hesper_stage/decoration_ids.json').read_text())

# --- Materials --------------------------------------------------------------------------------------------------------
ART = ROOT / 'design/kreegan_world/art'
FOLDERS = [ART / 'textures_d0/blv', ART / 'textures_interiors/masters', ART / 'textures_out1/masters',
           ART / 'textures_k3_transit/masters']                 # K3: the Deep Stair bulkhead (CR-P3-03)
ROLE = {
    'wall': 'hcpanel', 'patch': 'hcpatch', 'trim': 'hctrim', 'girder': 'hcgirder', 'floor': 'hcfloor',
    'plank': 'hfplank', 'ceiling': 'hcceiling', 'scrap': 'hfscrap', 'pillar': 'hcpillar', 'rail': 'hfrail',
    'marble': 'hamarble', 'well': 'hawell', 'water': 'hawater', 'strip': 'hcstripw', 'rug': 'hfrug',
    'door_shop': 'hfdoorsh', 'door_home': 'hfdoorhm', 'door_home2': 'hfdoorhm2', 'door_double': 'hfdoordb',
    'door_shack': 'hfdoorsk', 'cage': 'hhcage', 'hatch': 'hcdoor', 'bulkhead': 'htbulk', 'marker': 'hcconsole',
    'works_wall': 'hiwall', 'pipe': 'hipipe', 'valve': 'hivalve', 'recess': 'hcrecess', 'cloth': 'hfcloth',
    'stall': 'hccounter', 'gold': 'hogold', 'awning': 'hfawning', 'banner_red': 'hfbanrd', 'banner_blue': 'hfbanbl',
}
FRONTS = {'Salvage & Arms': ('hfrarms', 'hfsignarms'), 'Emitters': ('hfremit', 'hfsignemit'),
          'Provisions': ('hfrprov', 'hfsignprov'), 'The Clinic': ('hfrclin', 'hfsignclin'),
          'The Last Lamp (inn)': ('hfrlamp', 'hfsignlamp'), 'Bounty board': ('hfrbnty', 'hfboard'),
          'Sim Hall': ('hfrsim', 'hfsignsim'), 'Workshop': ('hfrwork', 'hfsignwork'),
          'Council Hall': ('hfrcncl', 'hfsigncncl'), 'Archive': ('hfrarch', 'hfsignarch')}
# A role's texture repeat over its native size, for the great hall's scale (the vault, its floor and big panels).
ROLE_SCALE = {'ceiling': 3.0, 'wall': 2.0, 'patch': 1.5, 'floor': 2.0, 'plank': 1.5, 'pillar': 1.5, 'marble': 1.5}
for front, sign in FRONTS.values():
    ROLE[front] = front
    ROLE[sign] = sign


def texture_path(key):
    for folder in FOLDERS:
        if (folder / f'{key}.png').exists():
            return folder / f'{key}.png'
    raise FileNotFoundError(key)


for scene_object in list(bpy.data.objects):
    bpy.data.objects.remove(scene_object, do_unlink=True)
scene = bpy.context.scene
scene.name = 'Undervault authoring'
scene['levelgen_project'] = 'hesper_undervault'
metadata = {'format_version': 2, 'kind': 'indoor_geometry', 'map_file': 'hes_undervault.blv',
            'source': {'authoring_file': 'hes_undervault.blend', 'asset_path': 'hes_undervault.glb',
                       'coordinate_system': 'blender_z_up', 'unit_scale': SCALE,
                       'import': {'source_format': 'glb', 'reserve_sector_zero': True, 'merge_coplanar_faces': False,
                                  'generate_bsp': True, 'generate_outlines': True}},
            'materials': [], 'rooms': [], 'portals': [], 'surfaces': [], 'mechanisms': [], 'entities': [],
            'lights': [], 'spawns': []}
materials, dimensions, palette = {}, {}, []
for key in sorted(set(ROLE.values())):
    image = bpy.data.images.load(str(texture_path(key)), check_existing=True)
    image.pack()
    material = bpy.data.materials.new('LH_' + key)
    material.use_nodes = True
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    node.interpolation = 'Closest'
    material.node_tree.links.new(node.outputs['Color'],
                                 material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    native = (image.size[0] // 4, image.size[1] // 4)
    materials[key], dimensions[key] = material, native
    palette.append(key)
    metadata['materials'].append({'id': key, 'source_material': material.name, 'texture': key,
                                  'texture_width': native[0], 'texture_height': native[1]})


# --- Faces ------------------------------------------------------------------------------------------------------------
class Fit:
    """A fitted texture: the picture spans one rectangle of a wall (origin, right and up in world units), so the
    pieces cut round a door share it."""
    def __init__(self, origin, right, up, width, height):
        self.origin, self.right, self.up = Vector(origin), Vector(right), Vector(up)
        self.width, self.height = width, height


def mesh(name, panels, kind, **properties):
    """panels: (coords, role, inward[, Fit]). UVs: one texel per world unit on the face's dominant plane, or fitted."""
    vertices, polygons, uvs, keys = [], [], [], []
    for panel in panels:
        coords, role, inward = panel[:3]
        fit = panel[3] if len(panel) > 3 else None
        key = ROLE[role]
        points = []
        for p in coords:                       # a corner given twice (the vault meeting the springing) is one corner
            if not points or (Vector(p) - points[-1]).length > 0.5:
                points.append(Vector(p))
        if len(points) > 1 and (points[0] - points[-1]).length <= 0.5:
            points.pop()
        if len(points) < 3:
            continue
        normal = (points[1] - points[0]).cross(points[2] - points[0])
        if normal.length < .001:
            continue
        if normal.dot(Vector(inward)) < 0:
            points.reverse()
        offset = len(vertices)
        vertices.extend(tuple(p / SCALE) for p in points)
        polygons.append(tuple(range(offset, len(vertices))))
        if fit:
            uvs.extend(((p - fit.origin).dot(fit.right) / fit.width, (p - fit.origin).dot(fit.up) / fit.height)
                       for p in points)
        else:
            drop = max(range(3), key=lambda i: abs(normal[i]))
            tangents = [i for i in range(3) if i != drop]
            width, height = (d * ROLE_SCALE.get(role, 1.0) for d in dimensions[key])
            uvs.extend((p[tangents[0]] / width, p[tangents[1]] / height) for p in points)
        keys.append(key)
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], polygons)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj['levelgen_kind'] = kind
    for key, value in properties.items():
        obj[key] = value
    for key in palette:
        data.materials.append(materials[key])
    for polygon, key in zip(data.polygons, keys):
        polygon.material_index = palette.index(key)
    layer = data.uv_layers.new()
    for loop, uv in zip(layer.data, uvs):
        loop.uv = uv
    return obj


class Wall:
    """A vertical wall plane: x = plane (axis 'x') or y = plane (axis 'y'), facing `inward` into its room. Points are
    (along, z); `right` is the direction a viewer facing the wall sees as right."""
    def __init__(self, axis, plane, inward):
        self.axis, self.plane, self.inward = axis, plane, inward
        n = Vector(inward)
        self.right = (-n).cross(Vector((0, 0, 1)))

    def point(self, along, z, out=0.0):
        n = Vector(self.inward)
        if self.axis == 'x':
            return Vector((self.plane, along, z)) + n * out
        return Vector((along, self.plane, z)) + n * out

    def quad(self, a0, a1, z0, z1, role, fit=None, out=0.0):
        if a1 - a0 < 0.5 or z1 - z0 < 0.5:
            return []
        coords = [self.point(a0, z0, out), self.point(a1, z0, out), self.point(a1, z1, out), self.point(a0, z1, out)]
        return [(coords, role, self.inward, fit)] if fit else [(coords, role, self.inward)]

    def fit(self, a0, a1, z0, z1, out=0.0):
        """A Fit over the rectangle from a0 to a1, z0 to z1 (u left to right as the viewer sees it)."""
        left = a0 if self.right.dot(self.axis_vector()) > 0 else a1
        return Fit(self.point(left, z0, out), self.right, (0, 0, 1), abs(a1 - a0), z1 - z0)

    def axis_vector(self):
        return Vector((0, 1, 0)) if self.axis == 'x' else Vector((1, 0, 0))


def rect_minus(a0, a1, z0, z1, holes):
    """The rectangle minus holes (a0, a1, z0, z1), as rectangles: cut at every hole edge along the wall, then the free
    heights of each strip."""
    cuts = sorted({a0, a1} | {v for h in holes for v in (h[0], h[1]) if a0 < v < a1})
    pieces = []
    for s0, s1 in zip(cuts, cuts[1:]):
        covering = sorted((max(z0, h[2]), min(z1, h[3])) for h in holes
                          if h[0] < s1 - 0.1 and h[1] > s0 + 0.1 and h[2] < z1 and h[3] > z0)
        z = z0
        for c0, c1 in covering:
            if c0 > z:
                pieces.append((s0, s1, z, c0))
            z = max(z, c1)
        if z < z1:
            pieces.append((s0, s1, z, z1))
    return pieces


def banded(wall, a0, a1, bands, holes):
    panels = []
    for z0, z1, role in bands:
        for p in rect_minus(a0, a1, z0, z1, holes):
            panels += wall.quad(*p, role)
    return panels


def recessed_door(wall, a, z0, width, height, role, depth=16.0, trim='trim'):
    """The door face `depth` behind the wall plane at a (centre), with jambs and a lintel; returns (door, jambs)."""
    a0, a1 = a - width / 2, a + width / 2
    door = Wall(wall.axis, wall.plane - wall.inward[0 if wall.axis == 'x' else 1] * depth, wall.inward)
    face = door.quad(a0, a1, z0, z0 + height, role, fit=door.fit(a0, a1, z0, z0 + height))
    jambs = []
    sign = -(wall.inward[0] if wall.axis == 'x' else wall.inward[1])        # into the wall
    for edge, facing in ((a0, 1), (a1, -1)):
        side = wall.axis_vector() * facing
        p0, p1 = wall.point(edge, z0), wall.point(edge, z0 + height)
        back = Vector(wall.inward) * -depth
        jambs.append(([p0, p0 + back, p1 + back, p1], trim, tuple(side)))
    back = Vector(wall.inward) * depth
    top = [wall.point(a0, z0 + height), wall.point(a1, z0 + height), wall.point(a1, z0 + height) - back,
           wall.point(a0, z0 + height) - back]
    jambs.append((top, trim, (0, 0, -1)))
    return face, jambs


def plaque(wall, a, z0, width, height, role, out=8.0):
    """A sign plaque on a little box standing `out` from the wall, its face fitted to the sign."""
    a0, a1 = a - width / 2, a + width / 2
    panels = wall.quad(a0, a1, z0, z0 + height, role, fit=wall.fit(a0, a1, z0, z0 + height, out), out=out)
    for edge, facing in ((a0, -1), (a1, 1)):
        side = wall.axis_vector() * facing
        p0, p1 = wall.point(edge, z0), wall.point(edge, z0 + height)
        panels.append(([p0, p0 + Vector(wall.inward) * out, p1 + Vector(wall.inward) * out, p1], 'trim', tuple(side)))
    for z, facing in ((z0, -1), (z0 + height, 1)):
        q = [wall.point(a0, z), wall.point(a1, z), wall.point(a1, z, out), wall.point(a0, z, out)]
        panels.append((q, 'trim', (0, 0, facing)))
    return panels


def box(lo, hi, side, top=None, bottom=None):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    panels = [([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], side, (0, -1, 0)),
              ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], side, (0, 1, 0)),
              ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], side, (-1, 0, 0)),
              ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], side, (1, 0, 0))]
    if top:
        panels.append(([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top, (0, 0, 1)))
    if bottom:
        panels.append(([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], bottom, (0, 0, -1)))
    return panels


def floor(x0, y0, x1, y1, z, role):
    return [([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], role, (0, 0, 1))]


def ceiling(x0, y0, x1, y1, z, role='ceiling'):
    return [([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], role, (0, 0, -1))]


# --- Rooms ------------------------------------------------------------------------------------------------------------
rooms = {}            # id -> [panels]
room_bounds = {}      # id -> (x0, y0, x1, y1, z0, z1) for markers
ambient = {}
EVENTS = {}
triggers = []         # (name, room, panels, event, cog)
# The Deep Stair bulkhead's face, for event 17's evt.SetTexture (htbulk shut, htbulkon open): the cog evt.SetTexture
# swaps (the engine loads htbulkon when the swap needs it).
BULKHEAD_COG = 9017


def room(rid, bounds, light):
    rooms[rid] = []
    room_bounds[rid] = bounds
    ambient[rid] = light


def trigger(name, rid, panels, event, cog=0):
    """cog: the faces' cog number, the key evt.SetTexture swaps them by (0: none)."""
    triggers.append((name, rid, panels, event, cog))
    EVENTS.setdefault(event, name)


# The vault: barrel-shaped across x, the plan's ceiling at the crown, 1 400 at the side walls. Its strips break at the
# sector columns and at the Chapel Steps' opening, which reaches above the springing.
VAULT, SPRING = float(next(r['ceiling'] for r in PLAN.rooms if r['id'] == 'hall')), 1400.0
XS = sorted(set(range(0, HALL_W + 1, 400)) | set(plans.HALL_COLS) | {plans.LIFT_X - 1000, plans.LIFT_X + 1000})


def vault(x):
    return VAULT - (VAULT - SPRING) * ((x - HALL_W / 2) / (HALL_W / 2)) ** 2


COLS, ROWS = plans.HALL_COLS, plans.HALL_ROWS
HALL_BANDS = [(0, 448, 'patch'), (448, 512, 'trim'), (512, 1336, 'wall'), (1336, SPRING, 'trim')]
GAL_X, GAL_Z, GAL_Y0, GAL_Y1, PARAPET = 384, 512, plans.GALLERY_Y0, plans.GALLERY_Y1, 96
BAY_W, BAY_D, BAY_H = 640, 192, 448
DOOR_W, DOOR_H = 128, 256

for r in range(3):
    for c in range(3):
        room(f'hall_{r}{c}', (COLS[c], ROWS[r], COLS[c + 1], ROWS[r + 1], 0, VAULT), 16)


def hall_room(x, y):
    c = min(2, max(0, next(i for i in range(3) if COLS[i] <= x <= COLS[i + 1])))
    r = min(2, max(0, next(i for i in range(3) if ROWS[i] <= y <= ROWS[i + 1])))
    return f'hall_{r}{c}'


for r in range(3):
    for c in range(3):
        rid = f'hall_{r}{c}'
        x0, y0, x1, y1 = COLS[c], ROWS[r], COLS[c + 1], ROWS[r + 1]
        rooms[rid] += floor(x0, y0, x1, y1, 0, 'plank' if c == 1 else 'floor')
        for xa, xb in zip(XS, XS[1:]):
            if x0 <= xa and xb <= x1:
                rooms[rid].append(([(xa, y0, vault(xa)), (xb, y0, vault(xb)), (xb, y1, vault(xb)),
                                    (xa, y1, vault(xa))], 'ceiling', (0, 0, -1)))

# Portals inside the hall: x splits (rectangles under the vault) and y splits (the vault's arch section).
portals = []          # (front room, back room, coords)
for r in range(3):
    for c in (1, 2):
        x, y0, y1 = COLS[c], ROWS[r], ROWS[r + 1]
        portals.append((f'hall_{r}{c - 1}', f'hall_{r}{c}',
                        [(x, y0, 0), (x, y1, 0), (x, y1, vault(x)), (x, y0, vault(x))]))
for r in (1, 2):
    for c in range(3):
        y, x0, x1 = ROWS[r], COLS[c], COLS[c + 1]
        arc = [(x, y, vault(x)) for x in XS if x0 <= x <= x1]
        portals.append((f'hall_{r - 1}{c}', f'hall_{r}{c}', [(x0, y, 0), (x1, y, 0)] + arc[::-1]))

# The side walls: shop bays, the home doors on the galleries, the bands.
house_events = {name: 3 + k for k, name in enumerate(['Salvage & Arms', 'Emitters', 'Provisions', 'The Clinic',
                                                       'The Last Lamp (inn)', 'Bounty board', 'Sim Hall', 'Workshop',
                                                       'Council Hall', 'Archive', 'Chapel', 'Kept Refuge'])}
home_event = 18
for side, wall_x, inward in (('west', 0, (1, 0, 0)), ('east', HALL_W, (-1, 0, 0))):
    wall = Wall('x', wall_x, inward)
    out = inward[0]
    holes = [(y - BAY_W / 2, y + BAY_W / 2, 0, BAY_H) for _, y in BAYS[side]]
    holes += [(y - DOOR_W / 2, y + DOOR_W / 2, GAL_Z, GAL_Z + DOOR_H) for y in HOME_DOORS]
    for r in range(3):
        rid = f'hall_{r}{0 if side == "west" else 2}'
        rooms[rid] += banded(wall, ROWS[r], ROWS[r + 1], HALL_BANDS, holes)
    # The bays: the house front cut round its door, the plaque above the door, plain sides, floor and ceiling.
    for name, y in BAYS[side]:
        rid = hall_room(wall_x, y)
        back = Wall('x', wall_x - out * BAY_D, inward)
        front, sign = FRONTS[name]
        fit = back.fit(y - BAY_W / 2, y + BAY_W / 2, 0, BAY_H)
        for piece in rect_minus(y - BAY_W / 2, y + BAY_W / 2, 0, BAY_H, [(y - DOOR_W / 2, y + DOOR_W / 2, 0, DOOR_H)]):
            rooms[rid] += back.quad(*piece, front, fit=fit)
        door, jambs = recessed_door(back, y, 0, DOOR_W, DOOR_H, 'door_shop')
        rooms[rid] += jambs
        trigger(f'house_{house_events[name]}', rid, door, house_events[name])
        rooms[rid] += plaque(back, y, DOOR_H + 16, 128, 64, sign)
        bx0, bx1 = sorted((wall_x, wall_x - out * BAY_D))
        for edge, facing in ((y - BAY_W / 2, 1), (y + BAY_W / 2, -1)):
            rooms[rid].append(([(bx0, edge, 0), (bx1, edge, 0), (bx1, edge, BAY_H), (bx0, edge, BAY_H)], 'wall',
                               (0, facing, 0)))
        rooms[rid] += floor(bx0, y - BAY_W / 2, bx1, y + BAY_W / 2, 0, 'floor')
        rooms[rid] += ceiling(bx0, y - BAY_W / 2, bx1, y + BAY_W / 2, BAY_H, 'trim')
    # The home doors on the gallery.
    for k, y in enumerate(HOME_DOORS):
        rid = hall_room(wall_x, y)
        door, jambs = recessed_door(wall, y, GAL_Z, DOOR_W, DOOR_H, 'door_home' if k % 2 == 0 else 'door_home2')
        rooms[rid] += jambs
        trigger(f'home_{home_event}', rid, door, home_event)
        home_event += 1
    # The gallery: a slab 32 thick at z 512 along the wall, a parapet on its edge, pillars under it, cut at the rows.
    gx0, gx1 = sorted((wall_x, wall_x + out * GAL_X))
    edge = wall_x + out * GAL_X
    for r in range(3):
        ya, yb = max(GAL_Y0, ROWS[r]), min(GAL_Y1, ROWS[r + 1])
        if yb <= ya:
            continue
        rid = f'hall_{r}{0 if side == "west" else 2}'
        rooms[rid] += floor(gx0, ya, gx1, yb, GAL_Z, 'plank')
        rooms[rid] += ceiling(gx0, ya, gx1, yb, GAL_Z - 32, 'girder')
        rooms[rid].append(([(edge, ya, GAL_Z - 32), (edge, yb, GAL_Z - 32), (edge, yb, GAL_Z), (edge, ya, GAL_Z)],
                           'trim', inward))
        px0, px1 = sorted((edge, edge - out * 24))
        rooms[rid] += [p for p in box((px0, ya, GAL_Z), (px1, yb, GAL_Z + PARAPET), 'rail', top='trim')
                       if abs(p[2][1]) < 0.5]                      # its two long faces and top; the ends join up
    for y, facing in ((GAL_Y0, -1), (GAL_Y1, 1)):                  # the gallery's ends
        rid = hall_room(wall_x, y + (1 if facing < 0 else -1))
        if facing > 0:
            rooms[rid].append(([(gx0, y, GAL_Z - 32), (gx1, y, GAL_Z - 32), (gx1, y, GAL_Z), (gx0, y, GAL_Z)],
                               'trim', (0, facing, 0)))
        px0, px1 = sorted((edge, edge - out * 24))
        rooms[rid].append(([(px0, y, GAL_Z), (px1, y, GAL_Z), (px1, y, GAL_Z + PARAPET), (px0, y, GAL_Z + PARAPET)],
                           'trim', (0, facing, 0)))
    for y in (1340, 2250, 2950, 3900, GAL_Y1 - 60):                  # pillars carrying the gallery's edge
        rid = hall_room(wall_x, y)
        px0, px1 = sorted((edge - out * 8, edge - out * 56))
        rooms[rid] += box((px0, y - 24, 0), (px1, y + 24, GAL_Z - 32), 'pillar')
    # The gallery stair: 16 steps of 32 x 64 along the wall, rising north to the gallery's south end; the space under
    # it closed off from under the gallery.
    rid = hall_room(wall_x, 700)
    rooms[rid].append(([(gx0, GAL_Y0, 0), (gx1, GAL_Y0, 0), (gx1, GAL_Y0, GAL_Z - 32), (gx0, GAL_Y0, GAL_Z - 32)],
                       'patch', (0, 1, 0)))
    for k in range(16):
        ya, yb, z = 256 + 64 * k, 256 + 64 * (k + 1), 32 * (k + 1)
        rooms[rid] += floor(gx0, ya, gx1, yb, z, 'plank')
        rooms[rid].append(([(gx0, ya, z - 32), (gx1, ya, z - 32), (gx1, ya, z), (gx0, ya, z)], 'gold', (0, -1, 0)))
        rooms[rid].append(([(edge, ya, 0), (edge, yb, 0), (edge, yb, z), (edge, ya, z)], 'patch', inward))

# The end walls: bands up to the springing, then the vault's end under its arch; openings and the big façades.
south = Wall('y', 0, (0, 1, 0))
north = Wall('y', HALL_D, (0, -1, 0))
FACADES = {name: (south if name in ('Sim Hall', 'Workshop') else north, x) for name, x in plans.FACADE_X.items()}
FACADE_W, FACADE_H, DOUBLE_W = 1280, 640, 256
OPENINGS = {'south': [(plans.REFUGE_ARCH - 256, plans.REFUGE_ARCH + 256, 0, 512),
                      (plans.LIFT_X - 384, plans.LIFT_X + 384, 0, 512),
                      (plans.WORKS_ARCH - 256, plans.WORKS_ARCH + 256, 0, 512)],
            'north': [(plans.LIFT_X - 1000, plans.LIFT_X + 1000, 0, 1536)]}
for wall, key in ((south, 'south'), (north, 'north')):
    facades = [(a, a + FACADE_W, 0, FACADE_H) for name, (w, a) in FACADES.items() if w is wall]
    holes = OPENINGS[key] + facades
    for c in range(3):
        x0, x1 = COLS[c], COLS[c + 1]
        rid = f'hall_{0 if key == "south" else 2}{c}'
        rooms[rid] += banded(wall, x0, x1, HALL_BANDS, holes)
        for xa, xb in zip(XS, XS[1:]):                              # under the arch, above the springing
            if not (x0 <= xa and xb <= x1):
                continue
            low = SPRING
            for h in holes:
                if h[0] < xb and h[1] > xa and h[3] > SPRING:
                    low = h[3]
            coords = [wall.point(xa, low), wall.point(xb, low), wall.point(xb, vault(xb)), wall.point(xa, vault(xa))]
            rooms[rid].append((coords, 'wall', wall.inward))
    for name, (w, a) in FACADES.items():
        if w is not wall:
            continue
        rid = hall_room(a + FACADE_W / 2, 10 if key == 'south' else HALL_D - 10)
        front, sign = FRONTS[name]
        centre = a + FACADE_W / 2
        fit = wall.fit(a, a + FACADE_W, 0, FACADE_H)
        for piece in rect_minus(a, a + FACADE_W, 0, FACADE_H, [(centre - DOUBLE_W / 2, centre + DOUBLE_W / 2, 0, 256)]):
            rooms[rid] += wall.quad(*piece, front, fit=fit)
        door, jambs = recessed_door(wall, centre, 0, DOUBLE_W, 256, 'door_double')
        rooms[rid] += jambs
        trigger(f'house_{house_events[name]}', rid, door, house_events[name])
        rooms[rid] += plaque(wall, centre, 256 + 8, 128, 64, sign)

# Cloth banners on little boxes standing off the bare walls: between the home doors above the galleries, and either
# side of the openings on the end walls.
BANNER_W, BANNER_H = 256, 512
banners_hung = []


def banner(wall, a, z0, rid, out=6.0):
    """A banner standing `out` off the wall: its face cut to the cloth's outline (straight sides down to 21 % of its
    height, then the point; the texture's corners beside the point are background), its edges gold."""
    banners_hung.append(a)
    role = 'banner_red' if len(banners_hung) % 2 else 'banner_blue'
    a0, a1, H = a - BANNER_W / 2, a + BANNER_W / 2, BANNER_H
    outline = [(a0, z0 + 0.21 * H), (a, z0 + 0.03 * H), (a1, z0 + 0.21 * H), (a1, z0 + H), (a0, z0 + H)]
    fit = wall.fit(a0, a1, z0, z0 + H, out)
    rooms[rid].append(([wall.point(u, z, out) for u, z in outline], role, wall.inward, fit))
    for (u0, z0_), (u1, z1_) in zip(outline, outline[1:] + outline[:1]):
        p0, p1 = wall.point(u0, z0_), wall.point(u1, z1_)
        q0, q1 = wall.point(u0, z0_, out), wall.point(u1, z1_, out)
        mid = (p0 + p1) / 2
        centre = wall.point(a, z0 + H * 0.6)
        rooms[rid].append(([p0, p1, q1, q0], 'gold', tuple(mid - centre)))


for side, wall_x, inward in (('west', 0, (1, 0, 0)), ('east', HALL_W, (-1, 0, 0))):
    wall = Wall('x', wall_x, inward)
    for ya, yb in zip(HOME_DOORS, HOME_DOORS[1:]):
        y = (ya + yb) / 2
        banner(wall, y, 820, hall_room(wall_x, y))
for wall, xs in ((south, (2548, 3852)), (north, (1990, 4410))):     # between the end walls' houses and openings
    for x in xs:
        banner(wall, x, 760, hall_room(x, 10 if wall is south else HALL_D - 10))

# The four great pillars, inside their sectors, and the coolant fountain.
GREAT_PILLARS = ((1500, 1300), (4900, 1300), (1500, 3500), (4900, 3500))
for x, y in GREAT_PILLARS:
    rooms[hall_room(x, y)] += box((x - 192, y - 192, 0), (x + 192, y + 192, vault(x) - 120), 'pillar', top='trim')
(FX, FY), FR = plans.FOUNTAIN, 400
rid = hall_room(FX, FY)
ring = [(FX + FR * math.cos(math.pi / 8 + k * math.pi / 4), FY + FR * math.sin(math.pi / 8 + k * math.pi / 4))
        for k in range(8)]
inner = [(FX + (FR - 40) * math.cos(math.pi / 8 + k * math.pi / 4),
          FY + (FR - 40) * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
for k in range(8):
    (ax, ay), (bx, by) = ring[k], ring[(k + 1) % 8]
    (ix, iy), (jx, jy) = inner[k], inner[(k + 1) % 8]
    mx, my = (ax + bx) / 2 - FX, (ay + by) / 2 - FY
    rooms[rid].append(([(ax, ay, 0), (bx, by, 0), (bx, by, 96), (ax, ay, 96)], 'well', (mx, my, 0)))
    rooms[rid].append(([(ax, ay, 96), (bx, by, 96), (jx, jy, 96), (ix, iy, 96)], 'well', (0, 0, 1)))
    rooms[rid].append(([(ix, iy, 64), (jx, jy, 64), (jx, jy, 96), (ix, iy, 96)], 'well', (-mx, -my, 0)))
water = [(x, y, 64) for x, y in inner]
rooms[rid].append((water, 'water', (0, 0, 1)))
trigger('fountain', rid, box((FX - 40, FY - 40, 64), (FX + 40, FY + 40, 320), 'well', top='strip'), 15)

# --- Rooms off the hall -----------------------------------------------------------------------------------------------
SMALL = [(0, 16, 'trim'), (16, 480, 'wall'), (480, 512, 'strip')]


def walled(rid, x0, y0, x1, y1, z, height, bands, holes_by_side, floor_role='floor', ceiling_role='ceiling'):
    rooms[rid] += floor(x0, y0, x1, y1, z, floor_role)
    rooms[rid] += ceiling(x0, y0, x1, y1, z + height, ceiling_role)
    for side, wall, a0, a1 in (('south', Wall('y', y0, (0, 1, 0)), x0, x1),
                                ('north', Wall('y', y1, (0, -1, 0)), x0, x1),
                                ('west', Wall('x', x0, (1, 0, 0)), y0, y1),
                                ('east', Wall('x', x1, (-1, 0, 0)), y0, y1)):
        holes = holes_by_side.get(side, [])
        if holes == 'open':
            continue
        rooms[rid] += banded(wall, a0, a1, [(z + b0, z + b1, role) for b0, b1, role in bands],
                             [(h[0], h[1], z + h[2], z + h[3]) for h in holes])
    return rooms[rid]


# Rooms beside the hall (and beside each other) have a wall THICK between them, crossed by a reveal: two faces in
# one plane facing apart fight in the depth buffer, as the indoor renderer draws both.
THICK = 64


def reveal(rid, x0, y0, x1, y1, z0, z1, along, floor_role='floor', ceiling_role='trim', side_role='trim'):
    """The floor, soffit and jambs of an opening through a thick wall; `along` is the axis the passage runs on."""
    rooms[rid] += floor(x0, y0, x1, y1, z0, floor_role)
    rooms[rid] += ceiling(x0, y0, x1, y1, z1, ceiling_role)
    if along == 'y':
        rooms[rid] += Wall('x', x0, (1, 0, 0)).quad(y0, y1, z0, z1, side_role)
        rooms[rid] += Wall('x', x1, (-1, 0, 0)).quad(y0, y1, z0, z1, side_role)
    else:
        rooms[rid] += Wall('y', y0, (0, 1, 0)).quad(x0, x1, z0, z1, side_role)
        rooms[rid] += Wall('y', y1, (0, -1, 0)).quad(x0, x1, z0, z1, side_role)


# The Lift Gate under the lift line (x L), the Kept Refuge (west) and the Water Works (east) behind the south wall.
L = plans.LIFT_X
LG0, LG1 = L - 512, L + 512                 # the Lift Gate's west and east walls
room('liftgate', (LG0, -768, LG1, 0, 0, 512), 18)
walled('liftgate', LG0 + THICK, -768, LG1, -THICK, 0, 512, SMALL,
       {'north': [(L - 384, L + 384, 0, 512)], 'west': [(-640, -384, 0, 256)], 'south': [(L - 128, L + 128, 0, 384)]})
reveal('liftgate', L - 384, -THICK, L + 384, 0, 0, 512, 'y')
reveal('liftgate', LG0, -640, LG0 + THICK, -384, 0, 256, 'x')
door, jambs = recessed_door(Wall('y', -768, (0, 1, 0)), L, 0, 256, 384, 'cage')
rooms['liftgate'] += jambs
trigger('lift_cage', 'liftgate', door, 2)
portals.append(('liftgate', hall_room(L, 10), [(L - 384, 0, 0), (L + 384, 0, 0), (L + 384, 0, 512), (L - 384, 0, 512)]))

RA = plans.REFUGE_ARCH
room('refuge', (0, -1800, 1500, 0, 0, 512), 18)
SHACK = [(0, 448, 'scrap'), (448, 512, 'trim')]
walled('refuge', 0, -1800, 1500, -THICK, 0, 512, SHACK,
       {'north': [(RA - 256, RA + 256, 0, 512)], 'west': [(-1364, -1236, 0, 256), (-664, -536, 0, 256)],
        'south': [(686, 814, 0, 256)]}, floor_role='plank', ceiling_role='girder')
reveal('refuge', RA - 256, -THICK, RA + 256, 0, 0, 512, 'y', floor_role='plank')
for name, wall, a, event in (('shack_tamsin', Wall('y', -1800, (0, 1, 0)), 750, house_events['Kept Refuge']),
                             ('shack_1', Wall('x', 0, (1, 0, 0)), -1300, 30),
                             ('shack_2', Wall('x', 0, (1, 0, 0)), -600, 31)):
    door, jambs = recessed_door(wall, a, 0, DOOR_W, DOOR_H, 'door_shack')
    rooms['refuge'] += jambs
    trigger(name, 'refuge', door, event)
portals.append(('refuge', hall_room(RA, 10), [(RA - 256, 0, 0), (RA + 256, 0, 0), (RA + 256, 0, 512),
                                              (RA - 256, 0, 512)]))

WA = plans.WORKS_ARCH
W0, W1 = HALL_W - 1500, HALL_W              # the Water Works' west and east walls
room('works', (W0, -1800, W1, 0, 0, 512), 18)
WORKS = [(0, 64, 'trim'), (64, 448, 'works_wall'), (448, 512, 'trim')]
walled('works', W0, -1800, W1, -THICK, 0, 512, WORKS,
       {'north': [(WA - 256, WA + 256, 0, 512)], 'east': [(-1028, -772, 0, 256)]})
reveal('works', WA - 256, -THICK, WA + 256, 0, 0, 512, 'y')
door, jambs = recessed_door(Wall('x', W1, (-1, 0, 0)), -900, 0, 256, 256, 'hatch')
rooms['works'] += jambs
trigger('works_door', 'works', door, 16)
rooms['works'] += box((W0 + 60, -1700, 0), (W0 + 200, -300, 96), 'pipe', top='pipe')
rooms['works'] += box((W1 - 200, -1700, 300), (W1 - 100, -1100, 420), 'pipe', top='pipe', bottom='pipe')
portals.append(('works', hall_room(WA, 10), [(WA - 256, 0, 0), (WA + 256, 0, 0), (WA + 256, 0, 512), (WA - 256, 0, 512)]))

# The Chapel Steps: 12 steps of 32 x 64 up to z 384, then the Chapel.
STEPS_TOP = 384
S0, S1 = L - 1000, L + 1000
room('steps', (S0, HALL_D, S1, HALL_D + 768, 0, 1536), 16)
rooms['steps'] += ceiling(S0, HALL_D, S1, HALL_D + 768, 1536)
for k in range(12):
    ya, yb, z = HALL_D + 64 * k, HALL_D + 64 * (k + 1), 32 * (k + 1)
    rooms['steps'] += floor(S0, ya, S1, yb, z, 'marble')
    rooms['steps'].append(([(S0, ya, z - 32), (S1, ya, z - 32), (S1, ya, z), (S0, ya, z)], 'gold', (0, -1, 0)))
    for x, inward in ((S0, (1, 0, 0)), (S1, (-1, 0, 0))):
        rooms['steps'].append(([(x, ya, z), (x, yb, z), (x, yb, 1536), (x, ya, 1536)], 'wall', inward))
north_steps = Wall('y', HALL_D + 768, (0, -1, 0))
rooms['steps'] += banded(north_steps, S0, S1, [(STEPS_TOP, 1536, 'wall')], [(LG0, LG1, STEPS_TOP, STEPS_TOP + 1024)])
portals.append((hall_room(L, HALL_D - 10), 'steps', [(S0, HALL_D, 0), (S1, HALL_D, 0), (S1, HALL_D, 1536),
                                                      (S0, HALL_D, 1536)]))

CHAPEL = (L - 1300, HALL_D + 768 + THICK, L + 1300, HALL_D + 768 + THICK + 1600)
y_s = HALL_D + 768                          # the Steps' north wall; the Chapel's south wall stands THICK behind it
room('chapel', (CHAPEL[0], y_s, CHAPEL[2], CHAPEL[3], STEPS_TOP, STEPS_TOP + 1024), 14)
CHAPEL_BANDS = [(0, 32, 'trim'), (32, 960, 'wall'), (960, 1024, 'trim')]
walled('chapel', *CHAPEL, STEPS_TOP, 1024, CHAPEL_BANDS, {'south': [(LG0, LG1, 0, 1024)]}, floor_role='marble')
reveal('chapel', LG0, y_s, LG1, CHAPEL[1], STEPS_TOP, STEPS_TOP + 1024, 'y', floor_role='marble')
portals.append(('steps', 'chapel', [(LG0, y_s, STEPS_TOP), (LG1, y_s, STEPS_TOP), (LG1, y_s, STEPS_TOP + 1024),
                                    (LG0, y_s, STEPS_TOP + 1024)]))
altar = box((L - 200, CHAPEL[3] - 400, STEPS_TOP), (L + 200, CHAPEL[3] - 200, STEPS_TOP + 96), 'marble', top='marble')
rooms['chapel'] += [p for p in altar if p[2] != (0, -1, 0)]
trigger('altar', 'chapel', [p for p in altar if p[2] == (0, -1, 0)], house_events['Chapel'])

# The Deep Stair: head, a flight south, the landing, a flight west, the bulkhead. DX0-DX1 is the head's and the
# upper flight's width; the lower flight runs west to DB1, the bulkhead's east wall.
DX0 = plans.DEEP_X
DX1, DB1, DB0 = DX0 + 512, DX0 - 1024, DX0 - 1876
room('deep_top', (DX0, -768, DX1, -256, 0, 512), 22)
walled('deep_top', DX0, -768, DX1, -256, 0, 512, SMALL, {'south': 'open', 'east': [(-640, -384, 0, 256)]})
portals.append(('liftgate', 'deep_top', [(DX1, -640, 0), (DX1, -384, 0), (DX1, -384, 256), (DX1, -640, 256)]))
room('flight1', (DX0, -1792, DX1, -768, -512, 512), 24)
for k in range(16):
    ya, yb, z = -768 - 64 * (k + 1), -768 - 64 * k, -32 * (k + 1)
    rooms['flight1'] += floor(DX0, ya, DX1, yb, z, 'floor')
    rooms['flight1'].append(([(DX0, yb, z), (DX1, yb, z), (DX1, yb, z + 32), (DX0, yb, z + 32)], 'trim',
                             (0, -1, 0)))
    for x, inward in ((DX0, (1, 0, 0)), (DX1, (-1, 0, 0))):
        rooms['flight1'].append(([(x, ya, z), (x, yb, z), (x, yb, 512 + z + 32), (x, ya, 512 + z)], 'wall', inward))
rooms['flight1'].append(([(DX0, -768, 512), (DX1, -768, 512), (DX1, -1792, 0), (DX0, -1792, 0)], 'ceiling',
                         (0, -0.5, -1)))
portals.append(('deep_top', 'flight1', [(DX0, -768, 0), (DX1, -768, 0), (DX1, -768, 512), (DX0, -768, 512)]))
room('landing', (DX0, -2304, DX1, -1792, -512, 0), 24)
walled('landing', DX0, -2304, DX1, -1792, -512, 512, SMALL, {'north': 'open', 'west': 'open'})
portals.append(('flight1', 'landing', [(DX0, -1792, -512), (DX1, -1792, -512), (DX1, -1792, 0), (DX0, -1792, 0)]))
room('flight2', (DB1, -2304, DX0, -1792, -1024, 0), 24)
for k in range(16):
    xa, xb, z = DX0 - 64 * (k + 1), DX0 - 64 * k, -512 - 32 * (k + 1)
    rooms['flight2'] += floor(xa, -2304, xb, -1792, z, 'floor')
    rooms['flight2'].append(([(xb, -2304, z), (xb, -1792, z), (xb, -1792, z + 32), (xb, -2304, z + 32)], 'trim',
                             (-1, 0, 0)))
    for y, inward in ((-2304, (0, 1, 0)), (-1792, (0, -1, 0))):
        rooms['flight2'].append(([(xa, y, z), (xb, y, z), (xb, y, z + 32 + 512), (xa, y, z + 512)], 'wall', inward))
rooms['flight2'].append(([(DX0, -2304, 0), (DX0, -1792, 0), (DB1, -1792, -512), (DB1, -2304, -512)], 'ceiling',
                         (-0.5, 0, -1)))
portals.append(('landing', 'flight2', [(DX0, -2304, -512), (DX0, -1792, -512), (DX0, -1792, 0), (DX0, -2304, 0)]))
room('bulkhead', (DB0, -2816, DB1, -1280, -1024, -512), 24)
walled('bulkhead', DB0, -2816, DB1, -1280, -1024, 512, SMALL,
       {'east': [(-2304, -1792, 0, 512)], 'west': [(-2240, -1856, 0, 384)]})
door, jambs = recessed_door(Wall('x', DB0, (1, 0, 0)), -2048, -1024, 384, 384, 'bulkhead', depth=24)
rooms['bulkhead'] += jambs
trigger('bulkhead', 'bulkhead', door, 17, cog=BULKHEAD_COG)
portals.append(('flight2', 'bulkhead', [(DB1, -2304, -1024), (DB1, -1792, -1024), (DB1, -1792, -512),
                                        (DB1, -2304, -512)]))

# --- Market stalls (geometry) --------------------------------------------------------------------------------------


def beam(p0, p1, width, role):
    """A square bar between two points (chains, hoops, brackets, posts), open at its ends."""
    a, b = Vector(p0), Vector(p1)
    axis = (b - a).normalized()
    u = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))).normalized() * (width / 2)
    v = axis.cross(u).normalized() * (width / 2)
    corners = [u + v, -u + v, -u - v, u - v]
    panels = []
    for k in range(4):
        c0, c1 = corners[k], corners[(k + 1) % 4]
        panels.append(([a + c0, a + c1, b + c1, b + c0], role, tuple((c0 + c1).normalized())))
    return panels                                          # no end caps: they sit on a wall, a floor or a joint


# The lamps are the plan's light fixtures (decorations, below): no hoops or brackets.

# Four market stalls between the great pillars: a counter of crates, a cloth awning on four posts.
STALLS = [(1700, FY, 0.0), (HALL_W - 1700, FY, math.pi)]
for sx, sy, toward in STALLS:                              # `toward`: the side the counter faces
    rid = hall_room(sx, sy)
    c, s_ = math.cos(toward), math.sin(toward)

    def at(along, out, z=0.0):
        return (sx + c * out - s_ * along, sy + s_ * out + c * along, z)
    xs = sorted([at(-260, -60)[0], at(260, 60)[0]])
    ys = sorted([at(-260, -60)[1], at(260, 60)[1]])
    rooms[rid] += box((xs[0], ys[0], 0), (xs[1], ys[1], 110), 'stall', top='plank')
    for along in (-300, 300):
        for out in (-160, 140):
            rooms[rid] += beam(at(along, out), at(along, out, 340 if out > 0 else 380), 14, 'gold')
    p0, p1, p2, p3 = at(-330, 170, 330), at(330, 170, 330), at(330, -190, 380), at(-330, -190, 380)
    rooms[rid].append(([p0, p1, p2, p3], 'awning', (0, 0, 1)))
    under = [tuple(Vector(q) - Vector((0, 0, 4))) for q in (p3, p2, p1, p0)]    # 4 below: one plane would z-fight
    rooms[rid].append((under, 'awning', (0, 0, -1)))

# --- Objects: rooms, portals, triggers, decorations, lights -----------------------------------------------------------
for rid, panels in rooms.items():
    obj = mesh('ROOM_' + rid, panels, 'room', semantic_id=rid)
    obj['min_ambient_light_level'] = ambient[rid]
    metadata['rooms'].append({'id': 'room_' + rid, 'source_nodes': [obj.name], 'min_ambient_light_level': ambient[rid]})


def own(rid, obj):
    next(r for r in metadata['rooms'] if r['id'] == 'room_' + rid)['source_nodes'].append(obj.name)


for index, (front, back, coords) in enumerate(portals):
    name = f'PORTAL_{front}_{back}_{index}'
    b = room_bounds[front]
    centre = Vector(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (b[4] + b[5]) / 2))
    points = [Vector(p) for p in coords]
    normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
    facing = tuple(normal if normal.dot(centre - points[0]) > 0 else -normal)
    mesh(name, [(coords, 'marker', facing)], 'portal')
    metadata['portals'].append({'id': name[7:], 'source_node': name, 'front_room': 'room_' + front,
                                'back_room': 'room_' + back})

for name, rid, panels, event, cog in triggers:
    obj = mesh('TRIGGER_' + name, panels, 'trigger', event_id=event, activation='click')
    own(rid, obj)
    record = {'id': name, 'source_node': obj.name, 'flags': [], 'trigger': {'event_id': event, 'type': 'click'}}
    if cog:
        record['cog_number'] = cog
    metadata['surfaces'].append(record)


def room_at(x, y, z):
    for rid, (x0, y0, x1, y1, z0, z1) in room_bounds.items():
        if x0 <= x <= x1 and y0 <= y <= y1 and z0 - 1 <= z <= z1 + 1:
            return rid
    raise ValueError((x, y, z))


decorations = []


def decoration(name, x, y, z, facing=0):
    index = len(decorations)
    node = f'DECOR_{name}_{index}'
    obj = mesh(node, [([(x - 1, y - 1, z), (x + 1, y - 1, z), (x + 1, y + 1, z), (x - 1, y + 1, z)], 'marker',
                       (0, 0, 1))], 'decoration')
    own(room_at(x, y, z), obj)
    metadata['entities'].append({'id': f'{name}_{index}', 'kind': 'decoration', 'source_node': node,
                                 'decoration_list_id': DECORATION_IDS[name] - 1, 'event_id_primary': 0,
                                 'event_id_secondary': 0, 'facing': int(round(facing)) % 360})
    decorations.append(name)


# Benches round the fountain, along its rim (facing BENCH_YAW + their angle round it).
BENCH_YAW = 0                   # a bench's long side lies along its facing + 90 (seen in review/build02)
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    decoration('hes_bench', FX + 640 * math.cos(a), FY + 640 * math.sin(a), 0, math.degrees(a) + BENCH_YAW)
# The stalls' goods on and round their counters.
for sx, sy, toward in STALLS:
    c, s_ = math.cos(toward), math.sin(toward)
    d = math.degrees(toward)
    decoration('hes_goods_cells', sx - s_ * 60 + c * 10, sy + c * 60 + s_ * 10, 110, d + 90)
    decoration('hes_crate_clean', sx - c * 260 + s_ * 200, sy - s_ * 260 - c * 200, 0, d + 15)
    decoration('hes_drum_clean', sx - c * 230 - s_ * 230, sy - s_ * 230 + c * 230, 0)
# Salvage stacked against the great pillars, a different load at each.
for (px, py), load in zip(GREAT_PILLARS,
                          (('hes_crate_clean', 'hes_drum_clean'), ('hes_container', 'hes_crate_clean'),
                           ('hes_luggage_pile', 'hes_drum_clean'), ('hes_goods_cells', 'hes_crate_clean'))):
    toward_wall = -1 if px < HALL_W / 2 else 1                  # the pillar's side away from the fountain
    decoration(load[0], px + toward_wall * 330, py, 0, 90)
    decoration(load[1], px, py + (300 if py > HALL_D / 2 else -300), 0, 30)
# The Lift Gate's sides: luggage and cases; the Chapel Steps' foot: braziers and offerings.
L = plans.LIFT_X
for x in (L - 600, L + 600):
    decoration('hes_luggage_pile', x, 350, 0, 0 if x < L else 180)
for x in (L - 880, L + 880):
    decoration('hes_brazier_clean', x, HALL_D - 220, 0)
    decoration('hes_offerings_crystal', x + (120 if x < L else -120), HALL_D + 96, 64)      # on the second step
# Under the galleries, between the shop bays: crates and a bench to sit on.
for side, wall_x in (('west', 0), ('east', HALL_W)):
    out = 1 if side == 'west' else -1
    for y in ((3000, 3900) if side == 'west' else (2100, 3500)):    # clear of the Clinic's bay
        decoration('hes_bench', wall_x + out * 150, y, 0, 0)
    decoration('hes_crate_clean', wall_x + out * 140, GAL_Y1 - 200, 0, 90)
for y in (1800, 3000, 4300):
    decoration('hes_drum_clean', 200, y, GAL_Z)
    decoration('hes_drum_clean', HALL_W - 200, y + 300, GAL_Z)
# The Chapel, the Refuge, the Lift Gate and the Water Works.
decoration('hes_relay_post', L, CHAPEL[3] - 300, STEPS_TOP + 96)
for dx in (-320, 320):
    for dy in (-60, 160):
        decoration('hes_offerings_crystal', L + dx, CHAPEL[3] - 300 + dy, STEPS_TOP)
for k in range(8):
    decoration('hes_bedroll', 250 + (k % 4) * 300, -1500 + (k // 4) * 600, 0)
for x, y in ((400, -900), (1100, -300), (1100, -1500)):
    decoration('hes_brazier', x, y, 0)
for x, y in ((150, -200), (1350, -800), (1350, -1650), (200, -1700), (700, -1100), (900, -700)):
    decoration('hes_salvage_heap', x, y, 0)
decoration('hes_container', 1300, -150, 0)
decoration('hes_container', 150, -1050, 0)
decoration('hes_drum_clean', L - 300, -650, 0)
decoration('hes_drum_clean', L + 300, -650, 0)
decoration('hes_crate_clean', W1 - 200, -300, 0, 30)                  # the Water Works: spares and drums
decoration('hes_drum_clean', W0 + 400, -1650, 0)
decoration('hes_drum_clean', W0 + 560, -1600, 0)

for light in PLAN.lights:
    x, y, z = light['x'], light['y'], light['z']
    if light['fixture']:                             # a fixture is its own light (make_dungeon_plans.py FIXTURES)
        decoration(light['fixture'], x + (1 if x == 0 else -1 if x == HALL_W else 0),
                   y + (1 if y == 0 else -1 if y == HALL_D else 0), z, light['facing'])
        continue
    name = 'LIGHT_' + light['id']
    obj = mesh(name, [([(x - 1, y - 1, z), (x + 1, y - 1, z), (x + 1, y + 1, z), (x - 1, y + 1, z)], 'marker',
                       (0, 0, 1))], 'light_marker', radius=light['radius'], brightness=31)
    own(room_at(x, y, z), obj)
    metadata['lights'].append({'id': light['id'], 'source_node': name, 'color': list(light['colour']),
                               'radius': light['radius'], 'brightness': 31, 'type': 'point'})

# --- Export -----------------------------------------------------------------------------------------------------------
bpy.ops.export_scene.gltf(filepath=str(OUTPUT / 'hes_undervault.glb'), export_format='GLB', use_active_scene=True,
                          export_yup=False, export_cameras=False, export_lights=False, export_apply=True,
                          export_extras=True)
(OUTPUT / 'hes_undervault.geometry.yml').write_text(json.dumps(metadata, indent=2) + '\n')
semantic = {'map': 'hes_undervault.blv',
            'arrivals': {'lift': {'position': [plans.LIFT_X, -300, 0], 'direction_degrees': 90},
                         'water_works': {'position': [HALL_W - 300, -900, 0], 'direction_degrees': 180},
                         # D15's way back (CR-P3-14): a pace in front of the bulkhead, facing away from it, east
                         # to the lower flight.
                         'deep_stair_bulkhead': {'position': [DB0 + 192, -2048, -1024], 'direction_degrees': 0}},
            'cogs': {'bulkhead': BULKHEAD_COG},
            'house_events': house_events, 'events': EVENTS, 'decorations': len(decorations),
            'sectors': [r['id'] for r in metadata['rooms']]}
(OUTPUT / 'hes_undervault.semantic.json').write_text(json.dumps(semantic, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / 'hes_undervault.blend'), compress=True)
print(json.dumps({'objects': len(scene.objects), 'sectors': len(metadata['rooms']) + 1,
                  'portals': len(metadata['portals']), 'triggers': len(metadata['surfaces']),
                  'decorations': len(decorations), 'lights': len(metadata['lights'])}))
