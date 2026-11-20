"""Finish accepted LOD0 with the shared MeshLab/xatlas texture-transfer route; never alter its pose samples."""
import copy, json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
SHARED = P.parent / 'hes_kept_codex/lodrep'
sys.path[:0] = [str(SHARED), str(ROOT / 'tools')]
from build_actor_lods import read_glb, write_glb, merge_shadow, accessor_bytes
import build_lods as decimator
from build_lods import decimate_primitive, subset_primitive, source_faces
import pymeshlab
from scipy.spatial import cKDTree
from merge_head_material import accessor_array, compact as compact_materials
from splice_lods import compact, tuck_shadow, triangles
from transfer_textures import material_maps
import numpy as np
from build_actor_lods import append_accessor

stem = sys.argv[1]
ratios = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [.55, .30, .16]
assert 1 > ratios[0] > ratios[1] > ratios[2] > 0
bare = stem == 'hes_kreegan_winged'
body = stem in ('hes_overseer', 'hes_kreegan_winged')
source = P / ('work/overseer_body_lod0.glb' if body else f'work/attachments/{stem}.glb')
work = P / 'work/final_lods' / stem
work.mkdir(parents=True, exist_ok=True)
(P / 'export').mkdir(exist_ok=True)
doc, binary = read_glb(source); binary = bytearray(binary)
node = next(n for n in doc['nodes'] if 'mesh' in n)
base = doc['meshes'][node['mesh']]
if bare:
    base['primitives'] = [p for p in base['primitives']
                          if doc['materials'][p['material']]['name'].startswith(('OV_Body_', 'OV_Head_'))]
    assert len(base['primitives']) == 2
# Keep the accepted separate atlases: head/body ramps have different luminance ranges and culling.
for mat in doc['materials']:
    name = mat['name']; extras = mat.setdefault('extras', {})
    extras['openyamm_specular'] = .4 if name.startswith(('OV_Equipment', 'OV_Weapon')) else 0
    if name.startswith('OV_Glow'):
        extras['openyamm_bloom'] = True
    assert not extras.get('openyamm_specular_mask') or 'metallicRoughnessTexture' in mat['pbrMetallicRoughness']
base['extras'] = {'openyamm_lods': [], 'openyamm_shadow_lods': []}
source_mesh = copy.deepcopy(base)
counts = [triangles(doc, node['mesh'])]
if counts[0] <= 24 or stem == 'overseer_collar_key':
    base.pop('extras', None)
    write_glb(P / 'export' / f'{stem}.glb', doc, compact(doc, binary))
    (work / 'result.json').write_text(json.dumps({'triangles':counts,'simple_part_no_lods':True},indent=2)+'\n')
    sys.exit(0)

def contact_collapse(primitive, ratio):
    name = doc['materials'][primitive['material']]['name']
    if name.startswith(('OV_Sash', 'OV_Grip')):
        return copy.deepcopy(primitive)
    faces = source_faces(doc,binary,primitive)
    a = primitive['attributes']
    keep = np.zeros(len(faces),bool)
    if name.startswith('OV_Body'):
        names = [doc['nodes'][n]['name'] for n in doc['skins'][0]['joints']]
        arms = [i for i,n in enumerate(names) if n.startswith(('B_L_','B_R_'))
                and any(part in n for part in ('UpperArm','Forearm','Hand','Finger'))]
        j = accessor_array(doc,binary,a['JOINTS_0']); w = accessor_array(doc,binary,a['WEIGHTS_0'])
        keep = (np.isin(j,arms) & (w > 1e-5)).any(1)[faces].any(1)
    elif name.startswith('OV_Weapon'):
        grip = np.concatenate([accessor_array(doc,binary,p['attributes']['POSITION'])
            for p in source_mesh['primitives'] if doc['materials'][p['material']]['name'].startswith('OV_Grip')])
        distance,_ = cKDTree(grip).query(accessor_array(doc,binary,a['POSITION']))
        keep = (distance < .03)[faces].any(1)
    ordinary = decimator.collapse
    def collapse(points, faces, target):
        used,local = np.unique(faces,return_inverse=True)
        ms = pymeshlab.MeshSet()
        ms.add_mesh(pymeshlab.Mesh(vertex_matrix=points[used], face_matrix=local.reshape(-1,3).astype(np.int32),
                                  f_scalar_array=(~keep).astype(float)))
        ms.compute_selection_by_condition_per_face(condselect='fq > 0.5')
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=max(12,int(target)), qualitythr=.3,
            preserveboundary=True,boundaryweight=100,preservenormal=True,preservetopology=True,
            optimalplacement=False,planarquadric=True,selected=True)
        distance,nearest = cKDTree(points[used]).query(ms.current_mesh().vertex_matrix())
        assert distance.max() < 1e-9
        out = used[nearest][ms.current_mesh().face_matrix()]
        assert {tuple(sorted(f)) for f in faces[keep]} <= {tuple(sorted(f)) for f in out}
        return out
    if keep.any(): decimator.collapse = collapse
    try:
        return subset_primitive(doc,binary,primitive,*decimate_primitive(doc,binary,primitive,ratio))
    finally:
        decimator.collapse = ordinary

