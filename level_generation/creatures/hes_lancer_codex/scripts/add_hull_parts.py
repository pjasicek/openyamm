"""Thin Ancient graft for Crown; articulated hull-plate apron and blunt industrial maul for Forge."""
import json
import math
from pathlib import Path
import sys
import bmesh
import bpy
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
source, mode, output = sys.argv[sys.argv.index('--')+1:]
assert mode in ('lancer', 'forge')
bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()))
rig = bpy.data.objects['Rig']
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.context.view_layer.update()
plate = bpy.data.materials['HKR_Plate']
ancient = bpy.data.materials.get('Lancer_Ancient') or plate.copy()
ancient.name = 'Lancer_Ancient'
for obj in list(bpy.data.objects):
    if (mode == 'forge' and (obj.name.startswith('Apron_') or obj.name == 'Thunder_Maul')) or (mode == 'lancer' and obj.name == 'Ancient_Graft'):
        bpy.data.objects.remove(obj, do_unlink=True)
dark = next(m for m in bpy.data.materials if m.name.startswith('Lancer_Resin'))
dark.name = 'Lancer_Resin'
glow = bpy.data.materials['HKR_Glow']
layout = json.loads((P / 'work/armour_layout.json').read_text())
rect = layout['plates']['back']['rect']
atlas = layout['atlas']

def bone(name, parent, matrix):
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    b = eb.get(name) or eb.new(name)
    b.head = matrix.translation
    b.tail = b.head+matrix.to_3x3() @ Vector((0, 0.08, 0))
    b.align_roll(matrix.to_3x3() @ Vector((0, 0, 1)))
    b.parent = eb[parent]
    bpy.ops.object.mode_set(mode='OBJECT')

def mesh(name, target, boxes=(), tubes=(), transform=None):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for centre, size, material, bevel in boxes:
        verts = bmesh.ops.create_cube(bm, size=1)['verts']
        for v in verts:
            v.co = Vector((v.co.x*size[0], v.co.y*size[1], v.co.z*size[2]))+Vector(centre)
        edges = list({e for v in verts for e in v.link_edges})
        faces = list({f for v in verts for f in v.link_faces})
        for f in faces:
            f.material_index = material
        if bevel:
            result = bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=1, affect='EDGES')
            for f in result['faces']:
                f.material_index = material
    for start, end, radius, material in tubes:
        axis = Vector(end)-Vector(start)
        rotate = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix()
        made = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                                    radius1=radius, radius2=radius, depth=axis.length)['verts']
        for v in made:
            v.co = rotate @ v.co+(Vector(start)+Vector(end))/2
        for f in {f for v in made for f in v.link_faces}:
            f.material_index = material
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for face in bm.faces:
        # Each hard face gets its own UV island and normal boundary; the common ceramic atlas supplies wear and trim.
        axis = max(range(3), key=lambda i: abs(face.normal[i]))
        axes = [i for i in range(3) if i != axis]
        for loop in face.loops:
            u, v = (loop.vert.co[axes[0]]*2+0.5)%1, (loop.vert.co[axes[1]]*2+0.5)%1
            loop[uv].uv = ((rect[0]+(0.12+u*0.76)*rect[2])/atlas,
                           1-(rect[1]+(0.12+v*0.76)*rect[3])/atlas)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), ngon_method='BEAUTY')
    data = bpy.data.meshes.new(name)
    bm.to_mesh(data)
    bm.free()
    if transform is not None:
        data.transform(transform)
    for material in (ancient, dark, glow, plate):
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj['lancer_atlas_rect'] = rect
    obj['lancer_atlas_size'] = atlas
    obj.vertex_groups.new(name=target).add(list(range(len(data.vertices))), 1, 'REPLACE')
    obj.modifiers.new('Armature', 'ARMATURE').object = rig
    print('HULL_PART', name, len(data.polygons), flush=True)
    return obj

if mode == 'lancer':
    bone('Ancient_Graft', 'B_Spine2', rig.data.bones['B_Spine2'].matrix_local)
    mesh('Ancient_Graft', 'Ancient_Graft', boxes=[
        ((-.045, -.445, 1.345), (.17, .018, .11), 0, .007),
        ((-.045, -.435, 1.345), (.19, .016, .125), 1, .006),
        ((-.045, -.459, 1.345), (.08, .006, .018), 3, .002)])
else:
    # The apron supplements the shared cuirass; lower halves follow the two legs through their joint gaps.
    mesh('Apron_Chest', 'B_Spine2', boxes=[((0, -.448, 1.285), (.29, .025, .285), 0, .012),
          ((0, -.467, 1.24), (.24, .008, .022), 1, .002),
          ((0, -.473, 1.365), (.16, .006, .014), 2, .002)])
    mesh('Apron_Waist', 'B_Spine', boxes=[((0, -.437, 1.071), (.29, .024, .07), 0, .009)])
    for side, sign in [('L', 1), ('R', -1)]:
        mesh(f'Apron_Hip_{side}', f'B_{side}_Thigh', boxes=[
            ((sign*.105, -.433, .905), (.155, .027, .215), 0, .012),
            ((sign*.105, -.450, .918), (.13, .006, .014), 1, .002)])
        mesh(f'Apron_Thigh_{side}', f'B_{side}_Thigh', boxes=[
            ((sign*.135, -.414, .677), (.17, .027, .215), 0, .012),
            ((sign*.135, -.431, .685), (.14, .006, .014), 1, .002)])
        mesh(f'Apron_Shin_{side}', f'B_{side}_Calf', boxes=[
            ((sign*.15, -.402, .496), (.17, .026, .11), 0, .010)])
        mesh(f'Apron_Strap_{side}', 'B_Spine2', boxes=[
            ((sign*.115, -.055, 1.30), (.044, .020, .15), 1, .003)])
    grip = json.loads((P / 'work/grip_pose_R.json').read_text())
    y = Vector(grip['handle_axis_hand_local']).normalized()
    z = Vector((0, 1, 0)); z = (z-y*z.dot(y)).normalized()
    x = y.cross(z).normalized()
    local = Matrix((x, y, z)).transposed().to_4x4()
    local.translation = Vector(grip['handle_centre_hand_local'])
    matrix = rig.data.bones['B_R_Hand'].matrix_local @ local
    bone('Thunder_Maul', 'B_R_Hand', matrix)
    mesh('Thunder_Maul', 'Thunder_Maul', tubes=[
        ((0, -.58, 0), (0, 1.06, 0), .018, 1),
        ((0, -.60, 0), (0, -.52, 0), .033, 3),
        ((0, .72, 0), (0, .86, 0), .038, 3)], boxes=[
        ((0, 1.02, 0), (.55, .25, .27), 1, .03),
        ((0, 1.02, 0), (.22, .27, .29), 2, .016),
        ((-.245, 1.02, 0), (.18, .30, .32), 0, .035),
        ((.245, 1.02, 0), (.18, .30, .32), 0, .035),
        ((0, 1.02, .15), (.50, .065, .045), 3, .008),
        ((0, 1.02, -.15), (.50, .065, .045), 3, .008)], transform=matrix)
    bone('Socket_Maul_Impact', 'Thunder_Maul', matrix @ Matrix.Translation((.335, 1.02, 0)))
    bone('Socket_Forge_Cast', 'B_L_Hand', rig.data.bones['B_L_Hand'].matrix_local @ Matrix.Translation((0, .16, 0)))
bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).resolve()))
