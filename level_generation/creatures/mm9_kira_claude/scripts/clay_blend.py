"""Clay views of every visible mesh in a blend, one random colour per object; SHOW=name1,name2 limits them; WIRE=1 adds wire. Args: <blend> <out prefix> <view spec ...>"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
show = os.environ.get('SHOW')
for o in sc.objects:
    if o.type == 'MESH': o.hide_render = bool(show) and o.name not in show.split(',')
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR', 'OBJECT' if False else 'RANDOM'); sh.show_cavity = True; sh.show_backface_culling = bool(os.environ.get('CULL'))
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SIZE', 700))
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.05, 0.25)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
if os.environ.get('POSE'):
    arm = next(o for o in sc.objects if o.type == 'ARMATURE')
    name, fr = os.environ['POSE'].split('@'); act = bpy.data.actions[name]
    if not arm.animation_data: arm.animation_data_create()
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(int(float(fr)))
for sp in a[2:]:
    n, d, c, z = sp.split(':')
    d = Vector([float(x) for x in d.split(',')]).normalized(); c = Vector([float(x) for x in c.split(',')])
    cd.ortho_scale = float(z); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
print('CLAY done')
