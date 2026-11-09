import bpy, math, addon_utils
from mathutils import Vector
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
bpy.ops.wm.read_factory_settings(use_empty=True); addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
h = HumanService.create_human(); rig = HumanService.add_builtin_rig(h, "default")
J = lambda n, t=False: rig.matrix_world @ (rig.pose.bones[n].tail if t else rig.pose.bones[n].head)
for sfx in ('.L', '.R'):
    w = J('wrist' + sfx); m3 = J('finger3-1' + sfx); hd = (m3 - w).normalized()
    t = J('finger2-1' + sfx) - J('finger5-1' + sfx); t = (t - hd * t.dot(hd)).normalized()
    n = (t.cross(hd) if sfx == '.R' else hd.cross(t)).normalized()
    print('FRAME', sfx, 'h', [round(x, 2) for x in hd], 't', [round(x, 2) for x in t], 'n', [round(x, 2) for x in n])
    for b in ('finger1-1', 'finger1-2', 'finger2-1', 'finger2-2', 'finger3-1'):
        pb = rig.pose.bones[b + sfx]; pb.rotation_mode = 'XYZ'
        t0 = J(b + sfx, True); base = J(b + sfx); L = (t0 - base).length
        res = []
        for k in range(3):
            e = [0, 0, 0]; e[k] = 0.3; pb.rotation_euler = e; bpy.context.view_layer.update()
            d = (J(b + sfx, True) - t0) / L
            res.append('xyz'[k] + ':h%.2f t%.2f n%.2f' % (d.dot(hd), d.dot(t), d.dot(n)))
        pb.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
        dirb = (t0 - base).normalized()
        print(' ', b + sfx, 'dir h%.2f t%.2f n%.2f' % (dirb.dot(hd), dirb.dot(t), dirb.dot(n)), ' | '.join(res))
