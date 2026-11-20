"""Render a GLB or .blend (optionally posed at an action/time) from several views with Eevee.

Usage (Blender): render_views.py <in.glb|in.blend> <out_prefix> [--action NAME --time SECONDS] [--size 900]
    [--views front,back,left,right,quarter] [--ortho] [--hide NAME,...] [--variant NAME]
Views: front = from -Y (the model faces -Y), quarter = front-left three-quarter, slightly from below.
Writes <out_prefix>_<view>.png."""
import bpy, sys, math, argparse
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--action'); ap.add_argument('--time', type=float, default=0.0)
ap.add_argument('--size', type=int, default=900)
ap.add_argument('--views', default='front,back,left,right,quarter')
ap.add_argument('--ortho', action='store_true')
ap.add_argument('--hide', default='')
ap.add_argument('--bg', default='0.30,0.31,0.34')
ap.add_argument('--fps', type=float, default=48.0)
ap.add_argument('--zoom', type=float, default=1.0)
ap.add_argument('--center', default='')
a = ap.parse_args(argv)

if a.src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=a.src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a.src)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)
hide = [h for h in a.hide.split(',') if h]
rigs = [o for o in sc.objects if o.type == 'ARMATURE']
for rig in rigs:
    rig.animation_data_create()
    if a.action:
        act = bpy.data.actions[a.action]
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        for t in rig.animation_data.nla_tracks:
            t.mute = True
        f = a.time * a.fps
        sc.render.fps = int(a.fps)
        sc.frame_set(int(math.floor(f)), subframe=f % 1)
    else:
        rig.animation_data.action = None
        for b in rig.pose.bones:
            b.matrix_basis.identity()
bpy.context.view_layer.update()
meshes = [o for o in sc.objects if o.type == 'MESH' and o.visible_get()
          and not any(k in o.name or k in o.data.name for k in ('LOD', 'Shadow', 'Icosphere'))
          and not any(h in o.name for h in hide)]
for o in sc.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.evaluated_get(dg).data.vertices])
                     for o in meshes])
lo, hi = co.min(0), co.max(0)
c = Vector((lo + hi) / 2); ext = float(np.linalg.norm(hi - lo)) / a.zoom
if a.center:
    c = Vector([float(x) for x in a.center.split(',')])
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
bg = [float(x) for x in a.bg.split(',')]
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*bg, 1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sc.render.resolution_x = sc.render.resolution_y = a.size
sc.render.film_transparent = False
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.2; sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN'))
fill.data.energy = 1.0; sc.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(150))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'front': Vector((0, -1, 0.0)), 'back': Vector((0, 1, 0.0)), 'left': Vector((1, 0, 0.0)),
        'right': Vector((-1, 0, 0.0)), 'quarter': Vector((0.62, -0.78, -0.12)),
        'quarter_back': Vector((-0.62, 0.78, 0.1)), 'top': Vector((0.0, -0.3, 1.0))}
for view in a.views.split(','):
    d = dirs[view].normalized()
    if a.ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(max(hi - lo)) * 1.08 / a.zoom
        cam.location = c + d * ext * 2
    else:
        cam.data.type = 'PERSP'; cam.data.lens = 50
        cam.location = c + d * ext * 1.55
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_end = ext * 10
    sc.render.filepath = f'{a.out}_{view}.png'
    bpy.ops.render.render(write_still=True)
print('RENDERED')
