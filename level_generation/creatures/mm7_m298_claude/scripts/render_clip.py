"""Clay renders of one clip every STEP frames (or the bind pose for clip REST): front, side and three-quarter
cameras 12 degrees above level (about the native sprite camera), a floor plane at z = 0, written to
review/<tag>/f_NN_<view>.png; scripts/sheet.py joins them. Args: -- <blend> <clip|REST> <tag> [step] [ortho scale]"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, clip, tag = a[:3]
step = int(a[3]) if len(a) > 3 else 2
scale = float(a[4]) if len(a) > 4 else 1.6
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
arm = bpy.data.objects['Ooze_Rig']
arm.animation_data_create()
sc = bpy.context.scene
if clip == 'REST':
    arm.animation_data.action = None
    for b in arm.pose.bones:
        b.matrix_basis.identity()
    frames = [0]
else:
    act = bpy.data.actions[clip]
    arm.animation_data.action = act
    if getattr(act, 'slots', None) and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames = list(range(f0, f1 + 1, step))
    if frames[-1] != f1:
        frames.append(f1)
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.55, 0.62, 0.5)
fl = bpy.data.meshes.new('floor')
fl.from_pydata([(-3, -3, -0.001), (3, -3, -0.001), (3, 3, -0.001), (-3, 3, -0.001)], [], [(0, 1, 2, 3)])
flo = bpy.data.objects.new('floor', fl)
sc.collection.objects.link(flo)
flo.color = (0.3, 0.3, 0.3, 1)
out = os.path.join(common.REVIEW, tag)
os.makedirs(out, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y = 360, 300
el = math.radians(12)
for f in frames:
    sc.frame_set(f)
    for view, az in (('front', 0.0), ('side', 90.0), ('three_quarter', 35.0)):
        r = math.radians(az)
        d = 6.0
        loc = (math.sin(r) * d * math.cos(el), -math.cos(r) * d * math.cos(el), 0.35 + d * math.sin(el))
        cam = common.ortho_camera('c', loc, (math.radians(90) - el, 0, r), scale)
        sc.camera = cam
        sc.render.filepath = os.path.join(out, f'f_{f:03d}_{view}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
print('RENDERED', tag, frames)
