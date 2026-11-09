"""Every colour LOD of a GLB (REA_NODE, School here): rest-pose bounds, minimum height over every clip (every frame), and faces that
stretch over 20x their rest area at any sampled frame (the lip-seam box). Usage: blender -b -P lod_check.py -- <glb> <label>
-> work/lod_check_<label>.json"""
import bpy, bmesh, copy, json, os, sys
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
D, B = read_glb(Path(glb)); NODE = os.environ.get('REA_NODE', 'Body'); node = next(n for n in D['nodes'] if n.get('name') == NODE)
levels = [node['mesh']] + D['meshes'][node['mesh']]['extras']['openyamm_lods']; report = {}


def state(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.faces.ensure_lookup_table()
    out = np.array([f.calc_area() for f in b.faces]), np.array([v.co[:] for v in b.verts]); b.free(); return out


for level, index in enumerate(levels):
    d = copy.deepcopy(D); next(n for n in d['nodes'] if n.get('name') == NODE)['mesh'] = index
    path = P / 'work' / f'lodcheck_{label}_{level}.glb'; write_glb(path, d, B)
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=str(path)); o = bpy.data.objects[NODE]
    rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
    rig.animation_data_create(); rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update(); a0, c0 = state(o)
    item = {'tris': len(a0), 'rest_min': np.round(c0.min(0), 4).tolist(), 'rest_max': np.round(c0.max(0), 4).tolist(), 'clips': {}}
    for act in bpy.data.actions:
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        f0, f1 = (int(x) for x in act.frame_range); zmin, stretched = 10.0, 0
        for f in range(f0, f1 + 1):
            sc.frame_set(f); a1, c1 = state(o); zmin = min(zmin, float(c1[:, 2].min()))
            stretched = max(stretched, int(((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9))).sum()))
        item['clips'][act.name] = {'min_z': round(zmin, 4), 'stretched_faces': stretched}
    report[level] = item; print('LODCHECK', label, level, json.dumps(item), flush=True)
(P / 'work' / f'lod_check_{label}.json').write_text(json.dumps(report, indent=1) + '\n')
