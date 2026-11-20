"""Local, editable deform skeleton. All bind locations come from the authored surface guides."""
import json
import math

import bpy
from mathutils import Vector, Matrix, Quaternion

from mesh_tools import ROOT, Mesh, material, ring


def weapon():
    marks = json.loads((ROOT / 'authoring/landmarks.json').read_text())
    wrist = Vector(marks['wrist.R'])
    down = (Vector(marks['hand_end.R']) - wrist).normalized()
    across = down.cross(Vector((0, -1, 0))).normalized()
    axis = (-across + down * .19).normalized()
    front = Vector((0, -1, 0))
    broad = axis.cross(front).normalized()
    # Bind hands show their dorsal surface forward; the palm is behind that surface.
    center = wrist + down * .060 - front * .025
    mesh = Mesh('GB15 Curved sword', material('Sword steel', (.19, .205, .215), .32, .9))
    weight = {'weapon.R': 1}
    # Six-sided blade cross section keeps a central ridge and thin cutting edges.
    rows = []
    for t, offset, width in [(0, 0, .024), (.08, -.002, .027), (.19, -.009, .030),
                              (.31, -.024, .032), (.41, -.047, .030), (.48, -.074, .025),
                              (.525, -.094, .013), (.553, -.109, .0008)]:
        c = center + axis * (.083 + t) + broad * offset
        rows.append([mesh.vertex(c + broad * x + front * y, weight)
                     for x, y in [(-width, 0), (-width * .65, .003), (width * .65, .003),
                                  (width, 0), (width * .65, -.003), (-width * .65, -.003)]])
    for a, b in zip(rows, rows[1:]):
        mesh.bridge(a, b)
    mesh.cap(rows[0], weight)
    mesh.cap(rows[-1], weight)
    # A shallow hooked crossguard, rather than a heavy modern sword hilt.
    rows = []
    for x, bend in [(-.064, -.019), (-.057, -.010), (-.031, 0), (0, .003), (.031, 0),
                    (.057, -.010), (.064, -.019)]:
        c = center + axis * (.073 + bend) + broad * x
        rows.append(ring(mesh, c, axis, front, .007, .006, 6, weight))
    for a, b in zip(rows, rows[1:]):
        mesh.bridge(a, b)
    mesh.cap(rows[0], weight)
    mesh.cap(rows[-1], weight)
    # Grip and pommel have their own material regions but stay one rigid surface assembly.
    grip_start = len(mesh.faces)
    rows = [ring(mesh, center + axis * t, broad, front, radius, radius, 10, weight)
            for t, radius in [(-.064, .012), (-.056, .013), (.046, .013), (.063, .012)]]
    for a, b in zip(rows, rows[1:]):
        mesh.bridge(a, b)
    mesh.cap(rows[0], weight)
    mesh.cap(rows[-1], weight)
    grip_end = len(mesh.faces)
    rows = [ring(mesh, center + axis * t, broad, front, radius, radius, 8, weight)
            for t, radius in [(-.079, .007), (-.074, .020), (-.064, .021), (-.059, .013)]]
    for a, b in zip(rows, rows[1:]):
        mesh.bridge(a, b)
    mesh.cap(rows[0], weight)
    mesh.cap(rows[-1], weight)
    obj = mesh.object()
    obj.data.materials.append(bpy.data.materials['GB15 Leather blockout'])
    obj.data.materials.append(bpy.data.materials['GB15 Muted brass'])
    for poly in obj.data.polygons:
        if grip_start <= poly.index < grip_end:
            poly.material_index = 1
        elif poly.index >= grip_end:
            poly.material_index = 2
    obj.data.set_sharp_from_angle(angle=.65)
    info = {'center': list(center), 'axis': list(axis), 'front': list(front), 'broad': list(broad),
            'grip_radius': .013, 'grip_length': .127, 'blade_length': .553}
    (ROOT / 'authoring/weapon.json').write_text(json.dumps(info, indent=2) + '\n')
    return info


