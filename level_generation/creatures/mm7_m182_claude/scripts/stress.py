"""Stress poses on the fresh rig: rest, wings up, wings down + swept, neck turn + jaw open, legs tucked, tail curl.
Renders review/stress/<pose>_<view>.png (workbench, material colours by texture domain)."""
import bpy, math, sys
from pathlib import Path
from mathutils import Quaternion, Vector
P = Path(__file__).resolve().parents[1]
blend = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else str(P / 'work/rig_v1.blend')
bpy.ops.wm.open_mainfile(filepath=blend)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
axes = {n: b.matrix_local.to_3x3().inverted() for n, b in rig.data.bones.items()}
def reset():
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
def rot(n, axis, a):
    pb = rig.pose.bones[n]; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(axes[n] @ Vector(axis), a)
poses = {
    'rest': [],
    'wings_up': [(s + 'Wing0', (0, 1, 0), g * -.55) for s, g in (('L', 1), ('R', -1))] + [(s + 'Wing2', (0, 1, 0), g * -.25) for s, g in (('L', 1), ('R', -1))],
    'wings_down': [(s + 'Wing0', (0, 1, 0), g * .75) for s, g in (('L', 1), ('R', -1))] + [(s + 'Wing0', (0, 0, 1), g * .35) for s, g in (('L', 1), ('R', -1))] + [(s + 'Wing2', (0, 1, 0), g * .35) for s, g in (('L', 1), ('R', -1))],
    'neck_jaw': [('Neck1', (0, 0, 1), .25), ('Neck2', (0, 0, 1), .25), ('Neck3', (1, 0, 0), -.3), ('Jaw', (1, 0, 0), .55)],
    'legs': [(s + 'ForeUpper', (1, 0, 0), -.6) for s in 'LR'] + [(s + 'ForeLower', (1, 0, 0), .5) for s in 'LR'] + [(s + 'HindUpper', (1, 0, 0), .6) for s in 'LR'] + [(s + 'HindLower', (1, 0, 0), -.4) for s in 'LR'],
    'tail': [(f'Tail{i}', (0, 0, 1), .15) for i in range(1, 11)] + [(f'Tail{i}', (1, 0, 0), .06) for i in range(4, 11)],
}
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True; sc.render.resolution_x = 900; sc.render.resolution_y = 700; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('StressCam', bpy.data.cameras.new('StressCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.35; target = Vector((0, -.05, .32))
out = P / 'review/stress'; out.mkdir(parents=True, exist_ok=True)
for name, ops in poses.items():
    reset()
    for n, axis, a in ops: rot(n, axis, a)
    bpy.context.view_layer.update()
    for view, d in [('quarter', (1, -1, .45)), ('front', (0, -1, .1)), ('side', (1, 0, .1))]:
        cam.location = target + Vector(d).normalized() * 3; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(out / f'{name}_{view}.png'); bpy.ops.render.render(write_still=True)
print('STRESS done')
