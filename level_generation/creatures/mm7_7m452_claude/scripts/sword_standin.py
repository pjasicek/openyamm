"""Stand-in sword on our rig's B_R_Hand from work/grip_source.json (source hand-local grip, scaled by the hand length
ratio). Usable as a module: add_sword(rig) -> object to re-place each frame with place(obj, rig)."""
import bpy, bmesh, json, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def add_sword(rig):
    g = json.load(open(os.path.join(HERE, 'work', 'grip_source.json')))
    src = json.load(open(os.path.join(HERE, 'work', 'source_rest.json')))
    hs = (Vector(src['B_R_Hand']['head']) - Vector(src['B_R_Forearm']['head'])).length
    ho = (rig.data.bones['B_R_Hand'].head_local - rig.data.bones['B_R_Forearm'].head_local).length
    # grip_source.json is in the source hand bone's local space incl. the armature's 0.01 scale: centre in cm-ish units
    c = Vector(g['centre_hand']) * 0.01 * (ho / hs) * (1.0 / 1.0)
    ax = Vector(g['axis_hand']).normalized()
    side = ax.orthogonal().normalized(); flat = ax.cross(side)
    me = bpy.data.meshes.new('sword'); bm = bmesh.new()
    for a0, a1, w, t in ((-0.10, 0.0, 0.015, 0.015), (0.0, 0.015, 0.08, 0.018), (0.015, 0.8, 0.025, 0.005)):
        corners = [c + ax * a + side * (sx * w) + flat * (sy * t) for a in (a0, a1) for sx in (-1, 1) for sy in (-1, 1)]
        vs = [bm.verts.new(v) for v in corners]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            bm.faces.new([vs[i] for i in q])
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('StandInSword', me); bpy.context.scene.collection.objects.link(ob)
    return ob


def place(ob, rig):
    m = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    loc, rot, _ = m.decompose()
    ob.matrix_world = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
