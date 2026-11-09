"""Step 5 (after hes_turrets_claude/scripts/build_actor_v2.py): the Harvester actor from the textured, split model.

Reads work/harvester_tex.blend (parts.py, prepare_uv.py, adopt_retexture.py) and textures/harvester_* (compose.py).
Writes export/hes_harvester_lod0.glb (LOD0, rig, clips), export/hes_harvester_authored_lods.glb (LOD1..3 on the same
rig, no clips; scripts/link_lods.py links them), export/hes_harvester.blend and export/hes_harvester_info.json.

Materials: HS_Harvester (the retexture's maps) and HS_Glow_Harvester (the added pieces, textures/harvester_glow_*: a
dark base colour and the swatches as its emissive texture; set_emissive.py sets the strength).
Added pieces (glow material, swatches from compose.py):
  the sprayer's throat  a disc inside the nozzle mouth (B_Sprayer); Socket_Nozzle just outside it
  core slots            a narrow vertical white-gold strip on the outer face of each core drum, laid onto the surface
                        by ray casts (B_Body)
  vent louvres          a glowing louvre plate per heat vent, shaped to VENT_SCALE of its hexagonal frame's outline
                        (measure_vents.py) on the frame's slanted plane; bound VENT_HIDE behind it, inside the hood
                        (B_Vent_L / B_Vent_R): the Dig clip slides it forward into the frame, so the vents light up
                        (a swinging hatch had no room: a solid block sits 0.2 m behind each frame)
Bones (every vertex rigid on one bone; parts from parts.py):
  B_Root     the ground centre, not animated (the engine turns and moves the actor)
  B_Body     child of B_Root, pivot on the ground centre: hull, tracks, fins, drums, hoods (rumble, lunge, sag)
  B_Boom     the hinge between the gold hubs: the drill housing's rings (tilts down to dig)
  B_Drill    child of B_Boom on the drill's axis, along -y: the drill cone (spins)
  B_Sprayer  the gooseneck's base: neck and nozzle (swivels about the vertical; pitches when it dies)
  B_Vent_L/R the vent louvres (left = +x, right = -x), sliding along -y
  B_Bucket_R0..5, B_Bucket_L0..5  the conveyor buckets, front to rear (move one step rearward per Walking cycle)
Clips (30 fps): Standing 4 s, Walking 2 s, Attack (melee, drill lunge) 1.5 s, Spray (ranged and cast) 1.5 s,
Dig 8 s (harvester.lua's dig stop), Hit 0.5 s, Death 3 s, Dead 1 s."""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH = 'Harvester'
OUTNAME = 'hes_harvester'
FPS = 30
LOD_RATIOS = [0.5, 0.25, 0.12]
DROP_BELOW = [0.0, 0.05, 0.10]
TEX = os.path.join(HERE, 'textures')
swatch = json.load(open(os.path.join(TEX, 'harvester_swatches.json')))

HINGE = Vector((0.0, -2.83, 1.20))                # between the gold hinge hubs (components 201 / 101)
SPRAYER_BASE = Vector((-0.425, 3.33, 2.05))       # the gooseneck's foot (component 40)
NOZZLE = Vector((-1.201, 4.074, 2.807))           # centre of the nozzle mouth (component 4), pointing +y
NOZZLE_R = 0.12
DRUM_X = {'L': (0.402, 1.428), 'R': (-1.414, -0.434)}
DRUM_YZ = (1.48, 2.40)
SLOT_HALF = (0.065, 0.30)                         # the core slot: half width along y, half height
# outer outline (x, z) of each vent frame's front ring (measure_vents.py, components 2 and 44); the ring's plane
# leans back: y = -2.37 at z 1.70, -2.20 at z 2.50
VENT_HULL = {'L': [(0.596, 2.096), (0.809, 1.782), (1.015, 1.7), (1.661, 1.73), (1.796, 1.757), (1.711, 2.02),
                   (1.402, 2.421), (1.308, 2.498), (0.909, 2.489), (0.802, 2.436), (0.716, 2.358), (0.645, 2.229)],
             'R': [(-1.773, 1.737), (-1.646, 1.727), (-1.039, 1.697), (-0.83, 1.779), (-0.638, 2.103), (-0.688, 2.247),
                   (-0.75, 2.363), (-0.826, 2.432), (-0.94, 2.484), (-1.329, 2.489), (-1.399, 2.412), (-1.692, 2.017)]}
