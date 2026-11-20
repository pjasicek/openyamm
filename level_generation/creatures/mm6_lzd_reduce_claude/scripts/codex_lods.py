"""LOD1-3 from the accepted Codex LODs instead of decimating the reduced LOD0 (tools/build_actor_lods.py moved the
fitted grips and soles: review/gates_nofix). Each Codex level is trimmed to its target body triangle count with the
hands, fingers, loin flap and soles locked (vertex group: hand/finger/LoinFlap weight >= 0.2 or z < 0.06 m are not
collapsed; an unlocked LOD2 flap turned dark and crumpled); the
string/arrow primitive is kept. Spliced into the reduced LOD0 file like build_actor_lods (shadow LODs rebuilt).
Usage: blender -b -P codex_lods.py -- <codex source glb> <reduced lod0 glb> <out glb> <t1,t2,t3 body tris>"""
import copy, json, struct, sys, tempfile
from pathlib import Path
import bpy, bmesh
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor, merge_shadow  # noqa: E402
src_path, lod0_path, out_path, targets = sys.argv[sys.argv.index('--') + 1:]
targets = [int(t) for t in targets.split(',')]
NODE, LOCK_Z, HAND_W = 'Lizard', 0.06, 0.2
src, src_bin = read_glb(Path(src_path))
node = next(n for n in src['nodes'] if n.get('name') == NODE)
codex_lods = src['meshes'][node['mesh']]['extras']['openyamm_lods']
tmp = copy.deepcopy(src); parent = next(n for n in tmp['nodes'] if tmp['nodes'].index(node) in n.get('children', []))
for k, mi in enumerate(codex_lods, 1):
    parent['children'].append(len(tmp['nodes'])); tmp['nodes'].append({'name': f'Src{k}', 'mesh': mi, 'skin': node['skin']})
tmp_path = Path(tempfile.mkdtemp()) / 'codex_lods_in.glb'; write_glb(tmp_path, tmp, bytearray(src_bin))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(tmp_path))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data_clear()
for bone in rig.pose.bones: bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
hand_bones = {b.name for b in rig.data.bones if any(s in b.name for s in ('_L_Hand', '_R_Hand', '_L_Finger', '_R_Finger', 'LoinFlap'))}
objects = []
for level, target in enumerate(targets, 1):
    srco = bpy.data.objects[f'Src{level}']
    for slot in range(len(srco.data.materials)):
        obj = srco.copy(); obj.data = srco.data.copy(); obj.animation_data_clear(); obj.name = f'LOD{level}_{slot}'
        bpy.context.collection.objects.link(obj)
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != slot], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        n = len(bm.faces); bm.to_mesh(obj.data); bm.free()
        if obj.data.materials[slot].name.startswith('Lizard_A') and n > target:
            idx = {g.index for g in obj.vertex_groups if g.name in hand_bones}
            group = obj.vertex_groups.new(name='Reduce'); mw = obj.matrix_world; free = []
            for v in obj.data.vertices:
                hand = sum(g.weight for g in v.groups if g.group in idx)
                if hand < HAND_W and (mw @ v.co).z >= LOCK_Z: free.append(v.index)
            group.add(free, 1.0, 'REPLACE')
            mod = obj.modifiers.new('Trim', 'DECIMATE'); mod.use_collapse_triangulate = True
            mod.vertex_group = 'Reduce'; mod.vertex_group_factor = 1000
            while obj.modifiers[0] != mod:
                bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_move_up(modifier=mod.name)
            lo, hi = 0.05, 1.0
            for _ in range(24):
                mod.ratio = (lo + hi) / 2; bpy.context.view_layer.update()
                got = len(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
                lo, hi = (mod.ratio, hi) if got < target else (lo, mod.ratio)
            mod.ratio = hi
            bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name); obj.vertex_groups.remove(obj.vertex_groups['Reduce'])
            print('LEVEL', level, n, '->', len(obj.data.polygons), 'free verts', len(free), 'of', len(obj.data.vertices))
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bpy.ops.object.vertex_group_limit_total(limit=8); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        objects.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for o in objects + [rig]: o.select_set(True)
geo = Path(out_path).with_suffix('.geometry.glb')
bpy.ops.export_scene.gltf(filepath=str(geo), use_selection=True, export_format='GLB', export_animations=False,
                          export_skins=True, export_all_influences=True)
# Splice (as tools/build_actor_lods.py) into the reduced LOD0 file.
before, original = read_glb(Path(lod0_path))
bnode = next(n for n in before['nodes'] if n.get('name') == NODE); mesh_index = bnode['mesh']
joint_names = [before['nodes'][i]['name'] for i in before['skins'][bnode['skin']]['joints']]
bind = list(struct.iter_unpack('<16f', accessor_bytes(before, original, before['skins'][bnode['skin']]['inverseBindMatrices'])))
exported, payload = read_glb(geo)
doc = copy.deepcopy(before); binary = bytearray(original); mats = {m['name']: i for i, m in enumerate(doc['materials'])}
doc['meshes'][mesh_index].pop('extras', None); lod_indices = []
for level in range(1, 4):
    mesh = {'name': f'{NODE}_LOD{level}', 'primitives': []}
    for ln in exported['nodes']:
        if not ln.get('name', '').startswith(f'LOD{level}_') or 'mesh' not in ln: continue
        skin = exported['skins'][ln['skin']]; remap = [joint_names.index(exported['nodes'][i]['name']) for i in skin['joints']]
        mats4 = list(struct.iter_unpack('<16f', accessor_bytes(exported, payload, skin['inverseBindMatrices'])))
        assert all(abs(a - b) < 1e-4 for i, m in zip(remap, mats4) for a, b in zip(bind[i], m)), 'bind space changed'
        for prim in exported['meshes'][ln['mesh']]['primitives']:
            attrs = {}
            for sem, ai in prim['attributes'].items():
                acc = exported['accessors'][ai]; packed = accessor_bytes(exported, payload, ai)
                if sem.startswith('JOINTS_'):
                    code = {5121: 'B', 5123: 'H'}[acc['componentType']]
                    vals = [remap[v[0]] for v in struct.iter_unpack('<' + code, packed)]; packed = struct.pack('<' + code * len(vals), *vals)
                attrs[sem] = append_accessor(doc, binary, acc, packed)
            mesh['primitives'].append({'attributes': attrs, 'indices': append_accessor(doc, binary,
                exported['accessors'][prim['indices']], accessor_bytes(exported, payload, prim['indices'])),
                'material': mats[exported['materials'][prim['material']]['name']]})
    lod_indices.append(len(doc['meshes'])); doc['meshes'].append(mesh)
shadows = []
for i in [mesh_index] + lod_indices:
    shadows.append(len(doc['meshes'])); doc['meshes'].append(merge_shadow(doc, binary, doc['meshes'][i]))
doc['meshes'][mesh_index].setdefault('extras', {}).update(openyamm_lods=lod_indices, openyamm_shadow_lods=shadows)
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in [mesh_index] + lod_indices]
assert all(a > b for a, b in zip(counts, counts[1:])), counts
write_glb(Path(out_path), doc, binary); print('LOD triangles:', counts)
