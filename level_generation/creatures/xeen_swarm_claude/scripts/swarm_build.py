"""Insect Swarm / Stingers: seven copies of the one textured Stinger (work/wasp_uv.blend: 1,118 triangles, shared UVs)
in a cloud, each on its own bone W<i> (body, head and legs rigid) with four wing bones W<i>_FL/FR/HL/HR at the wing
roots (wasp_hinges.json). The wings are their own mesh (SwarmWings, blended material) so the body LODs and shadows stay
opaque. Forward -Y. Writes work/swarm_rig.blend and work/swarm_layout.json."""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'wasp_uv.blend'))
src = bpy.data.objects['Wasp']
hinges = {k: Vector(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'wasp_hinges.json')))['hinges'].items()}
# the wasp's own centre (its bone head): the thorax middle
co = np.array([v.co[:] for v in src.data.vertices])
centre = Vector(((co[:, 0].min() + co[:, 0].max()) / 2, (co[:, 1].min() + co[:, 1].max()) / 2, float(co[:, 2].mean())))
# cloud layout: positions (m, actor space) and yaw (deg); about 1.1 m wide, 0.2-1.25 m high
LAYOUT = [((0.00, 0.00, 0.85), 0), ((0.50, 0.16, 1.08), -18), ((-0.48, 0.10, 1.00), 15), ((0.28, -0.34, 0.52), -8),
          ((-0.33, -0.28, 0.62), 12), ((0.10, 0.42, 1.32), 25), ((-0.17, 0.34, 0.28), -20)]
SIZE = 1.6                                   # each Stinger 0.45 -> 0.72 m wingspan, about 0.4 m long
WING_KEYS = ('FL', 'FR', 'HL', 'HR')

arm = bpy.data.armatures.new('Swarm_Rig'); rig = bpy.data.objects.new('Swarm_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
root = eb.new('Root'); root.head = (0, 0, 0); root.tail = (0, 0.15, 0)
mats = []
for i, (p, yaw) in enumerate(LAYOUT):
    M = (Matrix.Translation(Vector(p)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Scale(SIZE, 4)
         @ Matrix.Translation(-centre))
    mats.append(M)
    b = eb.new(f'W{i}'); b.head = M @ centre; b.tail = M @ (centre + Vector((0, -0.08, 0))); b.parent = root
    b.align_roll(Vector((0, 0, 1)))
    for k in WING_KEYS:
        h = hinges['Wing' + k]
        out = Vector((0.06 if k[1] == 'L' else -0.06, 0, 0))
        w = eb.new(f'W{i}_{k}'); w.head = M @ h; w.tail = M @ (h + out); w.parent = b
        w.align_roll(M.to_3x3() @ Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')


def copies(keep_wings):
    objs = []
    for i, M in enumerate(mats):
        o = src.copy(); o.data = src.data.copy(); o.name = f'copy{i}'
        bpy.context.scene.collection.objects.link(o)
        o.data.transform(M)
        names = {g.index: g.name for g in o.vertex_groups}
        wing_faces = []
        for poly in o.data.polygons:
            g = [names[x.group] for x in o.data.vertices[poly.vertices[0]].groups]
            if any(n.startswith('Wing') for n in g) != keep_wings:
                wing_faces.append(poly.index)
        import bmesh
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[j] for j in wing_faces], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(o.data); bm.free()
        for g in list(o.vertex_groups):
            g.name = f'W{i}' if g.name in ('Body', 'Head') else f'W{i}_{g.name[4:]}'
        objs.append(o)
    for o in bpy.data.objects: o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    out = bpy.context.view_layer.objects.active
    # Body and Head groups of one copy both became W<i>: merge duplicates by name
    return out


body = copies(False); body.name = body.data.name = 'Swarm'
wings = copies(True); wings.name = wings.data.name = 'SwarmWings'
bpy.data.objects.remove(src, do_unlink=True)
for o in (body, wings):
    o.parent = rig
    mod = o.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
    # merge vertex groups that share a name after the rename (Blender suffixes duplicates with .001)
    for g in list(o.vertex_groups):
        if '.' in g.name:
            base = o.vertex_groups.get(g.name.split('.')[0])
            idx = [v.index for v in o.data.vertices if any(x.group == g.index for x in v.groups)]
            if base is None:
                g.name = g.name.split('.')[0]
            else:
                base.add(idx, 1.0, 'REPLACE'); o.vertex_groups.remove(g)
    empty = [v.index for v in o.data.vertices if not v.groups]
    print('MESH', o.name, 'tris', len(o.data.polygons), 'groups', len(o.vertex_groups), 'unweighted', len(empty))
json.dump({'layout': LAYOUT, 'centre': list(centre)}, open(os.path.join(HERE, 'work', 'swarm_layout.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'swarm_rig.blend'))
print('SAVED swarm_rig.blend bones', len(arm.bones))