def build():
    marks = json.loads((ROOT / 'authoring/landmarks.json').read_text())
    skirts = json.loads((ROOT / 'authoring/skirt_controls.json').read_text())
    sword = weapon()
    data = bpy.data.armatures.new('GB15 Local deform skeleton')
    rig = bpy.data.objects.new('GB15 Goblin rig', data)
    bpy.data.collections['GB15 Character'].objects.link(rig)
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')

    def bone(name, head, tail, parent=None, roll=(0, -1, 0)):
        b = data.edit_bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = data.edit_bones[parent]
        b.align_roll(Vector(roll))
        return b

    bone('root', (0, 0, 0), (0, 0, .20), roll=(0, -1, 0))
    for name, tail, parent in [('pelvis', marks['spine'], 'root'), ('spine', marks['chest'], 'pelvis'),
                               ('chest', marks['neck'], 'spine'), ('neck', marks['head'], 'chest'),
                               ('head', (0, .035, 1.70), 'neck')]:
        bone(name, marks[name], tail, parent)
    for suffix in ['.L', '.R']:
        side = 1 if suffix == '.L' else -1
        bone('clavicle' + suffix, (side * .037, .047, 1.318), marks['shoulder' + suffix], 'chest')
        bone('upper_arm' + suffix, marks['shoulder' + suffix], marks['elbow' + suffix], 'clavicle' + suffix)
        bone('forearm' + suffix, marks['elbow' + suffix], marks['wrist' + suffix], 'upper_arm' + suffix)
        bone('forearm_twist' + suffix, Vector(marks['elbow' + suffix]).lerp(Vector(marks['wrist' + suffix]), .45),
             marks['wrist' + suffix], 'forearm' + suffix)
        bone('hand' + suffix, marks['wrist' + suffix], marks['hand_end' + suffix], 'forearm_twist' + suffix)
        bone('pauldron' + suffix, marks['shoulder' + suffix],
             Vector(marks['shoulder' + suffix]) + Vector((side * .10, 0, .02)), 'upper_arm' + suffix)
        bone('thigh' + suffix, marks['hip' + suffix], marks['knee' + suffix], 'pelvis')
        bone('shin' + suffix, marks['knee' + suffix], marks['ankle' + suffix], 'thigh' + suffix)
        bone('foot' + suffix, marks['ankle' + suffix], marks['toe_end' + suffix], 'shin' + suffix,
             roll=(0, 0, 1))
        for name in ['digit' + suffix + '.' + str(i) for i in range(4)] + ['thumb' + suffix]:
            points = marks[name]
            for index in range(3):
                bname = name + '.' + str(index + 1).zfill(2)
                parent = 'hand' + suffix if index == 0 else name + '.' + str(index).zfill(2)
                bone(bname, points[index], points[index + 1], parent)
    for name, (head, tail) in skirts.items():
        bone(name, head, tail, 'pelvis')
    bone('weapon.R', sword['center'], Vector(sword['center']) + Vector(sword['axis']) * .18,
         'hand.R', roll=sword['front'])
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    rig['gb_role'] = 'rig'
    rig['gb_hand_revision'] = 1
    rig['gb_forward'] = '-Y; Z up; meters; working body height 1.7m'
    for pose in rig.pose.bones:
        pose.rotation_mode = 'QUATERNION'
    # Continuous distal twist weighting is independent of rigid forearm armor.
    skin = bpy.data.objects['GB15 Skin body']
    for suffix in ['.L', '.R']:
        original = skin.vertex_groups['forearm' + suffix]
        twist = skin.vertex_groups.new(name='forearm_twist' + suffix)
        a, b = Vector(marks['elbow' + suffix]), Vector(marks['wrist' + suffix])
        axis = b - a
        for vertex in skin.data.vertices:
            found = next((entry.weight for entry in vertex.groups if entry.group == original.index), 0)
            if found:
                t = max(0, min(1, ((vertex.co - a).dot(axis) / axis.length_squared - .26) / .62))
                if t:
                    original.add([vertex.index], found * (1 - t), 'REPLACE')
                    twist.add([vertex.index], found * t, 'REPLACE')
    for obj in list(bpy.data.collections['GB15 Character'].objects):
        if obj.type != 'MESH':
            continue
        obj.parent = rig
        mod = obj.modifiers.new('Local skeletal deformation', 'ARMATURE')
        mod.object = rig
        mod.use_deform_preserve_volume = False  # Same linear skinning as portable glTF.
    print('Local bones', len(data.bones))
    return rig


if __name__ == '__main__':
    build()