for level, ratio in enumerate(ratios, 1):
    mesh = {'name': f'{stem}_LOD{level}', 'primitives': []}
    for prim in source_mesh['primitives']:
        mesh['primitives'].append(contact_collapse(prim,ratio))
    base['extras']['openyamm_lods'].append(len(doc['meshes'])); doc['meshes'].append(mesh)
    counts.append(triangles(doc, len(doc['meshes'])-1))
assert all(a > b for a,b in zip(counts, counts[1:])), counts
# Match the colour surfaces exactly; distinct mesh indices satisfy the shadow-chain contract.
for level, mi in enumerate([node['mesh']] + base['extras']['openyamm_lods']):
    shadow = {'name':f'{stem}_Shadow{level}','primitives':copy.deepcopy(doc['meshes'][mi]['primitives'])}
    base['extras']['openyamm_shadow_lods'].append(len(doc['meshes'])); doc['meshes'].append(shadow)
built = work / 'built.glb'
write_glb(built, doc, compact(doc, binary))
print(stem, counts, flush=True)
for script, args in [
    ('unwrap_lods.py', [built,node['name'],work/'bake','1:1024,2:512,3:256']),
    ('transfer_textures.py', [built,node['name'],work/'bake']),
    ('apply_bake.py', [built,node['name'],work/'bake',P/'export'/f'{stem}.glb','1,2,3']),
]:
    subprocess.run([sys.executable,str(SHARED/script),*map(str,args)],check=True)
final, payload = read_glb(P/'export'/f'{stem}.glb')
payload = bytearray(payload)
for mi in final['meshes'][node['mesh']]['extras']['openyamm_lods']:
    for prim in final['meshes'][mi]['primitives']:
        if not material_maps(final['materials'][prim['material']]) and 'TEXCOORD_0' in prim['attributes']:
            index = prim['attributes']['TEXCOORD_0']
            values = np.frombuffer(accessor_bytes(final,payload,index),dtype=np.float32)
            prim['attributes']['TEXCOORD_0'] = append_accessor(final,payload,final['accessors'][index],np.clip(values,0,1).tobytes())
base_final = final['meshes'][node['mesh']]
for level,(mi,si) in enumerate(zip([node['mesh']]+base_final['extras']['openyamm_lods'],base_final['extras']['openyamm_shadow_lods'])):
    final['meshes'][si] = {'name':f'{stem}_Shadow{level}','primitives':copy.deepcopy(final['meshes'][mi]['primitives'])}
if stem == 'overseer_arc_maul':
    root = final['meshes'][node['mesh']]['extras']
    root['openyamm_lods'].pop(); root['openyamm_shadow_lods'].pop()
    keep = sorted({n['mesh'] for n in final['nodes'] if 'mesh' in n} |
                  {i for m in final['meshes'] for key in ('openyamm_lods','openyamm_shadow_lods') for i in m.get('extras',{}).get(key,[])})
    remap = {old:new for new,old in enumerate(keep)}
    final['meshes'] = [final['meshes'][i] for i in keep]
    for n in final['nodes']:
        if 'mesh' in n: n['mesh'] = remap[n['mesh']]
    for m in final['meshes']:
        for key in ('openyamm_lods','openyamm_shadow_lods'):
            if key in m.get('extras',{}): m['extras'][key] = [remap[i] for i in m['extras'][key]]
    final,payload = compact_materials(final,payload)
    counts = counts[:3]
write_glb(P/'export'/f'{stem}.glb',final,payload)
original, ob = read_glb(source)
original_prims = {original['materials'][p['material']]['name']:p for p in original['meshes'][0]['primitives']}
for after in final['meshes'][node['mesh']]['primitives']:
    before = original_prims[final['materials'][after['material']]['name']]
    for key in before['attributes']:
        assert accessor_bytes(original, ob, before['attributes'][key]) == accessor_bytes(final, payload, after['attributes'][key])
    assert accessor_bytes(original, ob, before['indices']) == accessor_bytes(final, payload, after['indices'])
for before, after in zip(original.get('animations',[]), final.get('animations',[])):
    assert before['channels'] == after['channels']
    for a,b in zip(before['samplers'],after['samplers']):
        for key in ('input','output'):
            assert accessor_bytes(original,ob,a[key]) == accessor_bytes(final,payload,b[key])
(work/'result.json').write_text(json.dumps({'source':str(source),'ratios':ratios,'triangles':counts,
    'route':'shared MeshLab subset collapse, xatlas UV, nearest-facing texture transfer',
    'silhouette_review':'pending'},indent=2)+'\n')

if body:
    from embed_burn import embed_burn
    embed_burn(P/'export'/f'{stem}.glb', P/'export'/f'{stem}.glb')
