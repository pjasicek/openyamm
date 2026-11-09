"""Fit finger chains around the hilt in hand space, penalizing bone/skin penetration along every link."""
import itertools
import json
import math

import bpy
from mathutils import Matrix, Vector

from mesh_tools import ROOT


def fit():
    arm = bpy.data.objects['GB15 Goblin rig']
    hand = arm.data.bones['hand.R']
    inverse = hand.matrix_local.inverted()
    weapon = arm.data.bones['weapon.R']
    center = inverse @ weapon.head_local
    axis = (inverse.to_3x3() @ (weapon.tail_local - weapon.head_local)).normalized()
    result = {}
    for finger in range(4):
        bones = [arm.data.bones[f'digit.R.{finger}.{i:02}'] for i in [1, 2, 3]]
        relatives = [inverse @ bones[0].matrix_local] + \
            [bones[i - 1].matrix_local.inverted() @ bones[i].matrix_local for i in [1, 2]]

        def evaluate(angles, details=False):
            matrices = []
            matrix = Matrix.Identity(4)
            for relative, angle in zip(relatives, angles):
                matrix = matrix @ relative @ Matrix.Rotation(math.radians(-angle), 4, 'X')
                matrices.append(matrix)
            points = [matrix.translation for matrix in matrices] + [matrices[-1] @ Vector((0, bones[-1].length, 0))]
            penalty, minimum = 0, 1
            for segment, (a, b) in enumerate(zip(points, points[1:])):
                radius = [.008, .0068, .0045][segment] * (1 if finger < 3 else .90)
                for t in [.15, .35, .55, .75, .95]:
                    v = a.lerp(b, t) - center
                    distance = (v - axis * v.dot(axis)).length
                    clearance = distance - (.013 + radius)
                    minimum = min(minimum, clearance)
                    penalty += 300 * min(0, clearance - .0005) ** 2
                    penalty += .12 * (distance - (.013 + radius + .003)) ** 2
            tip = points[-1] - center
            radial = (tip - axis * tip.dot(axis)).length
            penalty += (radial - .019) ** 2 * 2
            penalty += 30 * min(0, center.z - points[-1].z - .006) ** 2
            penalty += 30 * max(0, points[-1].y - center.y + .007) ** 2
            penalty += 20 * min(0, center.z - points[2].z - .014) ** 2
            return (penalty, minimum, radial) if details else penalty

        best = min(itertools.product(range(35, 81, 5), range(45, 111, 5), range(0, 91, 5)), key=evaluate)
        best = min(itertools.product(*(range(max(0, n - 4), n + 5) for n in best)), key=evaluate)
        score, clearance, tip_distance = evaluate(best, True)
        result[str(finger)] = {'degrees': list(best), 'minimum_centerline_skin_clearance_m': clearance,
                               'tip_axis_distance_m': tip_distance}
    (ROOT / 'authoring/grip_angles.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result)
    return result
