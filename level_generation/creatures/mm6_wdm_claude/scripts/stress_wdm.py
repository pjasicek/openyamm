"""Stress poses on work/rig_v1.blend: rest (bones), arms raised/forward, legs kicked, spine twist, wings up/down.
Args: out_prefix. Writes <out>_sheet.png (front + three-quarter per pose)."""
import bpy, sys, os, math, subprocess
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Demon_Rig']
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.45, 0.62)
sh.background_type = 'VIEWPORT'; sh.background_color = (0.25, 0.27, 0.3)
sc.render.resolution_x, sc.render.resolution_y = 520, 520
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.3


def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    bpy.context.view_layer.update()


def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = rig.matrix_world @ b.head
    m = rig.matrix_world @ b.matrix
    r = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h)
    b.matrix = rig.matrix_world.inverted() @ (r @ m); bpy.context.view_layer.update()


X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
POSES = {
    'rest': lambda: None,
    'arms_up': lambda: (rot('mixamorig:LeftArm', Y, -70), rot('mixamorig:RightArm', Y, 70),
                        rot('mixamorig:LeftForeArm', Y, -40), rot('mixamorig:RightForeArm', Y, 40)),
    'arms_fwd': lambda: (rot('mixamorig:LeftArm', X, -70), rot('mixamorig:RightArm', X, -70),
                         rot('mixamorig:LeftForeArm', X, -50), rot('mixamorig:RightForeArm', X, -50),
                         rot('mixamorig:LeftHand', X, -30)),
    'legs': lambda: (rot('mixamorig:LeftUpLeg', X, -60), rot('mixamorig:LeftLeg', X, 70),
                     rot('mixamorig:RightUpLeg', X, 25), rot('mixamorig:RightFoot', X, 40)),
    'twist': lambda: (rot('mixamorig:Spine1', Z, 25), rot('mixamorig:Spine2', X, 20), rot('mixamorig:Head', Z, -30)),
    'wings_up': lambda: (rot('Wing_L_Root', Y, -35), rot('Wing_R_Root', Y, 35),
                         rot('Wing_L_Arm', Y, -15), rot('Wing_R_Arm', Y, 15)),
    'wings_down': lambda: (rot('Wing_L_Root', Y, 45), rot('Wing_R_Root', Y, -45),
                           rot('Wing_L_Lead', Y, 15), rot('Wing_R_Lead', Y, -15)),
    'wings_fold': lambda: [rot(f'Wing_{s}_{k}', Z, sg * a) for s, sg in (('L', 1), ('R', -1))
                           for k, a in (('Lead', 50), ('Finger1', 45), ('Finger2', 35), ('Finger3', 20))],
}
cells = []
for name, fn in POSES.items():
    reset(); fn()
    for view, d in (('f', (0, 1, 0.05)), ('q', (-0.7, 0.7, 0.25))):
        d = Vector(d).normalized(); cam.location = Vector((0, 0, 1.15)) - d * 6
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        p = f'{out}_{name}_{view}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', "import sys\nfrom PIL import Image\nims=[Image.open(p) for p in sys.argv[2:]]\n"
                "w,h=ims[0].size\no=Image.new('RGB',(w*4,h*((len(ims)+3)//4)))\n"
                "[o.paste(im,((i%4)*w,(i//4)*h)) for i,im in enumerate(ims)]\no.save(sys.argv[1])",
                out + '_sheet.png'] + cells, check=True)
print('SHEET')
