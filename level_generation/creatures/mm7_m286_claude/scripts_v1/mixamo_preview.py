"""Preview skin-less Mixamo clips on a joint-head stick mannequin (G1, before modelling).
Left hand red, right hand blue. Frames go to <out_dir>/<tag>_<view>_<i>.png with frames.json for sheet_rows.py.
Args: -- <out_dir> <frames per clip> <views comma list> <fbx> [<fbx> ...]"""
import bpy, sys, os, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
out, n, views, files = a[0], int(a[1]), a[2].split(','), a[3:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'OBJECT'
pairs = [('Hips', 'Spine', .07), ('Spine', 'Spine1', .08), ('Spine1', 'Spine2', .10), ('Spine2', 'Neck', .12),
         ('Neck', 'Head', .05)]
for s in ('Left', 'Right'):
    pairs += [(s + 'Shoulder', s + 'Arm', .05), (s + 'Arm', s + 'ForeArm', .05), (s + 'ForeArm', s + 'Hand', .04),
              ('Hips', s + 'UpLeg', .07), (s + 'UpLeg', s + 'Leg', .07), (s + 'Leg', s + 'Foot', .05),
              (s + 'Foot', s + 'ToeBase', .05), (s + 'Hand', s + 'HandMiddle1', .03)]
parts = []
for _ in pairs:
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1, depth=1)
    parts.append(bpy.context.object)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=.12)
head = bpy.context.object
hands = {}
for s, col in (('Left', (1, .1, .1, 1)), ('Right', (.1, .3, 1, 1))):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=.06)
    hands[s] = bpy.context.object
    hands[s].color = col
rows = []
for fbx in files:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    act = src.animation_data.action
    pre = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
    names = {b.name for b in src.data.bones}
    tag = os.path.splitext(os.path.basename(fbx))[0].replace(' ', '_')
    f0, f1 = act.frame_range
    for view in views:
        row = []
        for i in range(n):
            f = f0 + (f1 - f0) * i / max(n - 1, 1)
            scene.frame_set(int(f), subframe=f - int(f))
            bpy.context.view_layer.update()

            def point(b):
                return src.matrix_world @ src.pose.bones[pre + b].head
            for (p0, p1, r), o in zip(pairs, parts):
                if pre + p1 not in names:
                    o.hide_render = True
                    continue
                o.hide_render = False
                va, vb = point(p0), point(p1)
                o.location = (va + vb) / 2
                o.scale = (r, r, max((vb - va).length, 1e-4))
                o.rotation_euler = (vb - va).to_track_quat('Z', 'Y').to_euler()
            head.location = point('Head') + Vector((0, 0, .08))
            for s in hands:
                hands[s].location = point(s + 'Hand')
            hip = point('Hips')
            p = common.render_views(os.path.join(out, f'{tag}_{view}_{i}'), 1.0, 2.4, views=(view,),
                                    resolution=(220, 300), target=(hip.x, hip.y))[0]
            row.append([p, f'{tag[:18]} {view[:5]} {f:.0f}'])
        rows.append(row)
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
print('PREVIEW', len(rows), 'rows')