VENT_SCALE = 0.82
VENT_INSET = 0.05                                 # the louvre plate's open position behind the frame's front plane
VENT_HIDE = 0.60                                  # how far behind that it is bound (hidden in the hood)


def vent_plane_y(z):
    return -2.37 + (z - 1.70) * (0.17 / 0.80)
BUCKET_STEP = (2.06 - (-1.72)) / 5                # parts.py

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'harvester_tex.blend'))
scene = bpy.context.scene
scene.render.fps, scene.render.fps_base = FPS, 1
body = bpy.data.objects['harvester']
drill_axis = Vector(body['drill_axis'])


def select_only(objs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = active or objs[0]


def image(path, colour):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return img


def pbr_material(name, prefix):
    """Principled material on <prefix>_basecolor/normal/orm (glTF ORM: G roughness, B metallic)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage'); base.image = image(prefix + '_basecolor.png', True)
    links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    orm = nodes.new('ShaderNodeTexImage'); orm.image = image(prefix + '_orm.png', False)
    sep = nodes.new('ShaderNodeSeparateColor')
    links.new(orm.outputs['Color'], sep.inputs['Color'])
    links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    ntex = nodes.new('ShaderNodeTexImage'); ntex.image = image(prefix + '_normal.png', False)
    nmap = nodes.new('ShaderNodeNormalMap')
    links.new(ntex.outputs['Color'], nmap.inputs['Color'])
    links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def glow_material():
    mat = bpy.data.materials.new(f'HS_Glow_{MESH}')   # not HS_Harvester...: emission.py matches by prefix
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage'); base.image = image(os.path.join(TEX, 'harvester_glow_basecolor.png'), True)
    base.interpolation = 'Linear'
    links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    glow = nodes.new('ShaderNodeTexImage'); glow.image = image(os.path.join(TEX, 'harvester_glow_emissive.png'), True)
    links.new(glow.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Metallic'].default_value = 0.0
    return mat


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


body.name = body.data.name = MESH
body.data.materials.clear()
body.data.materials.append(pbr_material(f'HS_{MESH}', os.path.join(TEX, 'harvester')))
co = np.array([v.co[:] for v in body.data.vertices])
fpart = np.zeros(len(body.data.polygons), int); body.data.attributes['part'].data.foreach_get('value', fpart)
vpart = np.zeros(len(co), int)
for poly in body.data.polygons:
    for vi in poly.vertices:
        vpart[vi] = fpart[poly.index]
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
BOTTOM = co[(vpart == 0) & (co[:, 2] < 0.15)]          # the hull's underside (tracks, guards, plates)
BOTTOM_REST = float(BOTTOM[:, 2].min())

# ---------------------------------------------------------------- added pieces
add = bmesh.new()
uvl = add.loops.layers.uv.new('UVMap')
piece_bone = []                                         # per added face: bone name


def swatch_uv(name, s, t):
    u0, v0, u1, v1 = swatch[name]
    return (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)


def face(verts_uv, bone, outward=None):
    f = add.faces.new([v for v, _ in verts_uv])
    for loop, (_, uv) in zip(f.loops, verts_uv):
        loop[uvl].uv = uv
    f.normal_update()
    if outward is not None and f.normal.dot(Vector(outward)) < 0:
        f.normal_flip()
    piece_bone.append(bone)
    return f


def add_disc(centre, normal, radius, bone, name, sides=16):
    """A flat disc facing `normal` (an inner ring and a strip cap: no high-valence fan), radial swatch UVs."""
    n = Vector(normal).normalized()
    a = n.orthogonal().normalized(); b = n.cross(a)
    rings = []
    for k, rr in enumerate((radius * 0.45, radius)):
        count = sides if k else sides // 2
        rings.append([(add.verts.new(Vector(centre) + (a * math.cos(2 * math.pi * i / count) + b * math.sin(
            2 * math.pi * i / count)) * rr), swatch_uv(name, 0.5 + 0.5 * rr / radius * math.cos(2 * math.pi * i / count),
                                                       0.5 + 0.5 * rr / radius * math.sin(2 * math.pi * i / count)))
                      for i in range(count)])
    inner, outer = rings
    m = len(inner)
    face(inner[::-1], bone, n)
    for i in range(sides):
        j = (i + 1) % sides
        ii, jj = (i // 2) % m, ((i + 1) // 2) % m
        quad = [outer[i], outer[j], inner[jj]] + ([inner[ii]] if ii != jj else [])
        face(quad, bone, n)


def add_grid(corner_fn, nu, nv, name, bone, outward):
    """A grid of quads whose vertex (i, j) is corner_fn(i / nu, j / nv); swatch UVs over the whole grid."""
    verts = [[(add.verts.new(corner_fn(i / nu, j / nv)), swatch_uv(name, i / nu, j / nv)) for j in range(nv + 1)]
             for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            face([verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1]], bone, outward)


sockets = {}
# the sprayer's throat, 4 cm inside the mouth
add_disc(NOZZLE - Vector((0, 0.04, 0)), (0, 1, 0), NOZZLE_R, 'B_Sprayer', 'nozzle')
sockets['Socket_Nozzle'] = (NOZZLE + Vector((0, 0.10, 0)), 'B_Sprayer')

# core slots on the drums' outer faces: a 1 x 6 strip laid onto the surface by rays from outside
slot_hits = {}
for side, (x0, x1) in DRUM_X.items():
    sign = 1 if side == 'L' else -1
    def on_drum(s, t, sign=sign):
        y = DRUM_YZ[0] + (s - 0.5) * 2 * SLOT_HALF[0]
        z = DRUM_YZ[1] + (t - 0.5) * 2 * SLOT_HALF[1]
        loc, nrm, _, _ = bvh.ray_cast(Vector((sign * 4.0, y, z)), Vector((-sign, 0, 0)))
        return loc + nrm * 0.006
    add_grid(on_drum, 1, 6, 'core', 'B_Body', (sign, 0, 0))
    slot_hits[side] = list(on_drum(0.5, 0.5))

# vent louvres: the frame outline shrunk about its centre, on the frame's slanted plane, bound hidden in the hood
for side, hull in VENT_HULL.items():
    pts = np.array(hull)
    c = pts.mean(0)
    inner = c + VENT_SCALE * (pts - c)
    lo, hi = inner.min(0), inner.max(0)
    ring = [(add.verts.new(Vector((x, vent_plane_y(z) + VENT_INSET + VENT_HIDE, z))),
             swatch_uv('grille', (x - lo[0]) / (hi[0] - lo[0]), (z - lo[1]) / (hi[1] - lo[1]))) for x, z in inner]
    centre = (add.verts.new(Vector((c[0], vent_plane_y(c[1]) + VENT_INSET + VENT_HIDE, c[1]))),
              swatch_uv('grille', (c[0] - lo[0]) / (hi[0] - lo[0]), (c[1] - lo[1]) / (hi[1] - lo[1])))
    for i in range(len(ring)):                          # a 12-triangle fan on a small plate
        face([centre, ring[i], ring[(i + 1) % len(ring)]], f'B_Vent_{side}', (0, -1, 0.21))

added_faces = len(piece_bone)
amesh = bpy.data.meshes.new('added'); add.to_mesh(amesh); add.free()
aobj = bpy.data.objects.new('added', amesh); scene.collection.objects.link(aobj)
aobj.data.materials.append(glow_material())
for poly in aobj.data.polygons:
    poly.use_smooth = False

# ---------------------------------------------------------------- weights
BONE_OF = {0: 'B_Body', 1: 'B_Drill', 2: 'B_Boom', 3: 'B_Sprayer'}
BONE_OF.update({10 + i: f'B_Bucket_R{i}' for i in range(6)})
BONE_OF.update({20 + i: f'B_Bucket_L{i}' for i in range(6)})
groups = {}
for vi, p in enumerate(vpart):
    name = BONE_OF[int(p)]
    g = groups.get(name) or body.vertex_groups.new(name=name)
    groups[name] = g
    g.add([vi], 1.0, 'REPLACE')
agroups = {}
for poly, bone in zip(aobj.data.polygons, piece_bone):
    agroups.setdefault(bone, set()).update(poly.vertices)
for bone, verts in agroups.items():
    g = aobj.vertex_groups.get(bone) or aobj.vertex_groups.new(name=bone)
    g.add(sorted(verts), 1.0, 'REPLACE')
select_only([body, aobj], body)
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = MESH
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='SHORT_EDGE')
bm.to_mesh(body.data); bm.free()
if 'part' in body.data.attributes:
    body.data.attributes.remove(body.data.attributes['part'])

# ---------------------------------------------------------------- rig
bucket_rest = {}
for p, name in BONE_OF.items():
    if p >= 10:
        pts = co[vpart == p]
        bucket_rest[name] = Vector(((pts.min(0) + pts.max(0)) / 2).tolist())
arm_data = bpy.data.armatures.new('Rig')
rig = bpy.data.objects.new('Rig', arm_data)
scene.collection.objects.link(rig)
select_only([rig])
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name); b.head, b.tail = Vector(head), Vector(tail)
    if parent:
        b.parent = eb[parent]
    b.use_deform = deform
    return b


bone('B_Root', (0, 0, 0), (0, 0, 0.5))
bone('B_Body', (0, 0, 0), (0, -0.5, 0), 'B_Root')
bone('B_Boom', HINGE, HINGE + Vector((0, -0.5, 0)), 'B_Body')
drill_start = Vector((0, -3.47, drill_axis.z))
bone('B_Drill', drill_start, drill_start + Vector((0, -0.5, 0)), 'B_Boom')
bone('B_Sprayer', SPRAYER_BASE, SPRAYER_BASE + Vector((0, 0, 0.4)), 'B_Body')
for side, hull in VENT_HULL.items():
    c = np.array(hull).mean(0)
    at = Vector((c[0], vent_plane_y(c[1]) + VENT_INSET + VENT_HIDE, c[1]))
    bone(f'B_Vent_{side}', at, at + Vector((0, -0.3, 0)), 'B_Body')
for name, c in bucket_rest.items():
    bone(name, c, c + Vector((0, 0, 0.25)), 'B_Body')
for name, (tip, parent) in sockets.items():
    bone(name, tip, tip + Vector((0, 0.1, 0)), parent, deform=False)
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = rig
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig


def rot(bone_name, axis, degrees):
    """A rotation about a world axis (rest pose) as the bone's local pose quaternion."""
    rest = rig.data.bones[bone_name].matrix_local.to_3x3()
    local_axis = (rest.inverted() @ Vector(axis)).normalized()
    return Quaternion(local_axis, math.radians(degrees))


def move(bone_name, world):
    rest = rig.data.bones[bone_name].matrix_local.to_3x3()
    return rest.inverted() @ Vector(world)


def pose(body_z=0.0, body_y=0.0, pitch=0.0, roll=0.0, boom=0.0, drill=0.0, spray_yaw=0.0, spray_pitch=0.0,
         vents=0.0, belt=None):
    """pitch + = nose down (degrees, about +x at the ground centre); roll + = left side up (about -y); boom + = drill
    down; drill = spin angle; spray_yaw + = nozzle toward the right flank; spray_pitch + = nozzle down; vents 0..1
    open; belt = conveyor phase 0..1 (None: buckets at rest)."""
    p = {}
    # a tracked machine rocks on its contact patch: after the tilt (about the ground centre) the hull is moved up or
    # down so its lowest bottom vertex stays at its rest height (no sinking into the floor, no floating)
    world = (Quaternion((1, 0, 0), math.radians(pitch)) @ Quaternion((0, -1, 0), math.radians(roll))).to_matrix()
    low = (BOTTOM @ np.array(world).T)[:, 2].min()
    keep = Vector((0.0, 0.0, BOTTOM_REST - low))
    p['B_Body'] = (rot('B_Body', (1, 0, 0), pitch) @ rot('B_Body', (0, -1, 0), roll),
                   move('B_Body', keep + Vector((0, body_y, body_z))), Vector((1, 1, 1)))
    p['B_Boom'] = (rot('B_Boom', (1, 0, 0), boom), Vector(), Vector((1, 1, 1)))
    p['B_Drill'] = (rot('B_Drill', (0, -1, 0), drill), Vector(), Vector((1, 1, 1)))
    p['B_Sprayer'] = (rot('B_Sprayer', (0, 0, 1), spray_yaw) @ rot('B_Sprayer', (1, 0, 0), spray_pitch),
                      Vector(), Vector((1, 1, 1)))
    p['B_Vent_L'] = (Quaternion(), move('B_Vent_L', (0, -VENT_HIDE * vents, 0)), Vector((1, 1, 1)))
    p['B_Vent_R'] = (Quaternion(), move('B_Vent_R', (0, -VENT_HIDE * vents, 0)), Vector((1, 1, 1)))
    if belt is not None:
        for name in bucket_rest:
            i = int(name[-1])
            s = 1.0
            if i == 0:
                s = smooth(min(belt / 0.35, 1.0))          # the front bucket rises out of the housing
            if i == 5:
                s = 1.0 - smooth(max((belt - 0.65) / 0.35, 0.0))  # the rear bucket drops into the hopper
            dz = -0.25 * (1 - s)
            p[name] = (Quaternion(), move(name, (0, BUCKET_STEP * belt, dz)), Vector((s, s, s)))
    return p


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ramp(f, f0, f1):
    return smooth((f - f0) / (f1 - f0))


def key(action, frame, poses):
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        q, loc, sc = poses.get(pb.name, (Quaternion(), Vector(), Vector((1, 1, 1))))
        pb.rotation_quaternion, pb.location, pb.scale = q, loc, sc
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)
        pb.keyframe_insert('scale', frame=frame)


