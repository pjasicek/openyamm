"""Face pre-screen renders of a runtime GLB (EEVEE, the GLB's own maps): one row per clip:frame48, one column per view.
Views: front (close-up), q34 (35 deg), profL / profR (true 90 deg profiles), low34 (30 deg round, 25 deg from below),
party (the party's view: camera 3 m away at 1.7 m eye height on a 1.2 m dwarf, full head and shoulders), earL/earR
(tight ear close-ups), under (under the jaw), back34. The head target is the centre of the head material's vertices at
that pose; the character's facing comes from the head bone's world matrix (bind facing -Y in Blender).
Args: -- <glb> <out png> <items clip:frame48,...> [views] [size 512] [variant name]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items = a[0], a[1], a[2].split(',')
views = (a[3] if len(a) > 3 else 'front,q34,profL,profR,low34,party').split(',')
size = int(a[4]) if len(a) > 4 else 512
variant = a[5] if len(a) > 5 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
if variant:
    try:
        bpy.context.scene.gltf2_active_variant = variant
        bpy.ops.wm.gltf2_variant_display(variant_name=variant) if hasattr(bpy.ops.wm, 'gltf2_variant_display') else None
    except Exception as e:
        print('VARIANT', e)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = size
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.32, 0.34, 0.37, 1); bg.inputs['Strength'].default_value = 1.0
for nm, rot, en in (('key', (50, 0, -30), 3.0), ('fill', (60, 0, 140), 1.2)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en
    lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
hb = next(b for b in rig.pose.bones if b.name.endswith('Head'))
# yaw deg (0 front, +90 the character's left side seen), pitch deg (+ from above), ortho m, dz m, perspective distance
V = {'front': (0, 0, 0.26, 0.0), 'q34': (35, 0, 0.28, 0.0), 'profL': (90, 0, 0.30, 0.0), 'profR': (-90, 0, 0.30, 0.0),
     'low34': (30, -25, 0.30, -0.01), 'party': (20, 0, 0, 0), 'earL': (100, 5, 0.12, 0.0), 'earR': (-100, 5, 0.12, 0.0),
     'under': (0, -55, 0.22, -0.03), 'back34': (150, 5, 0.32, 0.0), 'eyes': (0, 0, 0.11, 0.035), 'mouth': (0, 0, 0.11, -0.03),
     'nose_low': (0, -30, 0.11, 0.0)}
os.makedirs('/tmp/face_views', exist_ok=True)
rows = []
for it in items:
    clip, f = it.split(':')
    if clip == 'bind':
        if rig.animation_data: rig.animation_data.action = None
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(clip))
        rig.animation_data_create(); rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        t = float(f) / 48.0
        sc.frame_set(int(t * 24.0), subframe=(t * 24.0) % 1.0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        hm = [i for i, m in enumerate(o.material_slots) if m.material and m.material.name.endswith('Head')]
        vs = set()
        for p in me.polygons:
            if p.material_index in hm: vs.update(p.vertices)
        mw = o.matrix_world
        pts += [mw @ me.vertices[i].co for i in vs]
        ev.to_mesh_clear()
    P = np.array([tuple(p) for p in pts])
    zt = P[:, 2].max()
    head = P[P[:, 2] > zt - 0.30]                 # head + neck, not the hands
    head = head[np.abs(head[:, 0] - np.median(head[:, 0])) < 0.2]
    head = head[np.abs(head[:, 1] - np.median(head[:, 1])) < 0.2]
    c = Vector(((head[:, 0].min() + head[:, 0].max()) / 2, (head[:, 1].min() + head[:, 1].max()) / 2, zt - 0.13))
    hm_ = rig.matrix_world @ hb.matrix
    fwd = Vector((0, -1, 0))
    if clip != 'bind':
        rest = (rig.matrix_world @ rig.data.bones[hb.name].matrix_local).to_3x3()
        fwd = (hm_.to_3x3() @ rest.inverted() @ fwd)
        fwd.z = 0
        fwd.normalize()
    side = fwd.cross(Vector((0, 0, 1)))       # character's left when fwd is -Y? (checked on renders)
    row = []
    for v in views:
        yaw, pitch, ortho, dz = V[v]
        r, p = math.radians(yaw), math.radians(pitch)
        d = (fwd * math.cos(r) + side * math.sin(r)) * math.cos(p) + Vector((0, 0, math.sin(p)))
        if v == 'party':
            cd.type = 'PERSP'; cd.lens = 50
            tgt = c + Vector((0, 0, -0.10)); dist = 3.0
            floor_z = P[:, 2].min() - 0.0
            camz = tgt.z + 1.0                        # about 1.7 m eye height over a dwarf's ~0.95 m chest
            d2 = Vector((d.x, d.y, 0)).normalized() * dist; cam.location = tgt + d2 + Vector((0, 0, camz - tgt.z))
            cd.lens = 200
        else:
            cd.type = 'ORTHO'; cd.ortho_scale = ortho
            tgt = c + Vector((0, 0, dz)); cam.location = tgt + d * 3
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fn = f'/tmp/face_views/{os.getpid()}_{len(rows)}_{len(row)}.png'
        sc.render.filepath = fn; bpy.ops.render.render(write_still=True); row.append(fn)
    rows.append((it, row))
open(out + '.list', 'w').write('\n'.join(it + '\t' + '\t'.join(r) for it, r in rows))
print('FACEVIEWS', out, len(rows))
