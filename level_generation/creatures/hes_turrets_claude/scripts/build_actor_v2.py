"""v2 step 5: the turret actor and its mount decoration from the textured, split Meshy model.

Reads work/<name>_tex.blend (parts.py, prepare_uv.py, adopt_retexture.py) and textures/<name>_* (compose.py). Writes
- the mount decoration (part 0, unskinned, its own 1024x512 maps; atlas v 0..0.5 rescaled to 0..1) to
  level_generation/props/hesper_decorations/work/hard_surface/hes_<name>_mount.glb;
- export/hes_<name>_actor_lod0.glb (LOD0, rig, clips), export/hes_<name>_actor_authored_lods.glb (LOD1..3 on the
  same rig, no clips; scripts/link_lods.py links them), export/hes_<name>_actor.blend, export/..._info.json.

Energy (blue-white emitters, lenses, the Ward's coil): added geometry (discs and a core cylinder, mapped to the
energy swatch compose.py painted) on its own material HS_<Mesh>_Energy; build_runtime.sh gives that material the
glTF emissive factor and texture. Bones (every vertex rigid except the Ward's cable loops):
  B_Root   ring top centre, not animated (the engine turns the actor): the Ward's turntable
  B_Head   same pivot, child of B_Root: the Ward's yoke arm and hubs; the Bastion's column, dome, shoulders, lenses
  B_Barrel the pitch pivot (Ward: the elbow hubs' axis, carrying the whole gun housing, lens pods, pennant and
           shroud; Bastion: inside the dome between the barrels), bone along -y (front) as in v1 (the `look` node)
  B_Recoil Ward only: the barrel cluster, collars, coil and muzzle emitter, child of B_Barrel (slides back)
  Socket_Muzzle (Ward, child of B_Recoil) / Socket_Muzzle_Upper, Socket_Muzzle_Lower (Bastion, children of B_Barrel)
The Ward's two cable loops blend from B_Head to B_Barrel over 0.3 m below the pivot.
Clips at 30 fps as v1: Standing (6 s scan), Attack (0.5 s, shot at frame 5 = 0.167 s), Hit, Death, Dead.
Args: -- <ward_turret|gate_bastion>"""
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
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
NAME = sys.argv[sys.argv.index('--') + 1]
WARD = NAME == 'ward_turret'
MESH = 'WardTurret' if WARD else 'GateBastion'
OUTNAME = f'hes_{NAME}_actor'
MOUNT_OUT = os.path.join(REPO, 'level_generation', 'props', 'hesper_decorations', 'work', 'hard_surface',
                         f'hes_{NAME}_mount.glb')
FPS = 30
LOD_RATIOS = [0.5, 0.25, 0.12]
LENS_X, LENS_Z = (-0.136, -0.024, 0.088), 1.53            # the Bastion's three lenses on its lens bar
FIN_BAND = (-1.635, -1.415)                              # compose.py FIN_BAND (the Bastion)
BARREL_END_Y = -0.20
TEX = os.path.join(HERE, 'textures')
swatch = json.load(open(os.path.join(TEX, f'{NAME}_energy_swatch.json')))

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