def clip(name, frames, fn):
    action = bpy.data.actions.new(name); action.use_fake_user = True
    for f in range(frames + 1):
        key(action, f, fn(f))
    action.use_frame_range = True
    action.frame_start, action.frame_end = 0, frames
    return action


rig.animation_data_create()
TAU = 2 * math.pi


def rumble(f, amp=1.0):
    return dict(body_z=amp * 0.008 * math.sin(TAU * f / 15), pitch=amp * 0.25 * math.sin(TAU * f / 30 + 1.0),
                roll=amp * 0.2 * math.sin(TAU * f / 20))


# Standing (4 s): idle rumble, the drill turning over (two turns), the sprayer sweeping outboard
clip('Standing', 120, lambda f: pose(**rumble(f * 2, 0.6), drill=720 * f / 120,
                                     spray_yaw=12.5 - 12.5 * math.cos(TAU * f / 120)))
# Walking (2 s): grinding forward, the drill at a turn a second, the buckets one step rearward
clip('Walking', 60, lambda f: pose(**rumble(f * 2), drill=720 * f / 60, belt=f / 60,
                                   spray_yaw=6 - 6 * math.cos(TAU * f / 60)))


def attack(f):                                           # melee: wind back, lunge the drill, return (impact 0.6 s)
    back, lunge, ret = ramp(f, 0, 10), ramp(f, 10, 18), ramp(f, 24, 45)
    w = back * (1 - lunge)
    a = lunge * (1 - ret)
    return pose(body_y=0.10 * w - 0.40 * a, pitch=-1.0 * w + 1.8 * a, boom=-5 * w + 14 * a,
                drill=720 * f / 45)


