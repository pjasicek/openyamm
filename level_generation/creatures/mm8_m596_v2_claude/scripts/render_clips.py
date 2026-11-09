"""Pose sheets of the animated blend: per clip, N evenly spaced times, three-quarter front camera, clay or textured.
Usage: blender -b -P render_clips.py -- <blend> <label> [clip,clip..] [n] [view]  -> review/clips/<label>_<clip>.png"""
import math, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, label = a[0], a[1]
clips = a[2].split(',') if len(a) > 2 and a[2] != 'all' else None
N = int(a[3]) if len(a) > 3 else 8; view = a[4] if len(a) > 4 else 'quarter'
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, blend))
sc = bpy.context.scene; rig = bpy.data.objects['CrystalRig']; body = bpy.data.objects['CrystalWalker']
for o in bpy.data.objects:
    if o.type == 'LIGHT' or o.type == 'CAMERA':
        bpy.data.objects.remove(o)
if not body.data.materials or not body.data.materials[0].use_nodes or 'Image Texture' not in body.data.materials[0].node_tree.nodes:
    mat = bpy.data.materials.new('clay'); mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.75, .55, .66, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
if os.environ.get('RC_NOSPEC'):   # diagnosis: base colour and diffuse only
    for m in body.data.materials:
        b = m.node_tree.nodes.get('Principled BSDF')
        if b:
            for l in list(m.node_tree.links):
                if l.to_socket == b.inputs['Roughness']:
                    m.node_tree.links.remove(l)
            b.inputs['Roughness'].default_value = 1.0; b.inputs['Specular IOR Level'].default_value = 0.0
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = int(os.environ.get('RC_W', 360)); sc.render.resolution_y = int(os.environ.get('RC_H', 420))
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.32, .33, .36, 1)
for ang, en in ((40, 3.2), (210, 1.0)):
    s = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); s.data.energy = en; sc.collection.objects.link(s)
    s.rotation_euler = (math.radians(50), 0, math.radians(ang))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('RC_SCALE', 2.9))
d = {'quarter': Vector((.65, -1, .18)), 'front': Vector((0, -1, .1)), 'side': Vector((1, 0, .1)), 'below': Vector((.35, -1, -.32))}[view].normalized()
c = Vector(tuple(float(x) for x in os.environ.get('RC_CENTRE', '0,-.1,.95').split(','))); cam.location = c + d * 8; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
os.makedirs(os.path.join(P, 'review', 'clips'), exist_ok=True)
clips = clips or [a.name for a in bpy.data.actions if a.use_fake_user]
for clip in clips:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    f0, f1 = act.frame_range
    for k in range(N):
        fr = f0 + (f1 - f0) * k / max(N - 1, 1); sc.frame_set(int(fr), subframe=fr - int(fr))
        sc.render.filepath = os.path.join(P, 'review', 'clips', f'{label}_{clip}_{k:02d}.png')
        bpy.ops.render.render(write_still=True)
