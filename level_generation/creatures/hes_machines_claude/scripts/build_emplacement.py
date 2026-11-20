"""10140 Test Emplacement: the great ion cannon (hes_ion_cannon_codex/export/hes_great_cannon.glb, its rest state;
snapshot work/emplacement/great_cannon_source.glb, hash in the README) at SCALE on its own round turntable base,
rigged as a turret. No new geometry or Meshy job (CREATURE_BUILDS.md: reuse the cannon's geometry).

SCALE makes the 50 m head 6 m long (THE_CROWN.md's build table: "barrel 600" on a plinth of radius 300; the base
comes out 3.7 m across, 3 m tall in all). Parts by welded component at the source scale: base (max z <= 5.0 m) and
yoke (the rest below the head) on B_Root, the head (min z >= 8.4 m) on B_Barrel, which pitches about PIVOT (the
yoke arms' tops). The source's glow zones (materials GC_breech, GC_pods, GC_ring1..4, GC_muzzle) become three layers
on the head, switched by bone scale like the cell's (build_machine.py):
  dim  (B_Dim)   the zones as they are, HS_TestEmplacement_Energy (the cannon's resting violet, set_glow.py)
  dark (B_Dark)  a copy 3 mm inside, HS_TestEmplacement_Dark (out: Death, Dead)
  hot  (B_HotBreech, B_HotPods, B_HotRings, B_HotMuzzle) copies 3 mm outside, HS_TestEmplacement_Hot (white-violet):
        the Attack wind-up lights them in the great cannon's order (breech core, pods, rings, muzzle crown), the
        shot at frame 24 (0.8 s), then they go out.
Socket_Muzzle at the muzzle crown. Clips at 30 fps: Standing 6 s, Attack 1.0 s, Hit 0.4 s, Death 1.2 s, Dead 1 s.
Writes export/hes_test_emplacement_lod0.glb, .blend, _info.json."""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

NAME, MESH = 'test_emplacement', 'TestEmplacement'
SOURCE = os.path.join(HERE, 'work', 'emplacement', 'great_cannon_source.glb')
SCALE = 6.0 / 50.05
BASE_TOP, HEAD_BOTTOM = 5.0, 8.4                   # source metres
PIVOT = Vector((0.0, 10.0, 12.5))                  # source metres: the yoke arms' tops
MUZZLE = Vector((0.049, -31.95, 11.505))           # source metres (hes_ion_cannon_codex README: the muzzle axis)
ZONES = {'GC_breech': 'B_HotBreech', 'GC_pods': 'B_HotPods', 'GC_ring1': 'B_HotRings', 'GC_ring2': 'B_HotRings',
         'GC_ring3': 'B_HotRings', 'GC_ring4': 'B_HotRings', 'GC_muzzle': 'B_HotMuzzle'}
OFFSET = 0.003                                     # runtime metres, the dark (in) and hot (out) copies
FPS = 30

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps, scene.render.fps_base = FPS, 1
bpy.ops.import_scene.gltf(filepath=SOURCE)
src = bpy.data.objects['IonCannon']
for o in list(scene.objects):
    if o is not src:
        bpy.data.objects.remove(o)
src.parent = None
src.data.transform(src.matrix_world); src.matrix_world = Matrix()
mat_names = [m.name for m in src.data.materials]
body_mat = src.data.materials[mat_names.index('Opaque')]
zone_mat = src.data.materials[mat_names.index('GC_breech')]

bm = bmesh.new(); bm.from_mesh(src.data)
weld = bm.copy()
bmesh.ops.remove_doubles(weld, verts=weld.verts, dist=1e-4)
# the weld keeps face order: one label per face from the welded copy
labels = mc.component_labels(weld)
weld.faces.ensure_lookup_table()
face_comp = [labels[f.verts[0].index] for f in weld.faces]
co = np.array([v.co[:] for v in weld.verts])
comp_lo = {c: co[labels == c].min(0) for c in set(labels.tolist())}
comp_hi = {c: co[labels == c].max(0) for c in set(labels.tolist())}
weld.free()
bm.faces.ensure_lookup_table()
head = [comp_lo[face_comp[i]][2] >= HEAD_BOTTOM for i in range(len(bm.faces))]
part = bm.faces.layers.int.new('part')
for f, h in zip(bm.faces, head):
    f[part] = 3 if h else 1