clip('Attack', 45, attack)


def spray(f):                                            # ranged / cast: swing outboard, kick, back (release 0.6 s)
    out, ret = ramp(f, 0, 14), ramp(f, 28, 45)
    kick = math.exp(-((f - 18) / 3.0) ** 2)
    r = rumble(f * 2, 0.5)
    r['body_z'] += 0.01 * kick
    return pose(**r, spray_yaw=55 * out * (1 - ret) + 4 * kick, spray_pitch=-6 * kick, drill=360 * f / 45)


clip('Spray', 45, spray)


def dig(f):                                              # 8 s: drill down into the floor, vents open, grind, back up
    down, up = ramp(f, 0, 36), ramp(f, 204, 240)
    vents = ramp(f, 15, 45) * (1 - ramp(f, 195, 225))
    shake = down * (1 - up)
    spin = 360 * (f / 30) * 1.0 + 180 * (f / 30) * shake   # speeds up while it bites
    return pose(boom=26 * shake, vents=vents, pitch=1.2 * shake + 0.3 * shake * math.sin(TAU * f / 9),
                roll=0.4 * shake * math.sin(TAU * f / 7), body_z=-0.005 * shake * (1 + math.sin(TAU * f / 5)),
                drill=spin)


clip('Dig', 240, dig)


