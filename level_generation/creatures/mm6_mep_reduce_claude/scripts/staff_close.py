"""Staff close-ups (installed / reduced tags): top end, middle and bottom end, side and 45-degree views, clay with
cavity. review/props/staff_close.png. Usage: blender -b -P staff_close.py -- tag [tag ...]"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
tags = sys.argv[sys.argv.index('--') + 1:]
paths = [('installed', f'{HERE}/base/mm6_mep_staff.glb')] + [(t, f'{HERE}/export/mm6_mep_staff_{t}.glb') for t in tags]
shots = []
for label, p in paths:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=p)
    sc = bpy.context.scene
    ms = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in ms:
        if 'LOD' in o.name: o.hide_render = True
    o = next(o for o in ms if 'LOD' not in o.name)
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    ax = max(range(3), key=lambda i: max(q[i] for q in pts) - min(q[i] for q in pts))
    lo, hi = min(q[ax] for q in pts), max(q[ax] for q in pts)
    cen = sum(pts, Vector()) / len(pts)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.display.shading.show_cavity = True; sc.render.resolution_x = sc.render.resolution_y = 400
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .22
    for k, f in [('top', .93), ('mid', .5), ('bot', .07)]:
        c = cen.copy(); c[ax] = lo + (hi - lo) * f
        for vn, d in [('a', Vector((1, 0, 0)) if ax != 0 else Vector((0, 1, 0))), ('b', Vector((1, 1, 0)).normalized() if ax == 2 else Vector((0, 1, 1)).normalized())]:
            cam.location = c + d * 2; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y' if ax != 1 else 'Z').to_euler()
            f_ = f'{HERE}/review/props/_s_{label}_{k}{vn}.png'; sc.render.filepath = f_; bpy.ops.render.render(write_still=True)
    shots.append([f'{HERE}/review/props/_s_{label}_{k}{vn}.png' for k in ['top', 'mid', 'bot'] for vn in 'ab'])
open(f'{HERE}/review/props/_s_rows.txt', 'w').write('\n'.join(' '.join(r) for r in shots))
