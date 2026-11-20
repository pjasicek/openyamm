"""G6 head clearance (gob2 review 2: the right shoulder sank into the head in the attack's follow-through). Per frame:
head skin (piece 0, Head+Neck weight > 0.6) against the shoulder geometry (pauldrons P23/P24 and their spikes, the
gorget's shoulder parts |x| > 0.12, upper-arm/clavicle skin): depth of head vertices behind the closest shoulder face
(within a 45 deg cone of its normal) and the smallest head-shoulder distance. Usable as a module: Clearance(blend
objects).measure() -> (depth, min distance, side). Args: -- <blend> action [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


class Clearance:
    def __init__(self, body):
        self.body = body; me = body.data
        pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
        gi = {g.name: g.index for g in body.vertex_groups}
        def w(names):
            ids = {gi[n] for n in names if n in gi}
            return np.array([sum(e.weight for e in v.groups if e.group in ids) for v in me.vertices])
        rest = np.array([tuple(v.co) for v in me.vertices])
        # rest-position sets (weight-independent: a weight fix must not change what is measured): head = skin above
        # the jaw line (B_Head joint - 2 cm); shoulders = the pauldrons, the gorget's shoulder parts and skin outside the
        # neck's width (> 12 cm off the neck axis) between the armpit and the jaw line
        arm_ = bpy.data.objects['Rig'].data.bones
        jaw = arm_['B_Head'].head_local.z - 0.02; ax = arm_['B_Neck'].head_local.x
        self.head = np.where((pv == 0) & (rest[:, 2] > jaw))[0]
        self.side = {}
        for s, pa, sx in (('R', 23, -1), ('L', 24, 1)):
            off = (rest[:, 0] - ax) * sx
            vs = set(np.where((pv == 0) & (off > 0.12) & (rest[:, 2] > 1.1) & (rest[:, 2] < jaw))[0])
            self.side[s] = [p for p in me.polygons if all(i in vs for i in p.vertices)]
        self.pv = pv; self.armw = {s: w([f'B_{s}_UpperArm', f'B_{s}_UpperArmTwist', f'B_{s}_Clavicle']) for s in 'RL'}
        self.last_hit = None

    def measure(self):
        ev = self.body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = [self.body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
        best = (0.0, 1e9, None)
        for s, polys in self.side.items():
            t = BVHTree.FromPolygons(co, [tuple(p.vertices) for p in polys])
            for i in self.head[::2]:
                loc, nrm, fi, d = t.find_nearest(co[i], 0.3)
                if loc is None:
                    continue
                v = co[i] - loc
                behind = v.dot(nrm) < 0 and v.length > 1e-6 and (-v).normalized().angle(nrm) < math.radians(45)
                if behind and d < 0.05 and d > best[0]:          # deeper hits are the far side of open patches
                    best = (d, best[1], s)
                    fv = polys[fi].vertices[0]
                    self.last_hit = (int(self.pv[fv]), round(float(self.armw[s][fv]), 2), int(i))
                if not behind and d < best[1]:
                    best = (best[0], d, best[2] or s)
        return best


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
    rig = bpy.data.objects['Rig']; C = Clearance(bpy.data.objects['Body'])
    for an in a[1:]:
        act = bpy.data.actions[an]; rig.animation_data.action = act
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        rows = []
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            bpy.context.scene.frame_set(f); rows.append((f,) + C.measure())
        deep = max(rows, key=lambda r: r[1]); close = min(rows, key=lambda r: r[2])
        bad = [r[0] for r in rows if r[1] > 0.005]
        print(f'HEADCLEAR {an:9s} deepest {deep[1] * 100:.1f} cm at frame {deep[0]} ({deep[3]}), closest '
              f'{close[2] * 100:.1f} cm at {close[0]}, frames with > 0.5 cm: {bad[0] if bad else "-"}..{bad[-1] if bad else "-"} ({len(bad)})')
