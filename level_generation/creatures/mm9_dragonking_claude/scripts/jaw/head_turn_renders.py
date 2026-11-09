"""Orthographic head turnaround renders of the current model (bind pose, textured + clay) as the Codex shape
authority: front, three-quarter (creature's right toward camera), left profile (snout to image LEFT), back.
Args: -- <anim blend> <out dir>"""
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == rig)
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x = sc.render.resolution_y = 1024; sc.render.film_transparent = True
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 1.0
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 1.5
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(30), 0, math.radians(-20))
c = Vector((0, -3.3, 15.75))      # head centre (snout tip y -5.2, frill back -1.5, horns to z 17.4)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 5.4; cd.clip_start = 0.01; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
# creature faces -Y; its left is +X? (MM9 LithTech: check by eye). Profile = snout to image LEFT.
views = {'front': Vector((0, -1, 0)), 'three_quarter': Vector((-0.6, -0.8, 0)), 'profile_left': Vector((1, 0, 0)),
         'profile_right': Vector((-1, 0, 0)), 'back': Vector((0, 1, 0))}
clay = bpy.data.materials.new('clay'); clay.use_nodes = True
cb = next(n for n in clay.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); cb.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1)
orig = [s.material for s in body.material_slots]
for look in ('textured', 'clay'):
    for i, s in enumerate(body.material_slots): s.material = orig[i] if look == 'textured' else clay
    for nm, d in views.items():
        cam.location = c + d * 30; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{nm}_{look}.png'); bpy.ops.render.render(write_still=True)
