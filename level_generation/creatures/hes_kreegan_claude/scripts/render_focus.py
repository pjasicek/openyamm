"""Clay close-ups around a point (pose as saved). Args: -- <blend> <out_prefix> <x,y,z> <size> [views...]
views: front left back right three_quarter top bottom or az:el (degrees)."""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
c = Vector([float(x) for x in a[2].split(',')]); size = float(a[3]); views = a[4:] or ['front', 'left', 'three_quarter']
sc = bpy.context.scene; common.workbench_clay(sc, os.environ.get('TEX') == '1')
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RES', '500'))
for o in bpy.data.objects:
    if o.name == 'Demon': o.hide_render = True
if os.environ.get('ACTION'):
    rig = bpy.data.objects['Rig']; act = bpy.data.actions[os.environ['ACTION']]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(os.environ.get('FRAME', '0')))
NAMED = {'front': (0, 0), 'left': (90, 0), 'back': (180, 0), 'right': (-90, 0), 'three_quarter': (35, 10), 'top': (0, 89), 'bottom': (0, -89)}
for v in views:
    az, el = NAMED[v] if v in NAMED else [float(x) for x in v.split(':')]
    az, el = math.radians(az), math.radians(el)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam = common.ortho_camera('c', c + d * 4, (0, 0, 0), size)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = f'{a[1]}_{v.replace(":", "_")}.png'
    bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam)
