"""The warglaives replace the fist-held crescents (2026-10-24): Family_Blade_L/R get the standard Harrower glaive and
Vreth_Blade_L/R Vreth's (work/warglaive_<key>_baked.blend, warglaive_texture.py), skinned rigidly to Blade_<S> as the
crescents were, with the same material slots (plate, glow).
- UVs move into the glaive's atlas rect (warglaives/atlas_rects.json; warglaive_atlas.py pastes the texture there).
- Placement in the hand (grip_pose_<S>.json, hand-local): the grip centre on the solved handle centre, the long axis
  on the handle axis, and the glowing (concave) edge toward the knuckles along the forearm: the old frame's +y on the
  right hand and -y on the left (z x blade_out; the set's sword blows move the blade that way, so the edge leads where
  the crescents led with their flat). The left glaive is the right one mirrored through its face (its winding turned).
- grip_pose_<S>.json gets a 'glaive' block (the edge direction and the two tip points, hand-local) for the gates.
Args: -- <in blend> <out blend> [--write-grip]"""
from pathlib import Path
import sys, json
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
P = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
src, out = (str(Path(a).resolve()) for a in args[:2]); write_grip = '--write-grip' in args
R = json.loads((P / 'warglaives/atlas_rects.json').read_text()); N = R['atlas']
bpy.ops.wm.open_mainfile(filepath=src)
rig = bpy.data.objects['Rig']
G = {s: json.loads((P / f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
report = {}; TIPS = {}; EDGE = {}; YAX = {}
for kind, key in (('Family', 'harrower'), ('Vreth', 'vreth')):
    with bpy.data.libraries.load(str(P / f'work/warglaive_{key}_baked.blend'), link=False) as (a, b):
        b.objects = [f'Warglaive_{key}']
    glaive = b.objects[0]
    me0 = glaive.data
    x0, y0, w, h = R['rects'][key]
    for loop in me0.uv_layers.active.data:
        u, v = loop.uv
        loop.uv = ((x0 + u * w) / N, 1 - (y0 + (1 - v) * h) / N)
    co = np.array([v.co for v in me0.vertices])
    TIPS[key] = [co[np.argmax(co[:, 2])].tolist(), co[np.argmin(co[:, 2])].tolist()]
    near = co[np.abs(co[:, 2]) < 0.04]
    grip_r = float(np.median(np.linalg.norm(near[:, :2], axis=1))) if len(near) else None
    for s in 'LR':
        old = bpy.data.objects[f'{kind}_Blade_{s}']
        mats = list(old.data.materials); mods = [(m.name, m.type) for m in old.modifiers]
        groups = [g.name for g in old.vertex_groups]
        assert groups == [f'Blade_{s}'] or f'Blade_{s}' in groups, (old.name, groups)
        hand = rig.data.bones[f'B_{s}_Hand'].matrix_local
        z = Vector(G[s]['handle_axis_hand_local']).normalized(); xo = Vector(G[s]['blade_out_hand_local']).normalized()
        yo = z.cross(xo)
        edge = yo if s == 'R' else -yo
        Y = z.cross(edge) if s == 'R' else -z.cross(edge)
        M = Matrix((edge, Y, z)).transposed().to_4x4(); M.translation = Vector(G[s]['handle_centre_hand_local'])
        A = hand @ M
        me = me0.copy(); me.name = f'{kind}_Blade_{s}'
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.transform(bm, matrix=A, verts=bm.verts)
        if A.to_3x3().determinant() < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        for i, m in enumerate(mats):      # replace the slots in place: clearing them resets every face to slot 0
            me.materials[i] = m
        name = old.name
        bpy.data.objects.remove(old)
        ob = bpy.data.objects.new(name, me)
        for c in rig.users_collection:
            c.objects.link(ob)
        ob.parent = rig; ob.matrix_world = rig.matrix_world.copy()
        vg = ob.vertex_groups.new(name=f'Blade_{s}'); vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
        for mname, mtype in mods:
            m = ob.modifiers.new(mname, mtype)
            if mtype == 'ARMATURE':
                m.object = rig
        EDGE[s], YAX[s] = list(edge), list(Y)
        report[name] = {'tris': sum(len(p.vertices) - 2 for p in me.polygons), 'glow_faces': sum(p.material_index == 1 for p in me.polygons),
                        'grip_radius_m': round(grip_r, 4) if grip_r else None, 'mirrored': A.to_3x3().determinant() < 0}
    bpy.data.objects.remove(glaive); bpy.data.meshes.remove(me0)
if write_grip:
    # the glaive frame per hand (X the edge, Y, Z the handle; the left one mirrored) and each design's tips in it
    for s in 'LR':
        G[s]['glaive'] = {'edge_hand_local': EDGE[s], 'y_hand_local': YAX[s], 'tips_glaive_local': TIPS}
        (P / f'work/grip_pose_{s}.json').write_text(json.dumps(G[s], indent=1) + '\n')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out)
print('WARGLAIVES', json.dumps(report), flush=True)