def pbr_material(name, prefix, energy=False):
    """Principled material on <prefix>_basecolor/normal/orm (glTF ORM: G roughness, B metallic)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage'); base.image = image(prefix + '_basecolor.png', True)
    links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    if energy:
        bsdf.inputs['Roughness'].default_value = 0.4
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


# The Bastion's barrels end at BARREL_END_Y inside the dome (their textured mesh runs to y -0.05; further back they
# would poke out of the dome's top when pitched down): whole faces behind it are dropped.
if not WARD:
    bm = bmesh.new(); bm.from_mesh(src.data)
    layer = bm.faces.layers.int['part']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] == 3 and f.calc_center_median().y > BARREL_END_Y],
                     context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(src.data); bm.free()

# ---------------------------------------------------------------- the mount decoration
mount = split(src, {0})
remap_v(mount, 0.0, 0.5)
mount.name = mount.data.name = f'hes_{NAME}_mount'
mount.data.materials.clear()
mount.data.materials.append(pbr_material(f'HS_{MESH}_Mount', os.path.join(TEX, f'{NAME}_mount')))
select_only([mount])
bpy.ops.export_scene.gltf(filepath=MOUNT_OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=False, export_attributes=False,
                          export_image_format='AUTO')
mount_tris = tris(mount)

# ---------------------------------------------------------------- the actor body
body = split(src, {1, 2, 3, 4, 5})
bpy.data.objects.remove(src)
remap_v(body, 0.5, 1.0)
body.name = body.data.name = MESH
body.data.materials.clear()
body.data.materials.append(pbr_material(f'HS_{MESH}', os.path.join(TEX, f'{NAME}_actor')))
body.data.materials.append(pbr_material(f'HS_{MESH}_Energy', os.path.join(TEX, f'{NAME}_actor'), energy=True))
co = np.array([v.co[:] for v in body.data.vertices])
vpart = np.zeros(len(co), int)
fpart = np.zeros(len(body.data.polygons), int); body.data.attributes['part'].data.foreach_get('value', fpart)
for poly in body.data.polygons:
    for vi in poly.vertices:
        vpart[vi] = fpart[poly.index]
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())


def front_hit(x, z, y_from=-4.0):
    """First surface along +y from the front at (x, z): location and normal."""
    loc, nrm, _, _ = bvh.ray_cast(Vector((x, y_from, z)), Vector((0, 1, 0)))
    return loc, nrm


# --- energy pieces: (bmesh pieces with their bone); UVs into the swatch
energy = bmesh.new()
uvl = energy.loops.layers.uv.new('UVMap')
piece_bone = []                                         # per energy face: bone name


def add_disc(centre, normal, radius, bone, sides=16):
    """A flat disc facing `normal` (an inner ring and a strip cap: no high-valence fan), radial UVs on the swatch."""
    n = Vector(normal).normalized()
    a = n.orthogonal().normalized(); b = n.cross(a)
    u0, v0, u1, v1 = swatch['disc']
    cu, cv, ru, rv = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2 * 0.95, (v1 - v0) / 2 * 0.95
    rings = []
    for k, rr in enumerate((radius * 0.45, radius)):
        ring_verts = []
        for i in range(sides if k else sides // 2):
            t = 2 * math.pi * i / (sides if k else sides // 2)
            ring_verts.append((energy.verts.new(Vector(centre) + (a * math.cos(t) + b * math.sin(t)) * rr),
                               (cu + ru * rr / radius * math.cos(t), cv + rv * rr / radius * math.sin(t))))
        rings.append(ring_verts)
    faces = []
    inner, outer = rings
    m = len(inner)
    faces.append([vv for vv in inner[::-1]])            # inner polygon (8 sides), triangulated later
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


def add_cylinder(axis_point, y0, y1, radius, bone, sides=12):
    """An open cylinder along y (the barrel axis) from y0 to y1, flat-strip UVs."""
    u0, v0, u1, v1 = swatch['strip']
    rings = [[energy.verts.new((axis_point[0] + radius * math.cos(2 * math.pi * i / sides), y,
                                axis_point[1] + radius * math.sin(2 * math.pi * i / sides))) for i in range(sides)]
             for y in (y0, y1)]
    for i in range(sides):
        j = (i + 1) % sides
        f = energy.faces.new([rings[0][i], rings[0][j], rings[1][j], rings[1][i]])
        for loop, (uu, vv) in zip(f.loops, ((0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8))):
            loop[uvl].uv = (u0 + (u1 - u0) * uu, v0 + (v1 - v0) * vv)
        mid = (f.verts[0].co + f.verts[2].co) / 2
        if f.normal.dot(Vector((mid.x - axis_point[0], 0, mid.z - axis_point[1]))) < 0:
            f.normal_flip()
        piece_bone.append(bone)


sockets = {}
recoil_axis = None
if WARD:
    rec = co[vpart == 4]
    tip = rec[rec[:, 1] < rec[:, 1].min() + 0.12]
    ax, az = float(tip[:, 0].mean()), float(tip[:, 2].mean())
    recoil_axis = (ax, az)
    rods = rec[(rec[:, 1] > -0.8) & (rec[:, 1] < -0.45)]
    inner = float(np.percentile(np.hypot(rods[:, 0] - ax, rods[:, 2] - az), 3))
    add_cylinder((ax, az), -0.98, -0.42, max(inner * 0.92, 0.012), 'B_Recoil')
    ymin = float(rec[:, 1].min())
    add_disc((ax, -1.165, az), (0, -1, 0), 0.07, 'B_Recoil')
    sockets['Socket_Muzzle'] = (Vector((ax, ymin - 0.02, az)), 'B_Recoil')
    print('WARD energy: coil inner radius', round(inner, 4), 'axis', round(ax, 3), round(az, 3), 'tip y', ymin)
else:
    bar = co[vpart == 3]
    ymin = float(bar[:, 1].min())
    front = bar[bar[:, 1] < ymin + 0.03]
    for label, sel in (('Upper', front[:, 2] > 1.78), ('Lower', front[:, 2] <= 1.78)):
        f = front[sel]
        cx, cz = (f[:, 0].min() + f[:, 0].max()) / 2, (f[:, 2].min() + f[:, 2].max()) / 2
        rad = min(f[:, 0].max() - f[:, 0].min(), f[:, 2].max() - f[:, 2].min()) / 2
        loc, _ = front_hit(cx, cz)
        y = loc.y if loc is not None and loc.y < ymin + 0.1 else ymin
        add_disc((cx, y - 0.004, cz), (0, -1, 0), max(rad * 0.75, 0.05), 'B_Barrel')
        sockets[f'Socket_Muzzle_{label}'] = (Vector((cx, y - 0.03, cz)), 'B_Barrel')
        print('BASTION muzzle', label, round(cx, 3), round(cz, 3), 'r', round(rad, 3), 'y', round(y, 3))
    for lx in LENS_X:                                    # the three sensor lenses on the bar under the barrels
        loc, nrm = front_hit(lx, LENS_Z)
        add_disc(loc + nrm * 0.004, nrm, 0.036, 'B_Head', sides=12)
        print('BASTION lens', round(lx, 3), tuple(round(c, 3) for c in loc), tuple(round(c, 2) for c in nrm))
energy_faces = len(piece_bone)
emesh = bpy.data.meshes.new('energy'); energy.to_mesh(emesh); energy.free()
eobj = bpy.data.objects.new('energy', emesh); scene.collection.objects.link(eobj)
eobj.data.materials.append(body.data.materials[1])
for poly in eobj.data.polygons:
    poly.material_index = 0
    poly.use_smooth = False

def energize(select, centre, radius):
    """Faces of the body chosen by select(poly) go to the energy material, their UVs projected from the front
    (x, z about centre, scaled by radius) onto the swatch's radial disc: Meshy's lens and emitter glass glows."""
    u0, v0, u1, v1 = swatch['disc']
    cu, cv, ru, rv = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2 * 0.95, (v1 - v0) / 2 * 0.95
    uv = body.data.uv_layers.active.data
    hit = 0
    for poly in body.data.polygons:
        if not select(poly):
            continue
        poly.material_index = 1; hit += 1
        for li in poly.loop_indices:
            c = body.data.vertices[body.data.loops[li].vertex_index].co
            du = max(-1.0, min(1.0, (c.x - centre[0]) / radius)); dv = max(-1.0, min(1.0, (c.z - centre[1]) / radius))
            uv[li].uv = (cu + ru * du, cv + rv * dv)
    return hit


glass = {}
if WARD:
    for s in (-1, 1):                                    # the lens pods' front lenses (Meshy's faceted glass)
        c = (s * 0.445, 1.2)
        glass[f'pod{s}'] = energize(lambda p, c=c: fpart[p.index] == 3 and p.normal.y < 0.2 and p.center.y < 0.1
                                    and math.hypot(p.center.x - c[0], p.center.z - c[1]) < 0.066, c, 0.066)
    glass['muzzle'] = energize(lambda p: fpart[p.index] == 4 and p.normal.y < -0.3 and p.center.y < -1.12
                               and math.hypot(p.center.x - recoil_axis[0], p.center.z - recoil_axis[1]) < 0.045,
                               recoil_axis, 0.045)
print('GLASS faces', glass)

# the Bastion's fin band (compose.py FIN_BAND) goes to the energy material
fin_faces = 0
if not WARD:
    for poly in body.data.polygons:
        cy = poly.center.y
        if fpart[poly.index] == 3 and FIN_BAND[0] < cy < FIN_BAND[1]:
            poly.material_index = 1; fin_faces += 1
print('ENERGY added faces', energy_faces, 'fin faces', fin_faces)

# ---------------------------------------------------------------- weights
groups = {b: body.vertex_groups.new(name=b) for b in ('B_Root', 'B_Head', 'B_Barrel', 'B_Recoil')}
BONE_OF = {1: 'B_Root', 2: 'B_Head', 3: 'B_Barrel', 4: 'B_Recoil'}
for vi, p in enumerate(vpart):
    if p == 5:                                           # cable loops: B_Head below, B_Barrel near the pivot
        t = min(max((co[vi, 2] - (pivot.z - 0.3)) / 0.3, 0.0), 1.0)
        if t < 1:
            groups['B_Head'].add([vi], 1 - t, 'REPLACE')
        if t > 0:
            groups['B_Barrel'].add([vi], t, 'REPLACE')
    else:
        groups[BONE_OF[p]].add([vi], 1.0, 'REPLACE')
egroups = {}
for poly, bone in zip(eobj.data.polygons, piece_bone):
    egroups.setdefault(bone, set()).update(poly.vertices)
for bone, verts in egroups.items():
    g = eobj.vertex_groups.get(bone) or eobj.vertex_groups.new(name=bone)
    g.add(sorted(verts), 1.0, 'REPLACE')
select_only([body, eobj], body)
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = MESH
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
root_pt = Vector((0, 0, ring))
root = eb.new('B_Root'); root.head, root.tail = root_pt, root_pt + Vector((0, 0, 0.2))
bhead = eb.new('B_Head'); bhead.head, bhead.tail = root_pt, root_pt + Vector((0, 0, 0.3)); bhead.parent = root
bbar = eb.new('B_Barrel'); bbar.head, bbar.tail = pivot, pivot + Vector((0, -0.3, 0)); bbar.parent = bhead
recoil_bone = 'B_Barrel'
if WARD:
    rpt = Vector((recoil_axis[0], -0.4, recoil_axis[1]))
    brec = eb.new('B_Recoil'); brec.head, brec.tail = rpt, rpt + Vector((0, -0.3, 0)); brec.parent = bbar
    recoil_bone = 'B_Recoil'
for name, (tip, parent) in sockets.items():
    if name.startswith('_'):
        continue
    sock = eb.new(name); sock.head, sock.tail = tip, tip + Vector((0, -0.05, 0))
    sock.parent = eb[parent]; sock.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
if not WARD:
    body.vertex_groups.remove(body.vertex_groups['B_Recoil'])
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
        q, loc = poses.get(pb.name, (Quaternion(), Vector()))
        pb.rotation_quaternion, pb.location = q, loc
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)


def pose(head_yaw=0.0, head_roll=0.0, barrel_up=0.0, recoil=0.0):
    """Head yaw about up and roll about the front axis (B_Head); barrel elevation (+ raises the muzzle) on B_Barrel;
    recoil = metres the barrel slides back (B_Recoil on the Ward, B_Barrel on the Bastion; the bones' local -Y)."""
    hq = local_rotation('B_Head', (0, 0, 1), head_yaw) @ local_rotation('B_Head', (0, 1, 0), head_roll)
    bq = local_rotation('B_Barrel', (1, 0, 0), -barrel_up)
    poses = {'B_Head': (hq, Vector()), 'B_Barrel': (bq, Vector())}
    poses[recoil_bone] = (poses.get(recoil_bone, (Quaternion(), Vector()))[0], Vector((0, -recoil, 0)))
    return poses


def clip(name, keys):
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create()
    for frame, p in keys:
        key(action, frame, p)
    action.use_frame_range = True
    action.frame_start, action.frame_end = keys[0][0], keys[-1][0]
    return action


rig.animation_data_create()
clip('Standing', [(f, pose(head_yaw=25 * math.sin(2 * math.pi * f / 180), barrel_up=2 * math.sin(2 * math.pi * f / 90)))
                  for f in range(0, 181, 10)])
clip('Attack', [(0, pose()), (4, pose()), (5, pose(barrel_up=4, recoil=0.07)), (9, pose(barrel_up=2.5, recoil=0.035)),
                (15, pose())])
clip('Hit', [(0, pose()), (2, pose(head_yaw=4, head_roll=2, barrel_up=2)), (4, pose(head_yaw=-3, head_roll=-1.5)),
             (6, pose(head_yaw=2, head_roll=1, barrel_up=-1)), (8, pose(head_yaw=-1)), (12, pose())])
slump = dict(head_yaw=8, head_roll=5, barrel_up=-20)
clip('Death', [(0, pose()), (3, pose(head_yaw=3, barrel_up=3)), (24, pose(**slump)),
               (30, pose(head_yaw=8, head_roll=4.5, barrel_up=-17)), (36, pose(**slump))])
clip('Dead', [(0, pose(**slump)), (30, pose(**slump))])
for action in bpy.data.actions:
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER' if action.name == 'Standing' else 'LINEAR'

# ---------------------------------------------------------------- LODs (collapse on copies; UVs, weights kept)
# The retexture's mesh is split at every UV seam; collapsing it as it is tore the plates into spikes. Each LOD copy is
# welded first (positions only: UV seams stay as split loops), loses the pieces smaller than DROP_BELOW (bolts,
# rivets, tiny brackets: they only become spikes), then collapses to its share of LOD0's triangles.
DROP_BELOW = [0.0, 0.035, 0.07]
bodies = [body]
lod0_tris = tris(body)
for level, (ratio, drop) in enumerate(zip(LOD_RATIOS, DROP_BELOW), 1):
    lod = body.copy(); lod.data = body.data.copy(); scene.collection.objects.link(lod)
    lod.name = lod.data.name = f'{MESH}_LOD{level}'
    bm = bmesh.new(); bm.from_mesh(lod.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
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
            pts = np.array([w.co[:] for w in comp])
            if (pts.max(0) - pts.min(0)).max() < drop:
                small.extend(comp)
        bmesh.ops.delete(bm, geom=small, context='VERTS')
    bm.to_mesh(lod.data); bm.free()
    select_only([lod])
    m = lod.modifiers.new('collapse', 'DECIMATE'); m.decimate_type = 'COLLAPSE'
    m.ratio = min(1.0, ratio * lod0_tris / max(tris(lod), 1)); m.use_collapse_triangulate = True
    bpy.ops.object.modifier_move_to_index(modifier='collapse', index=0)
    bpy.ops.object.modifier_apply(modifier='collapse')
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
info = {'glb': out, 'mesh': MESH, 'tris': lod_tris[0], 'lod_tris': lod_tris, 'mount_tris': mount_tris,
        'mount': MOUNT_OUT, 'ring': [0, 0, ring], 'pitch': list(pivot),
        'sockets': {k: list(v[0]) for k, v in sockets.items() if not k.startswith('_')},
        'energy_added_faces': energy_faces, 'fin_faces': fin_faces, 'glass_faces': glass,
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', f'{OUTNAME}_info.json'), 'w'), indent=1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'export', f'{OUTNAME}.blend'))
print('EXPORTED', json.dumps(info))
