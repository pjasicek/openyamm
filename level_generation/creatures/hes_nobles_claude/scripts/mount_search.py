"""Two-handed weapons out of the body: search a constant extra turn of the weapon about its grip (yaw and pitch in the
right grip socket's frame, +-45 deg in 5 deg steps) that minimises the deepest weapon point inside the torso (the body
without the wing membranes; points within 7 cm of either hand are grip contacts and ignored) over the library poses of
the set (the torso, legs and head; the arms only with WITH_ARMS: a gun resting on the support forearm is contact: carry, fire/attack, cast at a few times), the source arms on our rig. The smallest turn within 5 mm of the best
depth wins; written as `adjust: [yaw, pitch]` (degrees) into scripts/weapons.json, applied by clips_lib.mount_matrix.
Args: -- <weapon> <glb> <clip:time> [<clip:time> ...]"""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]
a = sys.argv[sys.argv.index('--') + 1:]
weapon, glb, specs = a[0], a[1], [(x.rsplit(':', 1)[0], float(x.rsplit(':', 1)[1])) for x in a[2:]]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'rig.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; BODY = bpy.data.objects['Body']
MOUNTS = json.loads((P / 'scripts' / 'weapons.json').read_text()); m = dict(MOUNTS[weapon]); m.pop('adjust', None)
src = cl.load_sources(ROOT, {glb: sorted({c for c, t in specs})}, sc)
gi = {g.index: g.name for g in BODY.vertex_groups}
dom = [gi[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in BODY.data.vertices]
ARMS = ('B_Wing_',) if os.environ.get('WITH_ARMS') else \
    ('B_Wing_', 'B_L_UpperArm', 'B_R_UpperArm', 'B_L_Fore', 'B_R_Fore', 'B_L_Hand', 'B_R_Hand', 'B_L_Finger', 'B_R_Finger')
faces = [tuple(p.vertices) for p in BODY.data.polygons if not any(dom[i].startswith(ARMS) for i in p.vertices)]
with bpy.data.libraries.load(str(P / 'work' / 'weapons' / f"{m.get('mesh', weapon)}.blend"), link=False) as (s_, d_):
    d_.meshes = [n for n in s_.meshes if n.startswith('W_')]
pts = [Vector(v.co) for v in list(d_.meshes[0].vertices)[::4]]
poses = []
for clip, t in specs:
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for n in cl.TRUNK[1:]: cl.set_world_rot(rig, n, cl.sample(src, clip, t, n))
    for n in cl.CLAV + cl.ARM['L'] + cl.ARM['R']:
        cl.set_world_rot(rig, n, rig.pose.bones['B_Spine2'].matrix.to_quaternion()
                         @ cl.sample(src, clip, t, 'B_Spine2').inverted() @ cl.sample(src, clip, t, n))
    dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); me = e.to_mesh()
    co = [tuple(v.co) for v in me.vertices]; e.to_mesh_clear()
    poses.append((BVHTree.FromPolygons(co, faces), rig.pose.bones['Grip_R'].matrix.copy(),
                  [rig.pose.bones[f'B_{s}_Hand'].head.copy() for s in 'LR']))
base = cl.mount_matrix(m)


def depth(yaw, pitch):
    adj = (Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(pitch), 4, 'X'))
    worst = 0.0
    for tree, G, hands in poses:
        W = G @ adj @ base
        for p in pts:
            q = W @ p
            if min((q - h).length for h in hands) < 0.07: continue
            loc, n, i, dist = tree.find_nearest(q)
            if loc is not None and dist < 0.12:
                worst = max(worst, -(q - loc).dot(n))
    return worst


res = sorted((depth(y, p), y, p) for y in range(-45, 46, 5) for p in range(-45, 46, 5))
best = res[0][0]
pick = min((r for r in res if r[0] <= best + 0.005), key=lambda r: abs(r[1]) + abs(r[2]))
MOUNTS[weapon]['adjust'] = [pick[1], pick[2]]
for k, v in MOUNTS.items():                                         # the roll previews share the cleaver's mount
    if k.startswith(weapon + '_r') and isinstance(v, dict): v['adjust'] = [pick[1], pick[2]]
(P / 'scripts' / 'weapons.json').write_text(json.dumps(MOUNTS, indent=1))
print('ADJUST', weapon, 'depth before', round(depth(0, 0), 4), 'after', round(pick[0], 4), 'turn', pick[1:], flush=True)
sys.stdout.flush(); os._exit(0)
