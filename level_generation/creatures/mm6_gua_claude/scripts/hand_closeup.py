"""Large close-ups of chosen clip frames around one hand (camera follows the hand; three views).
Usage: blender --background --python hand_closeup.py -- <clip> <Left|Right> <frame,frame,...> <tag>"""
import bpy, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
clip, side, frames, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v7.blend'))
import gua_rig as gr
gr.set_action(clip)
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
out = os.path.join(common.REVIEW, 'hand_audit', tag)
os.makedirs(out, exist_ok=True)
for f in [int(x) for x in frames.split(',')]:
    sc.frame_set(f)
    h = gr.AW @ gr.B(side + 'Hand').head
    e = gr.AW @ gr.B(side + 'ForeArm').head
    c = h + (e - h) * 0.25
    fa = (h - e).normalized()
    s1 = fa.cross(Vector((0, 0, 1)))
    if s1.length < 0.2:
        s1 = fa.cross(Vector((0, 1, 0)))
    s1.normalize()
    s2 = s1.cross(fa).normalized()
    for t, d in (('a', s1), ('b', s2), ('c', -s1)):
        cam = common.ortho_camera('c', c + d * 2.0, (0, 0, 0), 0.26)
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = cam
        sc.render.resolution_x = sc.render.resolution_y = 520
        sc.render.filepath = os.path.join(out, f'{side[0]}_{f:02d}_{t}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
