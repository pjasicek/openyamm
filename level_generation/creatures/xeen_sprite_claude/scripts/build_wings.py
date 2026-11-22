"""Four wing cards (prep_wings.py) on four rigid wing bones. Each wing is a flat card of square cells in the plane of
the HD wing master (seen from behind), scaled to SPAN m across all four wings, rooted on the back just behind the
hair at shoulder-blade height (the native frames draw the wings behind the hair), swept back by SWEEP deg at rest
(tips toward +Y, behind her). Bones Wing_L_Up, Wing_L_Low, Wing_R_Up, Wing_R_Low (parent B_Spine2; head at the wing's
root, tail toward its centroid), each wing 100 % on its bone (insect wings are rigid). Object 'Wings', material
'SpriteWing' (textures/sprite_wing_basecolor.png, alpha blended, double-sided). The right wings mirror the left ones
and share their UVs. Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, json, math
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
from mathutils import Vector, Matrix
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
SPAN, SWEEP, ROOT_DZ, ROOT_GAP = E('SPAN', 1.45), E('SWEEP', 22), E('ROOT_DZ', -0.06), E('ROOT_GAP', 0.012)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
for o in [o for o in bpy.data.objects if o.name.startswith('Wings')]:     # rebuild: replace the old cards
    bpy.data.objects.remove(o, do_unlink=True)
W = json.load(open('work/wings.json'))
ru, rv = W['root']; T = W['tex']
xs = [c[0] for w in W['wings'].values() for c in w['cells']]
span_px = 2 * (ru - min(xs))
s = SPAN / span_px
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
pv = np.zeros(len(co), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
zr = rig.data.bones['B_L_UpperArm'].head_local.z + ROOT_DZ
near = (np.abs(co[:, 0]) < 0.06) & (np.abs(co[:, 2] - zr) < 0.03) & np.isin(pv, (0, 1))
y_back = float(co[near][:, 1].max()) + ROOT_GAP
root = Vector((0.0, y_back, zr))
print('WINGROOT', [round(x, 3) for x in root], 'scale m/px', round(s, 6), 'span', SPAN)
wings = bpy.data.objects.new('Wings', bpy.data.meshes.new('Wings'))
bpy.context.scene.collection.objects.link(wings)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
groups = {}
bone_def = {}
for side, sg in (('L', 1.0), ('R', -1.0)):
    ang = math.radians(SWEEP) * sg
    Rz = Matrix.Rotation(ang, 3, 'Z')
    for key, part in (('UL', 'Up'), ('LL', 'Low')):
        w = W['wings'][key]; C = w['cell']
        bname = f'Wing_{side}_{part}'
        vmap = {}
        r_off = Vector((sg * 0.012, 0, 0.015 if part == 'Up' else -0.015))

        def P(u, v):
            u = min(u, ru + 2)
            local = Vector((sg * (ru - u) * s, 0.0, (rv - v) * s))
            return root + r_off + Rz @ local

        def vert(u, v):
            k = (u, v)
            if k not in vmap:
                vmap[k] = bm.verts.new(P(u, v))
                groups.setdefault(bname, []).append(vmap[k])
            return vmap[k]
        for gx, gy in w['cells']:
            q = [(gx, gy), (gx + C, gy), (gx + C, gy + C), (gx, gy + C)]
            if sg < 0:
                q = q[::-1]
            vs = [vert(*p) for p in q]
            for tri in ((0, 1, 2), (0, 2, 3)):
                f = bm.faces.new([vs[i] for i in tri])
                for lp, i in zip(f.loops, tri):
                    u, v = q[i]; u = min(u, ru + 2)
                    lp[uvl].uv = ((u - T['x0']) * T['scale'] / 1024, 1 - (v - T['y0']) * T['scale'] / 1024)
        cu, cv = w['centroid']
        bone_def[bname] = (root + r_off, P(cu, cv))
bm.verts.index_update()
idx = {b: [v.index for v in vs] for b, vs in groups.items()}
bm.to_mesh(wings.data); bm.free()
for p in wings.data.polygons:
    p.use_smooth = False
# normals: every card faces back (+Y) at rest before the sweep, so the lit side is the side the party sees from behind;
# the material is double-sided
for b, ids in idx.items():
    g = wings.vertex_groups.new(name=b); g.add(ids, 1.0, 'REPLACE')
print('WINGMESH verts', len(wings.data.vertices), 'tris', len(wings.data.polygons))
# bones
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb_sp = rig.data.edit_bones['B_Spine2']
for b, (h, t) in bone_def.items():
    if b in rig.data.edit_bones:
        rig.data.edit_bones.remove(rig.data.edit_bones[b])
    eb = rig.data.edit_bones.new(b); eb.head = h; eb.tail = h + (t - h).normalized() * 0.12
    eb.align_roll(Vector((0, 0, 1)) if abs((t - h).normalized().z) < 0.9 else Vector((0, 1, 0)))
    eb.parent = eb_sp; eb.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
wings.parent = rig
m = wings.modifiers.new('Armature', 'ARMATURE'); m.object = rig
# material
mat = bpy.data.materials.new('SpriteWing'); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
img = bpy.data.images.load(os.path.abspath('textures/sprite_wing_basecolor.png'))
tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img
nt.links.new(tn.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(tn.outputs['Alpha'], bsdf.inputs['Alpha'])
bsdf.inputs['Roughness'].default_value = 0.6
for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
    if hasattr(mat, attr):
        try:
            setattr(mat, attr, val)
        except Exception:
            pass
mat.use_backface_culling = False
wings.data.materials.append(mat)
bpy.context.scene['wing_root'] = list(root)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
