"""The machine actors (and the turret's mount decoration) from the textured, split Meshy model.

Reads work/<name>_tex.blend (parts.py, prepare_uv.py, adopt_retexture.py) and textures/<name>* (compose.py). Writes
export/hes_<name>_lod0.glb (LOD0, rig, clips), export/hes_<name>.blend and export/hes_<name>_info.json; the turret
also export/hes_starport_turret_mount.glb (part 0, unskinned, its own 1024x512 maps; atlas v 0..0.5 rescaled).

Old Starport Turret (adapted from hes_turrets_claude/scripts/build_actor_v2.py, the Ward Turret):
  B_Root   ring top centre, not animated (the engine turns the actor): the turntable
  B_Head   same pivot, child of B_Root: the fork yoke and the hub trunnions
  B_Barrel the pitch pivot between the hubs, bone along -y (the `look` node): housing, lens pods, barrel, coil
  B_Recoil child of B_Barrel: the front sleeves, rods and muzzle ring (slides back)
  Socket_Muzzle (child of B_Recoil) at the muzzle. Energy (blue-white, material HS_StarportTurret_Energy): a lens
  disc on each lens pod (Meshy made one on each flank), the muzzle disc, and the exposed coil section of the barrel
  tube (its faces mapped onto compose.py's energy strip). Clips as the Ward: Standing (6 s scan), Attack (0.5 s,
  shot at frame 5 = 0.167 s), Hit, Death (slump), Dead.
Capacitor Column cell and Throne Conduit (one rigid body):
  B_Root   at the floor centre: the body; shudders on Hit and Death
  B_Glow   child: the glowing faces (work/<name>_energy.json; material HS_<Mesh>_Energy, emissiveFactor later)
  B_Dark   child: a copy of the same faces 3 mm inside (material HS_<Mesh>_Dark, the same atlas darkened), the off
           state. The clips switch the two by scale (1 / 0.001): on in Standing, flickering in Hit, going out in
           Death, out in Dead (the column shorted, the conduit cut). Separate offsets keep the LOD weld from merging
           the two copies (hand-built machines lesson, CLAUDE_QUADRUPED_PLAYBOOK.md).
Args: -- <name>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = sys.argv[sys.argv.index('--') + 1]
TURRET = NAME == 'starport_turret'
MESH = {'starport_turret': 'StarportTurret', 'capacitor_column': 'CapacitorCell',
        'throne_conduit': 'ThroneConduit'}[NAME]
OUTNAME = f'hes_{NAME}'
FPS = 30
TEX = os.path.join(HERE, 'textures')
EXPORT = os.path.join(HERE, 'export')
# Turret geometry (metres, work/<name>_tex.blend; scripts/probe_turret.py): the barrel axis (x, z), the muzzle's front,
# the exposed coil between the rear sleeve and the front collar, the lens pods' outer faces.
BARREL_AXIS = (0.005, 1.273)
MUZZLE_Y = -1.372
COIL_Y = (-0.835, -0.555)
COIL_COMPONENT_BOX = ((-0.14, -1.35, 1.05), (0.15, 0.08, 1.36))   # the long barrel tube (component 64)
PODS = [((0.345, 0.0, 1.22), (1, 0, 0)), ((-0.359, -0.05, 1.22), (-1, 0, 0))]
DARK_INSET = 0.003
# The pedestal core: (z, half width) at its foot and its top, inside the panels (mount_holes.py: panels at about
# 0.36-0.58 m from the axis, tapering upward).
CORE_FRUSTUM = ((0.03, 0.50), (0.50, 0.34))
DARK_FACTOR = [0.22, 0.2, 0.26, 1.0]

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_tex.blend'))
scene = bpy.context.scene
scene.render.fps, scene.render.fps_base = FPS, 1
src = bpy.data.objects[NAME]
pivot = Vector(src['pivot']); ring = float(src['ring_top'])


def select_only(objs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = active or objs[0]


def split(obj, keep):
    """A copy of obj with only the faces whose part is in `keep`."""
    me = obj.data.copy()
    bm = bmesh.new(); bm.from_mesh(me)
    layer = bm.faces.layers.int['part']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(obj.name + '_' + '_'.join(map(str, sorted(keep))), me)
    scene.collection.objects.link(o)
    return o


def image(path, colour):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return img


def pbr_material(name, prefix, flat=False, factor=None):
    """Principled material on <prefix>_basecolor/normal/orm (glTF ORM: G roughness, B metallic). flat: base colour
    only (energy and dark copies); factor: a dark copy (rougher here; build_runtime.sh sets its glTF baseColorFactor
    DARK_FACTOR, which the exporter cannot write from a texture node)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage'); base.image = image(prefix + '_basecolor.png', True)
    links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    if flat:
        bsdf.inputs['Roughness'].default_value = 0.4 if not factor else 0.7
        bsdf.inputs['Metallic'].default_value = 0.0
        return mat
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