# zone faces: dim stays, dark copy inside, hot copies outside (per zone group)
zone_faces = [f for f in bm.faces if mat_names[f.material_index] in ZONES]
assert all(f[part] == 3 for f in zone_faces), 'a glow zone outside the head'
groups = {f.index: ZONES[mat_names[f.material_index]] for f in zone_faces}
bm.verts.ensure_lookup_table()
for f in zone_faces:
    f[part] = 10                                   # dim
layers = {}


def copy_faces(faces, offset_m, tag):
    dup = bmesh.ops.duplicate(bm, geom=faces)
    new_faces = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    new_verts = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
    normals = {v: v.normal.copy() for v in new_verts}
    for v in new_verts:
        v.co += normals[v] * (offset_m / SCALE)
    for g in new_faces:
        g[part] = tag
    return new_faces


copy_faces(zone_faces, -OFFSET, 11)                # dark
hot_tags = {'B_HotBreech': 20, 'B_HotPods': 21, 'B_HotRings': 22, 'B_HotMuzzle': 23}
for bone, tag in hot_tags.items():
    faces = [f for f in zone_faces if groups[f.index] == bone]
    copy_faces(faces, OFFSET, tag)
bm.transform(Matrix.Scale(SCALE, 4))
bm.to_mesh(src.data); bm.free()
obj = src
obj.name = obj.data.name = MESH


def material(name, base, flat):
    m = base.copy(); m.name = name
    if flat:
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for link in list(bsdf.inputs['Emission Color'].links) + list(bsdf.inputs['Emission Strength'].links):
            m.node_tree.links.remove(link)
    return m


mats = {'body': material('HS_TestEmplacement', body_mat, False),
        'dim': material('HS_TestEmplacement_Energy', zone_mat, True),
        'dark': material('HS_TestEmplacement_Dark', zone_mat, True),
        'hot': material('HS_TestEmplacement_Hot', zone_mat, True)}
obj.data.materials.clear()
for key in ('body', 'dim', 'dark', 'hot'):
    obj.data.materials.append(mats[key])
ptag = np.zeros(len(obj.data.polygons), int); obj.data.attributes['part'].data.foreach_get('value', ptag)
slot = {1: 0, 3: 0, 10: 1, 11: 2, 20: 3, 21: 3, 22: 3, 23: 3}
bone_of = {1: 'B_Root', 3: 'B_Barrel', 10: 'B_Dim', 11: 'B_Dark', 20: 'B_HotBreech', 21: 'B_HotPods', 22: 'B_HotRings',
           23: 'B_HotMuzzle'}
for poly, t in zip(obj.data.polygons, ptag):
    poly.material_index = slot[int(t)]
vgroups = {b: obj.vertex_groups.new(name=b) for b in sorted(set(bone_of.values()))}
vbone = {}
for poly, t in zip(obj.data.polygons, ptag):
    for vi in poly.vertices:
        vbone[vi] = bone_of[int(t)]
for vi, b in vbone.items():
    vgroups[b].add([vi], 1.0, 'REPLACE')
obj.data.attributes.remove(obj.data.attributes['part'])
co = np.array([v.co[:] for v in obj.data.vertices])


def centroid(bone):
    idx = [vi for vi, b in vbone.items() if b == bone]
    return Vector(co[idx].mean(0).tolist())


