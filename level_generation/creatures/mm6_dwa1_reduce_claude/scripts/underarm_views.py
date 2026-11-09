"""Close-ups of the right upper arm and armpit (posed midpoint of shoulder and elbow), from the front-below and from
below, textured (EEVEE) and clay. Usage: blender -b -P underarm_views.py -- <glb|blend> <label> <clip> <frame,...>
-> review/arm/<label>_<clip><f>_{front,below}[_clay].png"""
import bpy, sys, os
from mathutils import Vector
src, label, clip, frames = sys.argv[sys.argv.index('--') + 1:][:4]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = os.path.join(HERE, 'review/arm'); os.makedirs(out, exist_ok=True)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
    for o in [o for o in bpy.data.objects if o.type in ('CAMERA', 'LIGHT')]: bpy.data.objects.remove(o)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Body': o.hide_render = True
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.render.resolution_x = sc.render.resolution_y = 500
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.4, 0.42, 0.45, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (2.6, 0.0, 0.3)   # light from below-front so the underside is lit
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
pb = rig.pose.bones
for f in [int(x) for x in frames.split(',')]:
    sc.frame_set(f); M = rig.matrix_world
    S = os.environ.get('ARM_SIDE', 'R'); t = (M @ pb[f'B_{S}_UpperArm'].head + M @ pb[f'B_{S}_Forearm'].head) / 2
    for engine in ('EEVEE', 'WORKBENCH'):
        try: sc.render.engine = 'BLENDER_' + engine + ('_NEXT' if engine == 'EEVEE' else '')
        except TypeError: sc.render.engine = 'BLENDER_' + engine
        if engine == 'WORKBENCH':
            sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
        sgn = -1 if os.environ.get('ARM_SIDE', 'R') == 'L' else 1
        for view, d in (('front', Vector((.15 * sgn, -1, -.45))), ('below', Vector((.25 * sgn, -.35, -1)))):
            cam.location = t + d.normalized() * .6
            cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f"{label}_{clip}{f}_{view}{'_clay' if engine == 'WORKBENCH' else ''}.png")
            bpy.ops.render.render(write_still=True)
