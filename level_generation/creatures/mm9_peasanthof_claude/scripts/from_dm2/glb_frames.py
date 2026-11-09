"""Textured renders of a runtime GLB at given clip times (party eye height front, side, three-quarter, hand close-ups).

Args: -- <glb> <out png> <clip:frame48[,clip:frame48...]> [views: front,side,q34,back,handL,handR] [hand token L,R]
One row per clip:frame, one column per view; Workbench studio light with the GLB's own textures, linear keys."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items = a[0], a[1], a[2].split(',')
views = (a[3] if len(a) > 3 else 'front,side,q34').split(',')
toks = (a[4] if len(a) > 4 else ' L , R ').split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 420
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.55, 0.58, 0.62)
sc.render.fps = 48
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'
tiles = []
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(out)), '_frames_tmp'), exist_ok=True)
for it in items:
    clip, f = it.split(':')
    act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    # glTF import keys at the scene rate (24 by default when imported): map 48 fps frames to seconds
    t = float(f) / 48.0
    fps_imp = 24.0
    sc.frame_set(int(t * fps_imp), subframe=(t * fps_imp) % 1.0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    P = np.array([tuple(rig.matrix_world @ b.head) for b in rig.pose.bones])      # bone heads: robust framing
    lo, hi = P.min(0) - 0.12, P.max(0) + 0.12; lo[2] = min(lo[2], 0.0); c = (lo + hi) / 2; hgt = hi[2] - lo[2]
    row = []
    for v in views:
        if v.startswith('hand'):
            tok = toks[0] if v == 'handL' else toks[1]
            hb = next(b for b in rig.pose.bones if tok in b.name and b.name.endswith('Hand'))
            p = rig.matrix_world @ hb.head; q = rig.matrix_world @ hb.tail
            tgt = p + (q - p).normalized() * 0.06; cd.ortho_scale = 0.32
            cam.location = tgt + Vector((0, -0.6, 0.15))
        else:
            ang = {'front': 0, 'side': 90, 'q34': 35, 'back': 180, 'rside': -90, 'lowback': 160, 'lowside': 100}[v]   # low*: from knee height up (2026-11-04)
            r = math.radians(ang); tgt = Vector((c[0], c[1], lo[2] + hgt * 0.55))
            cd.ortho_scale = max(hgt, hi[0] - lo[0], hi[1] - lo[1]) * 1.1
            cam.location = tgt + Vector((math.sin(r) * 4, -math.cos(r) * 4, -1.6 if v.startswith('low') else 0.3))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fn = os.path.join(os.path.dirname(os.path.abspath(out)), '_frames_tmp', f'{os.path.basename(out)}_{len(tiles)}_{len(row)}.png')
        sc.render.filepath = fn; bpy.ops.render.render(write_still=True); row.append(fn)
    tiles.append((it, row))
import subprocess
sys.stdout.flush()
open(out + '.list', 'w').write('\n'.join(it + '\t' + '\t'.join(r) for it, r in tiles))
print('FRAMES', out, len(tiles))
