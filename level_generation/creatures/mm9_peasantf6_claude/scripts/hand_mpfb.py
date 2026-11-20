"""One posed MPFB (MakeHuman, CC0) left hand with a forearm stub, for the sleeves: after mm9_thrall_claude/scripts/graft_hands.py, no weld, the stub ends inside the sleeve. Writes work/hand.npz: co, tri, W (per vertex, bones), bones,
joints (name -> head), frame. Args: <out npz> <tris>"""
import bpy, bmesh, math, sys, json
import addon_utils
import numpy as np
from mathutils import Vector
OUT, TRIS = sys.argv[sys.argv.index('--') + 1:]; TRIS = int(TRIS)
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
macro = {"gender": 0.0, "age": 0.5, "muscle": 0.4, "weight": 0.45, "proportions": 0.5, "height": 0.5, "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.33, "caucasian": 0.34, "african": 0.33}}
h = HumanService.create_human(macro_detail_dict=macro)
mrig = HumanService.add_builtin_rig(h, "default")
mask = next(m for m in h.modifiers if m.type == 'MASK'); MG, MI = mask.vertex_group, mask.invert_vertex_group
mask.show_viewport = False; mask.show_render = False
dg = lambda: bpy.context.evaluated_depsgraph_get()
nvm = len(h.data.vertices); names = {g.index: g.name for g in h.vertex_groups}
WM = {}
for v in h.data.vertices:
    for g in v.groups: WM.setdefault(names[g.group], np.zeros(nvm))[v.index] = g.weight
bodymask = WM.get(MG, np.zeros(nvm)) > .5
if MI: bodymask = ~bodymask
FING = {f: [f'finger{f}-{j}' for j in (1, 2, 3)] for f in range(1, 6)}; HANDB = ['wrist'] + [f'metacarpal{i}' for i in range(1, 5)]
def MJ(n, tail=False):
    pb = mrig.pose.bones[n]; return mrig.matrix_world @ (pb.tail if tail else pb.head)
def flex_sign(bone, n):
    pb = mrig.pose.bones[bone]; pb.rotation_mode = 'XYZ'
    t0 = MJ(bone, True); pb.rotation_euler = (0.3, 0, 0); bpy.context.view_layer.update()
    t1 = MJ(bone, True); pb.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    return 1.0 if (t1 - t0).dot(n) > 0 else -1.0
sfx = '.L'
w = MJ('wrist' + sfx); m3 = MJ('finger3-1' + sfx); i2 = MJ('finger2-1' + sfx); p5 = MJ('finger5-1' + sfx)
hd = (m3 - w).normalized(); t = i2 - p5; t = (t - hd * t.dot(hd)).normalized(); n = hd.cross(t).normalized()
for f, deg, sp in zip((2, 3, 4, 5), [-4, -3, -1, 1], [3, 0, -2, -5]):
    for b, k in zip(FING[f], (1.0, 1.1, 0.8)):
        s = flex_sign(b + sfx, n); pb = mrig.pose.bones[b + sfx]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (s * math.radians(deg * k), 0, math.radians(sp) if b.endswith('-1') else 0)
for b, a in zip(FING[1], [0, 4, 6]):
    s = flex_sign(b + sfx, n); pb = mrig.pose.bones[b + sfx]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (s * math.radians(a), 0, 0)
bpy.context.view_layer.update()
hw = sum(WM.get(b + sfx, 0) for b in HANDB + sum(FING.values(), []))
ev = h.evaluated_get(dg()); me_ev = ev.to_mesh(); PM = np.array([(h.matrix_world @ v.co)[:] for v in me_ev.vertices]); ev.to_mesh_clear()
hv = np.where((hw > .5) & bodymask)[0]; L = float(((PM[hv] - np.array(w[:])) @ np.array(hd[:])).max())
print('HANDLEN', L)
me = bpy.data.meshes.new_from_object(h.evaluated_get(dg()), preserve_all_data_layers=True, depsgraph=dg())
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
keep = set()
for v in bm.verts:
    if v.index >= nvm or not bodymask[v.index]: continue
    p = h.matrix_world @ v.co
    armw = hw[v.index] + WM.get('lowerarm02' + sfx, np.zeros(nvm))[v.index] + WM.get('lowerarm01' + sfx, np.zeros(nvm))[v.index]
    if hw[v.index] > .5 or ((p - w).dot(hd) > -0.9 * L and armw > .3): keep.add(v.index)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.transform(h.matrix_world); bm.to_mesh(me); bm.free()
o = bpy.data.objects.new('Hand', me); bpy.context.scene.collection.objects.link(o)
keepg = [b + sfx for b in HANDB + sum(FING.values(), [])] + ['lowerarm02' + sfx, 'lowerarm01' + sfx]
for g in list(o.vertex_groups):
    if g.name not in keepg: o.vertex_groups.remove(g)
bpy.context.view_layer.objects.active = o
for x in bpy.data.objects: x.select_set(x is o)
J = {b: list(MJ(b + sfx)) for b in HANDB + sum(FING.values(), [])}
for f in range(1, 6): J[f'finger{f}-3_tip'] = list(MJ(f'finger{f}-3' + sfx, True))
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x, do_unlink=True)
t0 = sum(len(p.vertices) - 2 for p in me.polygons)
m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TRIS / t0; m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d')
me = o.data; me.calc_loop_triangles()
co = np.array([v.co[:] for v in me.vertices]); tri = np.array([lt.vertices[:] for lt in me.loop_triangles])
gn = [g.name for g in o.vertex_groups]; W = np.zeros((len(co), len(gn)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
np.savez(OUT, co=co, tri=tri, W=W, bones=np.array(gn), joints=json.dumps(J), frame=json.dumps(dict(w=list(w), hd=list(hd), t=list(t), n=list(n), L=L)))
print('HAND', t0, '->', len(tri), 'verts', len(co), 'wrist', list(w), 'hd', list(hd))
