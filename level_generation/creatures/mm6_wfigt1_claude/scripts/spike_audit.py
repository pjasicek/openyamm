"""Skin spikes and creases in the shoulder region: per body-skin vertex the Laplacian (offset from the mean of its
neighbours) length; prints the vertices whose Laplacian grew most from the bind pose to the given frames, with their
weights. Args: blend clip frame[,frame]"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, clip, frames = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
arm = bpy.data.objects['Werewolf_Rig']; mesh = bpy.data.objects['Werewolf']; me = mesh.data
parts = json.loads(bpy.context.scene['wfigt1_parts'])
pa = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', pa)
body = set()
for p in me.polygons:
    if parts[pa[p.index]] == 'Body':
        body.update(p.vertices)
nb = {}
for e in me.edges:
    a, b = e.vertices
    if a in body and b in body:
        nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
G = {g.index: g.name for g in mesh.vertex_groups}


def P():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    X = np.array([tuple(mesh.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return X


def lap(X):
    return {i: float(np.linalg.norm(X[i] - X[n].mean(0))) for i, n in nb.items()}


arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
X0 = P(); L0 = lap(X0)
region = [i for i in nb if X0[i, 2] > 1.0 and 0.1 < abs(X0[i, 0]) < 0.45]
a = bpy.data.actions[clip]; arm.animation_data.action = a
if a.slots: arm.animation_data.action_slot = a.slots[0]
for f in frames.split(','):
    bpy.context.scene.frame_set(int(f)); X = P(); L = lap(X)
    rows = sorted(((L[i] - L0[i], i) for i in region), reverse=True)[:6]
    print('SPIKE', clip, f, 'max growth cm', round(rows[0][0] * 100, 2), 'n>1cm', sum(1 for i in region if L[i] - L0[i] > 0.01))
    for g, i in rows:
        print('   ', round(g * 100, 2), i, tuple(np.round(X0[i], 3)),
              {G[x.group]: round(x.weight, 2) for x in me.vertices[i].groups})
