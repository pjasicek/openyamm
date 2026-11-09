"""Head and neck close-ups of a runtime GLB (face defect checks: eyes, lips, neck seam).

Args: -- <glb> <out png> <clip:frame48[,clip:frame48...]> [views: front,rside,lside,q34,eyes,mouth,neckR,neckL]
Views are framed relative to the head bone; eyes/mouth/neck* are tight close-ups (ortho 0.12).
`bind` as the clip renders the rest pose. One row per item, one column per view; EEVEE with the GLB's own maps
(normal map included), camera framed on the head bone. Writes <out png>.list for sheet_frames.py <out png>."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items = a[0], a[1], a[2].split(',')
views = (a[3] if len(a) > 3 else 'front,rside,lside,q34').split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
if os.environ.get('CLAY'):      # diagnostics: base colour unplugged (grey), CLAY=nonormal also drops the normal maps
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None: continue
        for k in ('Base Color',) + (('Normal',) if os.environ['CLAY'] == 'nonormal' else ()):
            for l in list(bsdf.inputs[k].links): nt.links.remove(l)
        bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 360
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.35, 0.37, 0.4, 1); bg.inputs['Strength'].default_value = 1.0
for nm, rot, en in (('key', (50, 0, -30), 3.0), ('fill', (60, 0, 140), 1.2)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en
    lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.ortho_scale = 0.36
hb = next(b for b in rig.pose.bones if b.name.endswith('Head'))
# (camera yaw deg: 0 front, -90 the character's right side; height offset from the head bone m; ortho scale m;
#  optional pitch deg, negative = from below)
VIEWS = {'front': (0, 0.03, 0.3), 'rside': (-90, 0.03, 0.3), 'lside': (90, 0.03, 0.3), 'q34': (35, 0.03, 0.3),
         'back': (180, 0.03, 0.3), 'eyes': (0, 0.1, 0.09), 'mouth': (0, 0.035, 0.09), 'neckR': (-90, 0.0, 0.14),
         'neckL': (90, 0.0, 0.14), 'eyesLow': (10, 0.1, 0.09, -12), 'mouthLow': (-15, 0.035, 0.09, -12)}
rows = []
os.makedirs('/tmp/head_closeups', exist_ok=True)
for it in items:
    clip, f = it.split(':')
    if clip == 'bind':
        if rig.animation_data:
            rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions
                                                                            if x.name.startswith(clip))
        rig.animation_data_create(); rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        t = float(f) / 48.0
        sc.frame_set(int(t * 24.0), subframe=(t * 24.0) % 1.0)
    bpy.context.view_layer.update()
    m = rig.matrix_world @ hb.matrix
    tgt = m.translation - Vector((0, 0, 0.02))
    row = []
    for v in views:
        ang, dz, scale = VIEWS[v][:3]
        r = math.radians(ang); pt = math.radians(VIEWS[v][3] if len(VIEWS[v]) > 3 else 0)
        t = tgt + Vector((0, 0, dz))
        cd.ortho_scale = scale
        cam.location = t + Vector((math.sin(r) * math.cos(pt) * 2, -math.cos(r) * math.cos(pt) * 2, math.sin(pt) * 2))
        cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fn = f'/tmp/head_closeups/{os.getpid()}_{len(rows)}_{len(row)}.png'
        sc.render.filepath = fn; bpy.ops.render.render(write_still=True); row.append(fn)
    rows.append((it, row))
open(out + '.list', 'w').write('\n'.join(it + '\t' + '\t'.join(r) for it, r in rows))
print('CLOSEUPS', out, len(rows))
