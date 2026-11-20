"""Per clip and bone: key count, rotation range from the first key (deg) and location range (model units), plus the
world position of each bone head at the first/mid/last key. Args: <glb>"""
import bpy, sys, json, math
from mathutils import Quaternion, Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
out = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    n = 24
    rec = {}
    for k in range(n + 1):
        f = f0 + (f1 - f0) * k / n
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        for pb in arm.pose.bones:
            m = arm.matrix_world @ pb.matrix
            r = rec.setdefault(pb.name, {'q': [], 'p': []})
            r['q'].append(m.to_quaternion()); r['p'].append(m.translation.copy())
    res = {}
    for b, r in rec.items():
        q0 = r['q'][0]
        ang = max(math.degrees(q0.rotation_difference(q).angle) for q in r['q'])
        ps = r['p']
        span = [round(max(p[i] for p in ps) - min(p[i] for p in ps), 4) for i in range(3)]
        res[b] = {'rot_deg': round(ang, 1), 'pos_span': span, 'p0': [round(x, 4) for x in ps[0]],
                  'pmid': [round(x, 4) for x in ps[n // 2]], 'p1': [round(x, 4) for x in ps[-1]]}
    out[act.name] = {'frames': [f0, f1], 'bones': res}
print('RANGES ' + json.dumps(out))
