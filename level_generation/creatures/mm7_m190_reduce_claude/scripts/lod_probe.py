"""Where a LOD goes lowest / stretches: for work/lodcheck_<label>_<level>.glb, the lowest vertex over a clip (frame, rest
position, top weights) and the faces stretching over 20x their rest area (frame, rest centre, rest area, ratio).
Usage: blender -b -P lod_probe.py -- <label> <level> <clip,...>"""
import bpy, bmesh, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
label, level, clips = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'lodcheck_{label}_{level}.glb')); o = bpy.data.objects['Dwarf']
rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE'); names = {g.index: g.name for g in o.vertex_groups}
def state():
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.faces.ensure_lookup_table()
    out = np.array([f.calc_area() for f in b.faces]), np.array([v.co[:] for v in b.verts]); b.free(); return out
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update(); a0, c0 = state(); F = np.array([p.vertices[:] for p in o.data.polygons])
for clip in clips.split(','):
    act = bpy.data.actions[clip]; rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range); low = (9, 0, 0)
    for fr in range(f0, f1 + 1):
        sc.frame_set(fr); a1, c1 = state(); i = int(np.argmin(c1[:, 2]))
        if c1[i, 2] < low[0]:
            low = (c1[i, 2], fr, i)
        for k in np.flatnonzero((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9))):
            print('LODPROBE stretch', clip, fr, 'rest centre', np.round(c0[F[k]].mean(0), 3), 'rest area mm2', round(a0[k] * 1e6, 3), 'ratio', round(a1[k] / (a0[k] + 1e-12), 1))
    gs = sorted(o.data.vertices[low[2]].groups, key=lambda g: -g.weight)
    print('LODPROBE low', clip, 'z', round(low[0], 4), 'frame', low[1], 'rest', np.round(c0[low[2]], 3), [(names[g.group], round(g.weight, 2)) for g in gs[:4]])
