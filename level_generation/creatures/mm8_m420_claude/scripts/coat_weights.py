"""Keep the chest/collar on the torso and blend the sewn sleeves into the arms."""
import bpy
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]


def smooth(x, a, b):
    u = float(np.clip((x - a) / (b - a), 0, 1))
    return u * u * (3 - 2 * u)


def repair(body, rig):
    changed = 0
    center = rig.data.bones['B_Spine2'].head_local.x
    for v, piece in zip(body.data.vertices, body.data.attributes['piece'].data):
        if piece.value != 0:
            continue
        x, y, z = v.co
        lateral = abs(x - center)
        if z < 1.08 and not (lateral > .26 and z > .88):
            continue
        side = 'L' if x > center else 'R'
        bones = [f'B_{side}_{n}' for n in ['UpperArm', 'Forearm', 'Hand']]
        shoulder, elbow, wrist = [rig.data.bones[n].head_local for n in bones]
        upper = (v.co - shoulder).dot(elbow - shoulder) / (elbow - shoulder).length_squared
        lower = (v.co - elbow).dot(wrist - elbow) / (wrist - elbow).length_squared
        arm = smooth(lateral, .16, .28)
        forearm = smooth(upper, .78, 1.18)
        # The coat sleeve must not counter-twist through the shoulder seam.
        lower_twist = smooth(lower, .15, .85)
        values = {
            bones[0]: arm * (1 - forearm),
            bones[1]: arm * forearm * (1 - lower_twist),
            bones[1] + 'Twist': arm * forearm * lower_twist,
        }
        # The coat's waist is sewn to the rigid sash; its raised collar follows the neck.
        levels = [(1.08, 'B_Pelvis'), (1.18, 'B_Spine'), (1.28, 'B_Spine1'),
                  (1.36, 'B_Spine2'), (1.46, 'B_Neck')]
        for (za, na), (zb, nb) in zip(levels, levels[1:]):
            if z <= zb:
                t = smooth(z, za, zb)
                values[na] = (1 - arm) * (1 - t)
                values[nb] = (1 - arm) * t
                break
        else:
            values['B_Neck'] = 1 - arm
        values = dict(sorted(values.items(), key=lambda p: -p[1])[:4])
        total = sum(values.values())
        assert total > .99, (v.index, total)
        for g in body.vertex_groups:
            g.remove([v.index])
        for name, weight in values.items():
            if weight > 1e-7:
                body.vertex_groups[name].add([v.index], weight / total, 'REPLACE')
        assert abs(sum(g.weight for g in v.groups) - 1) < 1e-5
        if lateral <= .16:
            assert not any('Arm' in body.vertex_groups[g.group].name or
                           'Clavicle' in body.vertex_groups[g.group].name for g in v.groups)
        changed += 1
    print('COAT_WEIGHTS', changed, 'vertices; chest/collar isolated from arms')
    return changed


if __name__ == '__main__':
    bpy.ops.wm.open_mainfile(filepath=str(P / 'review/coat_skin/baseline/work/master_settled.blend'))
    repair(bpy.data.objects['Body'], bpy.data.objects['Rig'])
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/master_settled.blend'))
