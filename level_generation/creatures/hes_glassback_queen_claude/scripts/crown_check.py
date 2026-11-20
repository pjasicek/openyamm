"""Crown clearance gate on the exported Queen body (as crest_check_glb.py of hes_glassback_reduce_claude, for the
crown): per clip and frame, each crown spine's root, axis and tip follow Head (work/crown_layout.json):
- root offset: deformed hide height above the root along the axis, in sinks (1.3 r): + swallowed, - gap (below -1
  the open bottom would show);
- clearance: the nearest distance from each crown spine (root to tip) to each crest plate segment on another bone
  (work/crest_layout.json, tall sizes, the Neck1 plates and the two removed front Spine3 midline plates excluded), minus both
  radii; below 0 they intersect;
- body: whether a crown tip is inside the hide (a ray from the tip straight up hits the body's inside).
Usage: blender -b -P crown_check.py -- <glb> <out json name> -> review/<name>"""
import bpy, os, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, name = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects['Glassback']
crown = json.load(open(os.path.join(HERE, 'work', 'crown_layout.json')))
crest = [c for c in json.load(open(os.path.join(HERE, 'work', 'crest_layout.json')))
         if c['bone'] != 'Neck1' and not (c['bone'] == 'Spine3' and (c['p'][1] < -0.9 or (c['row'] == 'mid' and c['p'][1] < -0.7)))]
REST = {b.name: b.matrix_local.copy() for b in rig.data.bones}


def seg_seg(a0, a1, ra, b0, b1, rb):
    """Clearance between two tapered prisms (radius r at the root, 0.2 r at the tip): sampled on the first, nearest
    point on the second; distance minus both local radii."""
    best = 9.0
    ab = b1 - b0
    for k in range(21):
        t = k / 20
        p = a0.lerp(a1, t)
        u = max(0.0, min(1.0, (p - b0).dot(ab) / ab.length_squared))
        best = min(best, (p - (b0 + ab * u)).length - ra * (1 - 0.8 * t) - rb * (1 - 0.8 * u))
    return best


out = {}
for clip in ['Standing', 'Walking', 'Running', 'Attack', 'Bite', 'Hit', 'Death', 'Dead', 'Fidget']:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    gap, sw, clear, inside = 0.0, 0.0, 9.0, 0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
        segs = []
        for c in crest:
            M = rig.matrix_world @ rig.pose.bones[c['bone']].matrix @ REST[c['bone']].inverted()
            p = M @ Vector(c['p']); a = (M.to_3x3() @ Vector(c['axis'])).normalized()
            segs.append((p, p + a * c['h'] * 1.3, c['radius']))
        M = rig.matrix_world @ rig.pose.bones['Head'].matrix @ REST['Head'].inverted()
        for c in crown:
            p = M @ Vector(c['p']); a = (M.to_3x3() @ Vector(c['axis'])).normalized()
            hit = bvh.ray_cast(p + a * 0.25, -a, 0.6)
            off = (0.25 - hit[3] if hit[0] is not None else -0.3) / (1.3 * c['radius'])
            gap = min(gap, off); sw = max(sw, off)
            tip = p + a * c['h']
            for s0, s1, r in segs:
                d = seg_seg(p, tip, c['radius'], s0, s1, r)
                if d < clear:
                    clear = d; worst = (f, [round(x, 2) for x in s0], [round(x, 2) for x in p])
            h = bvh.ray_cast(tip, Vector((0, 0, 1)), 5.0)
            if h[0] is not None and h[1].dot(Vector((0, 0, 1))) > 0:
                inside += 1
    print('WORST', clip, worst)
    out[clip] = {'worst_gap': round(gap, 2), 'worst_swallow': round(sw, 2), 'min_clearance_m': round(clear, 3),
                 'tips_inside_frames': inside}
    print('CROWN_CHECK', clip, out[clip])
json.dump(out, open(os.path.join(HERE, 'review', name), 'w'), indent=1)