# ---------------------------------------------------------------- rig
arm = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', arm); scene.collection.objects.link(rig)
for o in scene.objects:
    o.select_set(o is rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
pivot = PIVOT * SCALE
root = eb.new('B_Root'); root.head, root.tail = Vector((0, 0, 0)), Vector((0, 0, 0.6))
bar = eb.new('B_Barrel'); bar.head, bar.tail = pivot, pivot + Vector((0, -0.4, 0)); bar.parent = root
for b in ('B_Dim', 'B_Dark') + tuple(hot_tags):
    c = centroid(b) if b in vbone.values() else pivot
    bone = eb.new(b); bone.head, bone.tail = c, c + Vector((0, 0, 0.15)); bone.parent = bar
muzzle = MUZZLE * SCALE + Vector((0, -0.02, 0))
sock = eb.new('Socket_Muzzle'); sock.head, sock.tail = muzzle, muzzle + Vector((0, -0.05, 0))
sock.parent = bar; sock.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
obj.parent = rig
obj.modifiers.new('Armature', 'ARMATURE').object = rig


def local_rotation(bone_name, axis, degrees):
    rest = rig.data.bones[bone_name].matrix_local.to_3x3()
    return Quaternion((rest.inverted() @ Vector(axis)).normalized(), math.radians(degrees))


ON, OFF = 1.0, 0.001


def pose(up=0.0, roll=0.0, lit=True, dead=False, hot=()):
    p = {'B_Barrel': (local_rotation('B_Barrel', (1, 0, 0), -up) @ local_rotation('B_Barrel', (0, 1, 0), roll),
                      Vector(), ON),
         'B_Dim': (Quaternion(), Vector(), ON if lit and not dead else OFF),
         'B_Dark': (Quaternion(), Vector(), ON if dead or not lit else OFF)}
    for b in hot_tags:
        p[b] = (Quaternion(), Vector(), ON if b in hot else OFF)
    return p


def key(action, frame, poses):
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        q, loc, s = poses.get(pb.name, (Quaternion(), Vector(), ON))
        pb.rotation_quaternion, pb.location, pb.scale = q, loc, (s, s, s)
        for path in ('rotation_quaternion', 'location', 'scale'):
            pb.keyframe_insert(path, frame=frame)


def clip(name, keys):
    action = bpy.data.actions.new(name); action.use_fake_user = True
    for frame, p in keys:
        key(action, frame, p)
    action.use_frame_range = True
    action.frame_start, action.frame_end = keys[0][0], keys[-1][0]
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT' if fc.data_path.endswith('scale') else 'LINEAR'


rig.animation_data_create()
B, Pd, R, M = 'B_HotBreech', 'B_HotPods', 'B_HotRings', 'B_HotMuzzle'
clip('Standing', [(0, pose()), (180, pose())])
clip('Attack', [(0, pose()), (6, pose(hot=(B,))), (12, pose(hot=(B, Pd))), (18, pose(hot=(B, Pd, R))),
                (23, pose(hot=(B, Pd, R, M))), (24, pose(up=3, hot=(B, Pd, R, M))), (27, pose(up=1.5)),
                (30, pose())])
clip('Hit', [(0, pose()), (2, pose(up=1.5, roll=1.2, lit=False)), (4, pose(up=-1, roll=-0.8)), (6, pose(up=0.5)),
             (12, pose())])
# the head may dip only a few degrees: below 0 it digs into the yoke arms (review/look_gate_emplacement.json)
slump = dict(up=-4, roll=3)
clip('Death', [(0, pose()), (3, pose(up=2, lit=False)), (6, pose(up=-1)), (9, pose(up=-2, lit=False)),
               (12, pose(up=-2.5)), (15, pose(up=-3, dead=True)), (30, pose(up=-4.3, roll=3.2, dead=True)),
               (36, pose(dead=True, **slump))])
clip('Dead', [(0, pose(dead=True, **slump)), (30, pose(dead=True, **slump))])
rig.animation_data.action = bpy.data.actions['Standing']
if len(bpy.data.actions['Standing'].slots):
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
for o in scene.objects:
    o.select_set(o in (obj, rig))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'hes_test_emplacement_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
co = np.array([v.co[:] for v in obj.data.vertices])
info = {'name': NAME, 'mesh': MESH, 'scale': SCALE, 'tris': sum(len(p.vertices) - 2 for p in obj.data.polygons),
        'height': round(float(co[:, 2].max()), 3), 'radius': round(float(np.hypot(co[:, 0], co[:, 1]).max()), 3),
        'pivot': list(pivot), 'muzzle': list(muzzle), 'zone_faces': len(zone_faces),
        'head_faces': int(sum(head)), 'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'hes_test_emplacement_info.json'), 'w'), indent=1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'export', 'hes_test_emplacement.blend'))
print('EXPORTED', json.dumps(info))
