"""Restore the exact runtime UV layout the Meshy retextures were painted on (Blender). The retexture returns keep the
uploaded UVs (enable_original_uv); smart-project packing is not bit-reproducible, so the layout is taken from the
returns themselves: body faces from meshy/body_retexture_v3, head faces from head_, wing faces from wings_ (each
upload carried its own set at the runtime place). Return positions are mapped back by bounding box, every face of
work/v3/uv_master.blend is matched to the return's triangles by vertex positions, and each corner takes the UV of
the coincident return corner. Saves work/v3/uv_master.blend (UVMap replaced) and work/v3/uv_final.npy.
Usage: blender -b -P meshy_uvs.py"""
import bpy, numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data; rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
co = np.array([v.co[:] for v in me.vertices]); lo, hi = co.min(0), co.max(0)
uv = me.uv_layers['UVMap'].data; report = {}
for slot, label in enumerate(['body', 'head', 'wings']):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(P / f'meshy/{label}_retexture_v3/model_urls_glb.glb'))
    new = [x for x in bpy.data.objects if x not in before and x.type == 'MESH']
    rm = new[0]; rme = rm.data; mw = rm.matrix_world
    rco = np.array([(mw @ v.co)[:] for v in rme.vertices]); rlo, rhi = rco.min(0), rco.max(0)
    sc = (hi - lo) / (rhi - rlo); rco = lo + (rco - rlo) * sc
    report[label + '_scale'] = sc.round(5).tolist()
    ruv = rme.uv_layers[0].data
    rme.calc_loop_triangles()
    kd = kdtree.KDTree(len(rme.loop_triangles))
    for i, t in enumerate(rme.loop_triangles): kd.insert(Vector(rco[list(t.vertices)].mean(0)), i)
    kd.balance()
    vk = kdtree.KDTree(len(rco))
    for i, p in enumerate(rco): vk.insert(Vector(p), i)
    vk.balance()
    worst = 0.; done = 0; miss = 0; fallback = 0
    me.calc_loop_triangles()
    tris_of_poly = {}
    for t in me.loop_triangles: tris_of_poly.setdefault(t.polygon_index, []).append(t)
    for t in me.loop_triangles:
        if me.polygons[t.polygon_index].material_index != slot: continue
        tv = [Vector(co[v]) for v in t.vertices]; c = (tv[0] + tv[1] + tv[2]) / 3; best = None
        for (pos, ri, dist) in kd.find_n(c, 12):
            rt = rme.loop_triangles[ri]; rv = [Vector(rco[v]) for v in rt.vertices]
            # corner correspondence: each of our corners to the nearest corner of this return triangle
            pairs = [min(range(3), key=lambda k: (rv[k] - x).length) for x in tv]
            err = sum((rv[k] - x).length for k, x in zip(pairs, tv))
            if len(set(pairs)) == 3 and (best is None or err < best[0]): best = (err, rt, pairs)
        if best is None or best[0] > 3e-3:
            # an n-gon triangulated differently (or a sliver): per corner, the coincident corner of a return triangle
            # that shares at least two of our vertex positions (same island)
            got = 0
            for li, x in zip(t.loops, tv):
                cand = None
                for (pos, ri, dist) in kd.find_n(c, 24):
                    rt = rme.loop_triangles[ri]; rv = [Vector(rco[v]) for v in rt.vertices]
                    shared = sum(1 for y in tv if min((r - y).length for r in rv) < 1e-4)
                    k = min(range(3), key=lambda k: (rv[k] - x).length)
                    if shared >= 2 and (rv[k] - x).length < 1e-4: cand = rt.loops[k]; break
                if cand is not None: uv[li].uv = ruv[cand].uv; got += 1
            if got < 3: miss += 1
            else: fallback += 1
            continue
        err, rt, pairs = best
        for li, k in zip(t.loops, pairs): uv[li].uv = ruv[rt.loops[k]].uv
        worst = max(worst, err); done += 1
    report[label] = {'triangles': done, 'fallback_triangles': fallback, 'missed': miss, 'max_position_error_mm': round(worst * 1000, 3)}
    for x in new: bpy.data.objects.remove(x, do_unlink=True)
print('MESHY_UV', report)
np.save(P / 'work/v3/uv_final.npy', np.array([d.uv[:] for d in uv], np.float32))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
