"""Analytic two-bone rest-frame solve keeps seated palms clear while the torso acts."""
from mathutils import Matrix, Vector
import math
import bpy


def pin_arm(rig, side, target, hand_rotation):
    upper, fore, hand = [rig.pose.bones[f'B_{side}_{n}'] for n in ('UpperArm', 'Forearm', 'Hand')]
    a, b, c = upper.head.copy(), fore.head.copy(), hand.head.copy()
    l1, l2 = (b - a).length, (c - b).length
    delta = target - a
    distance = delta.length
    assert abs(l1-l2) + 1e-4 < distance < l1+l2-1e-4, (side, distance, l1, l2)
    axis = delta.normalized()
    bend = b-a-axis*(b-a).dot(axis)
    bend.normalize()
    along = (l1*l1-l2*l2+distance*distance)/(2*distance)
    elbow = a+axis*along+bend*math.sqrt(max(0,l1*l1-along*along))

    def swing(bone, old, new):
        rotation = old.rotation_difference(new)
        matrix = rotation.to_matrix().to_4x4() @ bone.matrix
        matrix.translation = bone.head
        bone.matrix = matrix
        bpy.context.view_layer.update()

    swing(upper, b-a, elbow-a)
    swing(fore, hand.head-fore.head, target-fore.head)
    matrix = hand_rotation.to_matrix().to_4x4()
    matrix.translation = hand.head
    hand.matrix = matrix
    bpy.context.view_layer.update()
    assert (hand.head-target).length < 1e-4