def remap_v(obj, v0, v1):
    for d in obj.data.uv_layers.active.data:
        d.uv = (d.uv[0], (d.uv[1] - v0) / (v1 - v0))


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def export(objs, rig, path, animations):
    select_only(objs + ([rig] if rig else []), rig or objs[0])
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=animations, export_animation_mode='ACTIONS',
                              export_force_sampling=True, export_frame_step=1, export_skins=rig is not None,
                              export_all_influences=False, export_attributes=False, export_morph=False,
                              export_image_format='AUTO', export_reset_pose_bones=True,
                              export_anim_slide_to_zero=True)


info = {'name': NAME, 'mesh': MESH}
sockets = {}
if TURRET:
    # ------------------------------------------------------------ the mount decoration
    mount = split(src, {0})
    remap_v(mount, 0.0, 0.5)
    mount.name = mount.data.name = f'hes_{NAME}_mount'
    # The pedestal's panels are open shells and one has a V-notch at its foot: a closed core inside them, slightly
    # inset, in the pedestal's navy paint (textures/<name>_mount_core.json: one texel's UV), so nothing shows through.
    core = json.load(open(os.path.join(TEX, f'{NAME}_mount_core.json')))
    bm = bmesh.new(); bm.from_mesh(mount.data)
    uvl_m = bm.loops.layers.uv.active
    (z0, h0), (z1, h1) = CORE_FRUSTUM
    shell = [[bm.verts.new((sx * h, sy * h, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            for z, h in ((z0, h0), (z1, h1))]
    faces = [bm.faces.new(shell[0][::-1]), bm.faces.new(shell[1])]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(bm.faces.new([shell[0][i], shell[0][j], shell[1][j], shell[1][i]]))
    for f in faces:
        f.smooth = False
        for loop in f.loops:
            loop[uvl_m].uv = core['navy_uv']
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    bm.to_mesh(mount.data); bm.free()
    mount.data.materials.clear()
    mount.data.materials.append(pbr_material(f'HS_{MESH}_Mount', os.path.join(TEX, f'{NAME}_mount')))
    select_only([mount])
    bpy.ops.export_scene.gltf(filepath=os.path.join(EXPORT, f'hes_{NAME}_mount.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_animations=False, export_skins=False,
                              export_attributes=False, export_image_format='AUTO')
    info['mount_tris'] = tris(mount)
    bpy.data.objects.remove(mount)
    body = split(src, {1, 2, 3, 4})
    bpy.data.objects.remove(src)
    remap_v(body, 0.5, 1.0)
    prefix = os.path.join(TEX, f'{NAME}_actor')
else:
    body = src
    prefix = os.path.join(TEX, NAME)
body.name = body.data.name = MESH
body.data.materials.clear()
body.data.materials.append(pbr_material(f'HS_{MESH}', prefix))
body.data.materials.append(pbr_material(f'HS_{MESH}_Energy', prefix, flat=True))
if not TURRET:
    body.data.materials.append(pbr_material(f'HS_{MESH}_Dark', prefix, flat=True, factor=DARK_FACTOR))
co = np.array([v.co[:] for v in body.data.vertices])
fpart = np.zeros(len(body.data.polygons), int); body.data.attributes['part'].data.foreach_get('value', fpart)
vpart = np.zeros(len(co), int)
for poly in body.data.polygons:
    for vi in poly.vertices:
        vpart[vi] = fpart[poly.index]

# ---------------------------------------------------------------- energy
energy = bmesh.new()
uvl = energy.loops.layers.uv.new('UVMap')
piece_bone = []
if TURRET:
    swatch = json.load(open(os.path.join(TEX, f'{NAME}_energy_swatch.json')))
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())

    def add_disc(centre, normal, radius, bone, sides=16):
        """A flat disc facing `normal` (an inner ring and a strip cap: no high-valence fan), radial swatch UVs."""
        n = Vector(normal).normalized()
        a = n.orthogonal().normalized(); b = n.cross(a)
        u0, v0, u1, v1 = swatch['disc']
        cu, cv, ru, rv = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2 * 0.95, (v1 - v0) / 2 * 0.95
        rings = []
        for k, rr in enumerate((radius * 0.45, radius)):
            count = sides if k else sides // 2
            rings.append([(energy.verts.new(Vector(centre) + (a * math.cos(2 * math.pi * i / count)
                                                               + b * math.sin(2 * math.pi * i / count)) * rr),
                           (cu + ru * rr / radius * math.cos(2 * math.pi * i / count),
                            cv + rv * rr / radius * math.sin(2 * math.pi * i / count))) for i in range(count)])
        inner, outer = rings
        m = len(inner)
        faces = [inner[::-1]]
        for i in range(sides):
            j = (i + 1) % sides
            ii, jj = (i // 2) % m, ((i + 1) // 2) % m
            quad = [outer[i], outer[j], inner[jj]] + ([inner[ii]] if ii != jj else [])
            faces.append(quad[::-1])
        for f_verts in faces:
            f = energy.faces.new([vv for vv, _ in f_verts])
            for loop, (_, uv) in zip(f.loops, f_verts):
                loop[uvl].uv = uv
            if f.normal.dot(n) < 0:
                f.normal_flip()
            piece_bone.append(bone)

    for centre, normal in PODS:                          # the lens on each pod's outer face
        origin = Vector(centre) + Vector(normal) * 1.0
        loc, nrm, _, _ = bvh.ray_cast(origin, -Vector(normal))
        add_disc(loc + nrm * 0.004, nrm, 0.07, 'B_Barrel')
        info.setdefault('lenses', []).append([round(c, 3) for c in loc])
    ax, az = BARREL_AXIS
    add_disc((ax, MUZZLE_Y - 0.004, az), (0, -1, 0), 0.055, 'B_Recoil')
    sockets['Socket_Muzzle'] = (Vector((ax, MUZZLE_Y - 0.03, az)), 'B_Recoil')
    # the exposed coil: the long barrel tube's faces between the rear sleeve and the front collar, on the strip
    lo, hi = Vector(COIL_COMPONENT_BOX[0]), Vector(COIL_COMPONENT_BOX[1])
    u0, v0, u1, v1 = swatch['strip']
    uv = body.data.uv_layers.active.data
    coil = 0
    for poly in body.data.polygons:
        c = poly.center
        if fpart[poly.index] == 3 and COIL_Y[0] < c.y < COIL_Y[1] and math.hypot(c.x - ax, c.z - az) < 0.15 \
                and all(lo[k] <= c[k] <= hi[k] for k in range(3)):
            poly.material_index = 1; coil += 1
            for li in poly.loop_indices:
                uv[li].uv = (u0 + (u1 - u0) * 0.5, v0 + (v1 - v0) * 0.5)
    info['coil_faces'] = coil
else:
    picked = set(json.load(open(os.path.join(HERE, 'work', f'{NAME}_energy.json'))))
    for poly in body.data.polygons:
        if poly.index in picked:
            poly.material_index = 1
    # the dark copy of the glowing faces, 3 mm inside along the vertex normals, on its own material
    bm = bmesh.new(); bm.from_mesh(body.data)
    glow_faces = [f for f in bm.faces if f.material_index == 1]
    dup = bmesh.ops.duplicate(bm, geom=glow_faces)
    new_faces = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    new_verts = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
    normals = {v: v.normal.copy() for v in new_verts}
    for v in new_verts:
        v.co -= normals[v] * DARK_INSET
    for f in new_faces:
        f.material_index = 2
    bm.to_mesh(body.data); bm.free()
    info['energy_faces'] = len(glow_faces)
info['energy_added_faces'] = len(piece_bone)

# ---------------------------------------------------------------- weights
if TURRET:
    groups = {b: body.vertex_groups.new(name=b) for b in ('B_Root', 'B_Head', 'B_Barrel', 'B_Recoil')}
    BONE_OF = {1: 'B_Root', 2: 'B_Head', 3: 'B_Barrel', 4: 'B_Recoil'}
    for vi, p in enumerate(vpart):
        groups[BONE_OF[p]].add([vi], 1.0, 'REPLACE')
else:
    groups = {b: body.vertex_groups.new(name=b) for b in ('B_Root', 'B_Glow', 'B_Dark')}
    vbone = {}
    for poly in body.data.polygons:
        bone = {0: 'B_Root', 1: 'B_Glow', 2: 'B_Dark'}[poly.material_index]
        for vi in poly.vertices:
            vbone[vi] = bone
    for vi, bone in vbone.items():
        groups[bone].add([vi], 1.0, 'REPLACE')
if piece_bone:
    emesh = bpy.data.meshes.new('energy'); energy.to_mesh(emesh)
    eobj = bpy.data.objects.new('energy', emesh); scene.collection.objects.link(eobj)
    eobj.data.materials.append(body.data.materials[1])
    for poly in eobj.data.polygons:
        poly.use_smooth = False
    egroups = {}
    for poly, bone in zip(eobj.data.polygons, piece_bone):
        egroups.setdefault(bone, set()).update(poly.vertices)
    for bone, verts in egroups.items():
        eobj.vertex_groups.new(name=bone).add(sorted(verts), 1.0, 'REPLACE')
    select_only([body, eobj], body)
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = body.data.name = MESH
energy.free()
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='SHORT_EDGE')
bm.to_mesh(body.data); bm.free()
if 'part' in body.data.attributes:
    body.data.attributes.remove(body.data.attributes['part'])

# ---------------------------------------------------------------- rig
arm_data = bpy.data.armatures.new('Rig')
rig = bpy.data.objects.new('Rig', arm_data)
scene.collection.objects.link(rig)
select_only([rig])
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
co = np.array([v.co[:] for v in body.data.vertices])
height = float(co[:, 2].max())
if TURRET:
    root_pt = Vector((0, 0, ring))
    root = eb.new('B_Root'); root.head, root.tail = root_pt, root_pt + Vector((0, 0, 0.2))
    bhead = eb.new('B_Head'); bhead.head, bhead.tail = root_pt, root_pt + Vector((0, 0, 0.3)); bhead.parent = root
    bbar = eb.new('B_Barrel'); bbar.head, bbar.tail = pivot, pivot + Vector((0, -0.3, 0)); bbar.parent = bhead
    rpt = Vector((BARREL_AXIS[0], -0.9, BARREL_AXIS[1]))
    brec = eb.new('B_Recoil'); brec.head, brec.tail = rpt, rpt + Vector((0, -0.3, 0)); brec.parent = bbar
else:
    root = eb.new('B_Root'); root.head, root.tail = Vector((0, 0, 0)), Vector((0, 0, height * 0.3))
    glow_centre = Vector(co[[vi for vi, b in vbone.items() if b == 'B_Glow']].mean(0).tolist())
    for name in ('B_Glow', 'B_Dark'):
        bone = eb.new(name); bone.head, bone.tail = glow_centre, glow_centre + Vector((0, 0, 0.2)); bone.parent = root
    info['glow_centre'] = [round(c, 3) for c in glow_centre]
for name, (tip, parent) in sockets.items():
    sock = eb.new(name); sock.head, sock.tail = tip, tip + Vector((0, -0.05, 0))
    sock.parent = eb[parent]; sock.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = rig
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig


def local_rotation(bone_name, axis, degrees):
    rest = rig.data.bones[bone_name].matrix_local.to_3x3()
    local_axis = (rest.inverted() @ Vector(axis)).normalized()
    return Quaternion(local_axis, math.radians(degrees))


def key(action, frame, poses):
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        q, loc, s = poses.get(pb.name, (Quaternion(), Vector(), 1.0))
        pb.rotation_quaternion, pb.location, pb.scale = q, loc, (s, s, s)
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)
        pb.keyframe_insert('scale', frame=frame)


def turret_pose(head_yaw=0.0, head_roll=0.0, barrel_up=0.0, recoil=0.0):
    """Head yaw about up and roll about the front axis (B_Head); barrel elevation (+ raises the muzzle) on B_Barrel;
    recoil = metres the front sleeves slide back (B_Recoil, the bone's local -Y)."""
    hq = local_rotation('B_Head', (0, 0, 1), head_yaw) @ local_rotation('B_Head', (0, 1, 0), head_roll)
    bq = local_rotation('B_Barrel', (1, 0, 0), -barrel_up)
    return {'B_Head': (hq, Vector(), 1.0), 'B_Barrel': (bq, Vector(), 1.0),
            'B_Recoil': (Quaternion(), Vector((0, -recoil, 0)), 1.0)}


def cell_pose(tilt_x=0.0, tilt_y=0.0, lit=True):
    """Tilt of the whole body about the floor (degrees, a shudder), the glow on or off (B_Glow / B_Dark scale)."""
    q = local_rotation('B_Root', (1, 0, 0), tilt_x) @ local_rotation('B_Root', (0, 1, 0), tilt_y)
    on, off = 1.0, 0.001
    return {'B_Root': (q, Vector(), 1.0), 'B_Glow': (Quaternion(), Vector(), on if lit else off),
            'B_Dark': (Quaternion(), Vector(), off if lit else on)}


def clip(name, keys, interpolation='LINEAR'):
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create()
    for frame, p in keys:
        key(action, frame, p)
    action.use_frame_range = True
    action.frame_start, action.frame_end = keys[0][0], keys[-1][0]
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        constant = fc.data_path.endswith('scale')
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT' if constant else interpolation
    return action


rig.animation_data_create()
if TURRET:
    P = turret_pose
    clip('Standing', [(f, P(head_yaw=25 * math.sin(2 * math.pi * f / 180), barrel_up=2 * math.sin(2 * math.pi * f / 90)))
                      for f in range(0, 181, 10)], 'BEZIER')
    clip('Attack', [(0, P()), (4, P()), (5, P(barrel_up=4, recoil=0.07)), (9, P(barrel_up=2.5, recoil=0.035)),
                    (15, P())])
    clip('Hit', [(0, P()), (2, P(head_yaw=4, head_roll=2, barrel_up=2)), (4, P(head_yaw=-3, head_roll=-1.5)),
                 (6, P(head_yaw=2, head_roll=1, barrel_up=-1)), (8, P(head_yaw=-1)), (12, P())])
    slump = dict(head_yaw=8, head_roll=5, barrel_up=-15)
    clip('Death', [(0, P()), (3, P(head_yaw=3, barrel_up=3)), (24, P(**slump)),
                   (30, P(head_yaw=8, head_roll=4.5, barrel_up=-13)), (36, P(**slump))])
    clip('Dead', [(0, P(**slump)), (30, P(**slump))])
else:
    P = cell_pose
    # the conduit is twice the cell's height: half the tilt for the same sway at the top
    k = 0.5 if NAME == 'throne_conduit' else 1.0
    clip('Standing', [(0, P()), (180, P())])        # 6 s, as the turret's (one clip list in the viewer)
    clip('Hit', [(0, P()), (2, P(tilt_x=1.6 * k, tilt_y=-0.8 * k, lit=False)), (4, P(tilt_x=-1.0 * k, tilt_y=0.6 * k)),
                 (6, P(tilt_x=0.5 * k, lit=False)), (7, P(tilt_x=0.3 * k)), (12, P())])
    clip('Death', [(0, P()), (2, P(tilt_x=1.5 * k, tilt_y=1.0 * k, lit=False)), (4, P(tilt_x=-1.2 * k, tilt_y=-0.6 * k)),
                   (7, P(tilt_x=1.0 * k, tilt_y=-0.8 * k, lit=False)), (9, P(tilt_x=-0.8 * k)),
                   (12, P(tilt_x=0.6 * k, tilt_y=0.5 * k, lit=False)), (14, P(tilt_x=-0.4 * k)),
                   (16, P(tilt_x=0.3 * k, lit=False)), (24, P(tilt_x=-0.1 * k, lit=False)), (36, P(lit=False))])
    clip('Dead', [(0, P(lit=False)), (30, P(lit=False))])

standing = bpy.data.actions['Standing']
rig.animation_data.action = standing
if len(standing.slots):
    rig.animation_data.action_slot = standing.slots[0]
export([body], rig, os.path.join(EXPORT, f'{OUTNAME}_lod0.glb'), True)
co = np.array([v.co[:] for v in body.data.vertices])
info.update(tris=tris(body), height=round(float(co[:, 2].max()), 3),
            radius=round(float(np.hypot(co[:, 0], co[:, 1]).max()), 3),
            ring=[0, 0, ring], pitch=list(pivot), sockets={k: list(v[0]) for k, v in sockets.items()},
            clips={a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions})
json.dump(info, open(os.path.join(EXPORT, f'{OUTNAME}_info.json'), 'w'), indent=1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(EXPORT, f'{OUTNAME}.blend'))
print('EXPORTED', json.dumps(info))
