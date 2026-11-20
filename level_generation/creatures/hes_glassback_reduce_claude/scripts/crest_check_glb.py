"""Crest clearance gate on an exported GLB (the source project's crest_check.py, which reads its master blend, applied
to the runtime body as imported): per clip and frame, each crest plate's root and axis (work/crest_layout.json, copied
from ../hes_glassback_claude/work/) follow its bone; a ray down the axis from 25 cm above finds the deformed hide.
offset = hide height above the root in units of the plate's sink 1.3 r (+ swallowed, - gap; below -1 the open bottom
would show). Also the nearest tip-to-tip distance between plates on different bones for all three crest sizes.
Usage: blender -b -P crest_check_glb.py -- <glb> <out json name>  -> review/<name>"""
import bpy, os, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, name = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects['Glassback']
layout = json.load(open(os.path.join(HERE, 'work', 'crest_layout.json')))
REST = {b.name: b.matrix_local.copy() for b in rig.data.bones}
SIZES = {'short': (0.42, 0.85), 'full': (1.0, 1.0), 'tall': (1.3, 1.05)}
out = {}
for clip in ['Standing', 'Walking', 'Running', 'Attack', 'Bite', 'Hit', 'Death', 'Dead', 'Fidget']:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst_gap, worst_sw, min_tip = 0.0, 0.0, 9.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
        tips = []
        for c in layout:
            M = rig.matrix_world @ rig.pose.bones[c['bone']].matrix @ REST[c['bone']].inverted()
            p = M @ Vector(c['p']); a = (M.to_3x3() @ Vector(c['axis'])).normalized()
            hit = bvh.ray_cast(p + a * 0.25, -a, 0.6)
            off = (0.25 - hit[3] if hit[0] is not None else -0.3) / (1.3 * c['radius'])
            worst_gap = min(worst_gap, off); worst_sw = max(worst_sw, off)
            tips.append((c['bone'], p, a, c['h']))
        for size, (hs, rs) in SIZES.items():
            for i in range(len(tips)):
                for j in range(i + 1, len(tips)):
                    if tips[i][0] != tips[j][0]:
                        ti = tips[i][1] + tips[i][2] * tips[i][3] * hs; tj = tips[j][1] + tips[j][2] * tips[j][3] * hs
                        min_tip = min(min_tip, (ti - tj).length)
    out[clip] = {'gap_in_sinks': round(worst_gap, 3), 'swallow_in_sinks': round(worst_sw, 3),
                 'min_tip_distance_m_across_bones_all_sets': round(min_tip, 3)}
    print('CREST_CLEAR', clip, out[clip], flush=True)
json.dump(out, open(os.path.join(HERE, 'review', name), 'w'), indent=1)
