"""Posing helpers for the impaled corpses: import a rigged MM6 peasant GLB (assets_dev/worlds/mm6/models, read only),
drop its clips, place the armature with a world transform and pose bones with world-space operations, then bake the
pose into a static mesh. Bone operations, applied in order (each moves the bone's children with it):
  ('aim', bone, direction, amount[, tip])  turn the bone (minimal rotation) so head -> tip (default its tail) points
                                           along the world direction; amount < 1 turns part of the way
  ('rot', bone, axis, degrees)             rotate about a world axis through the bone's head
  ('twist', bone, degrees)                 rotate about the bone's own current axis
  ('move', bone, point)                    translate the bone so its head lands on the world point (unconnected
                                           bones only, e.g. a severed thigh)
  ('aim_group', [roots], [ends], direction) rigidly turn sibling chains (a skirt) about their roots' mean head so
                                           the axis from there to the ends' mean tail points along the direction
Directions and axes are world (Blender Z up; the sprite camera looks along +Y, so +X is screen right)."""
import bpy, bmesh, math
from mathutils import Matrix, Quaternion, Vector


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    body = next(o for o in new if o.type == 'MESH' and o.parent is arm)
    for o in new:
        if o not in (arm, body):
            bpy.data.objects.remove(o)
    arm.animation_data_clear()
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    return arm, body


def place(arm, rotation, hips_at):
    """World transform: rotation (3x3 Matrix) about the rest hips, which land at hips_at."""
    hips = arm.data.bones['mixamorig:Hips'].head_local
    arm.matrix_world = Matrix.Translation(Vector(hips_at) - rotation @ hips) @ rotation.to_4x4()
    bpy.context.view_layer.update()


def _apply(arm, pb, world_rotation, pivot_world):
    inv = arm.matrix_world.inverted()
    pivot = inv @ pivot_world
    local = inv.to_3x3() @ world_rotation @ arm.matrix_world.to_3x3()
    pb.matrix = Matrix.Translation(pivot) @ local.to_4x4() @ Matrix.Translation(-pivot) @ pb.matrix
    bpy.context.view_layer.update()


def pose(arm, ops):
    bones = arm.pose.bones
    for op in ops:
        kind, name = op[0], op[1]
        if kind == 'aim_group':
            roots, ends = [bones[n] for n in op[1]], [bones[n] for n in op[2]]
            pivot = sum((arm.matrix_world @ b.head for b in roots), Vector()) / len(roots)
            end = sum((arm.matrix_world @ b.tail for b in ends), Vector()) / len(ends)
            q = (end - pivot).normalized().rotation_difference(Vector(op[3]).normalized())
            for b in roots:
                _apply(arm, b, q.to_matrix(), pivot)
            continue
        pb = bones[name]
        head = arm.matrix_world @ pb.head
        if kind == 'aim':
            direction, amount = Vector(op[2]).normalized(), op[3]
            tip = arm.matrix_world @ (bones[op[4]].head if len(op) > 4 else pb.tail)
            q = (tip - head).normalized().rotation_difference(direction)
            q = Quaternion().slerp(q, amount)
            _apply(arm, pb, q.to_matrix(), head)
        elif kind == 'rot':
            _apply(arm, pb, Matrix.Rotation(math.radians(op[3]), 3, Vector(op[2]).normalized()), head)
        elif kind == 'move':
            offset = arm.matrix_world.inverted().to_3x3() @ (Vector(op[2]) - head)
            pb.matrix = Matrix.Translation(offset) @ pb.matrix
            bpy.context.view_layer.update()
        elif kind == 'twist':
            axis = (arm.matrix_world @ pb.tail - head).normalized()
            _apply(arm, pb, Matrix.Rotation(math.radians(op[2]), 3, axis), head)
        else:
            raise ValueError(kind)


def bake(arm, body, name, drop_groups=(), keep_groups=None):
    """Static copy of the posed mesh in world space (each vertex keeps its rest position in the 'rest' attribute).
    Vertices whose strongest bone is in drop_groups are removed; with
    keep_groups only those bones' vertices stay. Returns the object (its vertex groups are kept for later masks)."""
    if 'rest' not in body.data.attributes:
        rest = body.data.attributes.new('rest', 'FLOAT_VECTOR', 'POINT')
        co = [c for v in body.data.vertices for c in v.co]
        rest.data.foreach_set('vector', co)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    mesh.transform(body.matrix_world)
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    for g in body.vertex_groups:
        if g.name not in obj.vertex_groups:
            obj.vertex_groups.new(name=g.name)
    names = [g.name for g in body.vertex_groups]
    bm = bmesh.new(); bm.from_mesh(mesh)
    deform = bm.verts.layers.deform.verify()
    remove = []
    for v in bm.verts:
        weights = v[deform]
        strongest = names[max(weights.items(), key=lambda kv: kv[1])[0]] if len(weights) else None
        if strongest in drop_groups or (keep_groups is not None and strongest not in keep_groups):
            remove.append(v)
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    # the glTF import splits vertices along texture seams: weld them (texture coordinates stay per corner), so
    # decimation cannot crack the seams open and real holes (stumps) are closed loops
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    drop_duplicate_faces(bm)                      # welding can stack two faces on the same corners
    bm.to_mesh(mesh); bm.free()
    if 'custom_normal' in mesh.attributes:          # imported split normals no longer match the welded mesh
        mesh.attributes.remove(mesh.attributes['custom_normal'])
    return obj


def drop_duplicate_faces(bm):
    seen, duplicates = set(), []
    for f in bm.faces:
        key = frozenset(f.verts)
        if key in seen or len(key) < 3:
            duplicates.append(f)
        else:
            seen.add(key)
    bmesh.ops.delete(bm, geom=duplicates, context='FACES')
    return len(duplicates)


def clean(obj):
    """Remove duplicate and degenerate faces (decimation can leave some)."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    count = drop_duplicate_faces(bm)
    bm.to_mesh(obj.data); bm.free()
    return count


def strongest_bone(obj):
    """Per-vertex name of the strongest bone."""
    names = [g.name for g in obj.vertex_groups]
    out = []
    for v in obj.data.vertices:
        out.append(names[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '')
    return out