def hit(f):
    k = math.exp(-((f - 3) / 3.0) ** 2) * math.cos(TAU * (f - 3) / 10)
    return pose(pitch=-0.9 * k, roll=1.2 * k, drill=90 * f / 15)


clip('Hit', 15, hit)


def death_pose(f):
    jolt = math.exp(-((f - 4) / 3.0) ** 2)
    sag, slump, vent = ramp(f, 10, 60), ramp(f, 12, 55), ramp(f, 30, 60)
    settle = math.sin(TAU * max(f - 60, 0) / 24) * math.exp(-max(f - 60, 0) / 10) * (f > 60)
    t = min(f, 60) / 30.0                                # the drill spins down to a stop in 2 s
    spin = 360 * (t - t * t / 4)
    return pose(pitch=-1.5 * jolt + 2.0 * sag + 0.2 * settle, roll=1.0 * jolt + 3.5 * sag,
                boom=20 * slump, spray_yaw=30 * sag, spray_pitch=25 * slump, vents=0.5 * vent, drill=spin)


clip('Death', 90, death_pose)
clip('Dead', 30, lambda f: death_pose(90))
for action in bpy.data.actions:
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- LODs (collapse on copies; UVs, weights kept)
# As the turrets: each LOD copy is welded first (positions only), loses the pieces smaller than DROP_BELOW (bolts,
# rivets, small brackets), then collapses to its share of LOD0's triangles. The added pieces (glow material) are
# kept whole: they are few triangles and must keep their shapes.
bodies = [body]
lod0_tris = tris(body)
for level, (ratio, drop) in enumerate(zip(LOD_RATIOS, DROP_BELOW), 1):
    lod = body.copy(); lod.data = body.data.copy(); scene.collection.objects.link(lod)
    lod.name = lod.data.name = f'{MESH}_LOD{level}'
    bm = bmesh.new(); bm.from_mesh(lod.data)
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if all(f.material_index == 0 for f in v.link_faces)],
                             dist=1e-5)
    if drop:
        seen, small = set(), []
        for v in bm.verts:
            if v in seen:
                continue
            stack, comp = [v], []
            seen.add(v)
            while stack:
                w = stack.pop(); comp.append(w)
                for e in w.link_edges:
                    u = e.other_vert(w)
                    if u not in seen:
                        seen.add(u); stack.append(u)
            if any(f.material_index == 1 for w in comp for f in w.link_faces):
                continue
            pts = np.array([w.co[:] for w in comp])
            if (pts.max(0) - pts.min(0)).max() < drop:
                small.extend(comp)
        bmesh.ops.delete(bm, geom=small, context='VERTS')
    bm.to_mesh(lod.data); bm.free()
    select_only([lod])
    glow_verts = {vi for poly in lod.data.polygons if poly.material_index == 1 for vi in poly.vertices}
    reduce = lod.vertex_groups.new(name='_reduce')      # weight 0 on the added pieces: the collapse leaves them
    reduce.add([v.index for v in lod.data.vertices if v.index not in glow_verts], 1.0, 'REPLACE')
    reduce.add(sorted(glow_verts), 0.0, 'REPLACE')
    m = lod.modifiers.new('collapse', 'DECIMATE'); m.decimate_type = 'COLLAPSE'
    m.ratio = min(1.0, ratio * lod0_tris / max(tris(lod), 1)); m.use_collapse_triangulate = True
    m.vertex_group = '_reduce'; m.vertex_group_factor = 1000.0
    bpy.ops.object.modifier_move_to_index(modifier='collapse', index=0)
    bpy.ops.object.modifier_apply(modifier='collapse')
    lod.vertex_groups.remove(lod.vertex_groups['_reduce'])
    bodies.append(lod)
lod_tris = [tris(o) for o in bodies]
print('LOD_TRIS', lod_tris)

standing = bpy.data.actions['Standing']
rig.animation_data.action = standing
if len(standing.slots):
    rig.animation_data.action_slot = standing.slots[0]
select_only([body, rig], rig)
out = os.path.join(HERE, 'export', f'{OUTNAME}_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
select_only(bodies[1:] + [rig], rig)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'export', f'{OUTNAME}_authored_lods.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_animations=False, export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False,
                          export_image_format='AUTO')
co_all = np.array([v.co[:] for v in body.data.vertices])
info = {'glb': out, 'mesh': MESH, 'tris': lod_tris[0], 'lod_tris': lod_tris, 'added_faces': added_faces,
        'bounds': [co_all.min(0).round(3).tolist(), co_all.max(0).round(3).tolist()],
        'hinge': list(HINGE), 'sprayer_base': list(SPRAYER_BASE), 'core_slots': slot_hits,
        'sockets': {k: list(v[0]) for k, v in sockets.items()},
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', f'{OUTNAME}_info.json'), 'w'), indent=1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'export', f'{OUTNAME}.blend'))
print('EXPORTED', json.dumps(info))
