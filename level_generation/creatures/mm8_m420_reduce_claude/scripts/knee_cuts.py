"""Knee bend rows restored by planar cuts (copy of ../mm8_m412_claude/scripts/refine_knee_lods.py, which does this for
LOD1-3 after the LOD build): faces of the thigh/calf (> 95 % leg weight) crossing each height plane are split,
UVs, normals and skin weights interpolated, area unchanged. The reduction removes the same rows from LOD0.
Usage: knee_cuts.py <glb, rewritten in place> lod0|lods  (lod0: the Pirate mesh and its shadow LOD0, planes every 4 cm
from 0.44 to 0.72 m; lods: LOD1-3 colour and shadow with the creature's planes)"""
import json
import sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor
path = Path(sys.argv[1]); MODE = sys.argv[2]
doc, raw = read_glb(path)
binary = bytearray(raw)
node = next(n for n in doc['nodes'] if n.get('name') == 'Pirate')
joints = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
leg_ids = {i for i, n in enumerate(joints) if n in [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf')]}
extras = doc['meshes'][node['mesh']].get('extras', {})
report = []
PLANES = {0: (.44,.48,.52,.56,.60,.64,.68,.72), 1: (.44,.50,.56,.62,.68,.74), 2: (.48,.56,.64,.72), 3: (.48,.60,.72)}
for level in ((0,) if MODE == 'lod0' else (1, 2, 3)):
    planes = PLANES[level]
    shadow = extras.get('openyamm_shadow_lods', [])
    meshes = [node['mesh']] if level == 0 else [extras['openyamm_lods'][level-1]]
    if len(shadow) > level:
        meshes.append(shadow[level])
    for mi in meshes:
        mesh = doc['meshes'][mi]
        before = sum(doc['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])
        for primitive in mesh['primitives']:
            attrs = primitive['attributes']
            arrays = {}
            for semantic, index in attrs.items():
                a = doc['accessors'][index]
                dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
                arrays[semantic] = np.frombuffer(accessor_bytes(doc,binary,index),dtype=dtype).reshape(a['count'],-1)
            weight_sets = sorted(k for k in arrays if k.startswith('WEIGHTS_'))
            vertices = [{k: a[i].astype(float) for k,a in arrays.items()} for i in range(len(arrays['POSITION']))]
            index = doc['accessors'][primitive['indices']]
            dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4'}[index['componentType']]
            faces = np.frombuffer(accessor_bytes(doc,binary,primitive['indices']),dtype=dtype).reshape(-1,3).tolist()
            original_faces = np.asarray(faces)
            xyz = arrays['POSITION'][original_faces]
            original_area = np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1).sum()
            def weights(v):
                result = {}
                for key in weight_sets:
                    for joint, weight in zip(v[key.replace('WEIGHTS','JOINTS')],v[key]):
                        if weight > 0:
                            result[int(joint)] = result.get(int(joint),0)+float(weight)
                return result
            def leg_vertex(i):
                return sum(w for j,w in weights(vertices[i]).items() if j in leg_ids) > .95
            for plane in planes:
                cache = {}
                def split(a,b):
                    edge = tuple(sorted((a,b)))
                    if edge in cache:
                        return cache[edge]
                    va,vb = vertices[a],vertices[b]
                    da,db = va['POSITION'][1]-plane,vb['POSITION'][1]-plane
                    if abs(da)<.001:
                        return a
                    if abs(db)<.001:
                        return b
                    t = da/(da-db)
                    v = {k: va[k]*(1-t)+vb[k]*t for k in arrays if not k.startswith(('JOINTS','WEIGHTS'))}
                    for k in ('NORMAL','TANGENT'):
                        if k in v:
                            v[k][:3] /= max(np.linalg.norm(v[k][:3]),1e-12)
                    if 'TANGENT' in v:
                        v['TANGENT'][3] = va['TANGENT'][3]
                    blend = {}
                    for data,factor in ((va,1-t),(vb,t)):
                        for j,w in weights(data).items():
                            blend[j] = blend.get(j,0)+w*factor
                    ordered = sorted(blend.items(),key=lambda x:-x[1])
                    assert len(ordered) <= 4*len(weight_sets)
                    ordered += [(0,0)]*(4*len(weight_sets)-len(ordered))
                    for n,key in enumerate(weight_sets):
                        v[key] = np.array([w for _,w in ordered[n*4:n*4+4]])
                        v[key.replace('WEIGHTS','JOINTS')] = np.array([j for j,_ in ordered[n*4:n*4+4]])
                    assert abs(sum(v[k].sum() for k in weight_sets)-1) < 1e-5
                    cache[edge] = len(vertices)
                    vertices.append(v)
                    return cache[edge]
                refined = []
                for face in faces:
                    d = [vertices[i]['POSITION'][1]-plane for i in face]
                    if min(d)>=-.001 or max(d)<=.001 or sum(leg_vertex(i) for i in face) < 2:
                        refined.append(face)
                        continue
                    for sign in (-1,1):
                        polygon = []
                        for n,a in enumerate(face):
                            b = face[(n+1)%3]
                            da,db = d[n],d[(n+1)%3]
                            if sign*da>=-.001:
                                polygon.append(a)
                            if da*db<0 and abs(da)>=.001 and abs(db)>=.001:
                                polygon.append(split(a,b))
                        polygon = list(dict.fromkeys(polygon))
                        for n in range(1,len(polygon)-1):
                            tri = [polygon[0],polygon[n],polygon[n+1]]
                            xyz = np.array([vertices[i]['POSITION'] for i in tri])
                            if np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))>1e-10:
                                refined.append(tri)
                faces = refined
            xyz = np.array([v['POSITION'] for v in vertices])[np.asarray(faces)]
            refined_area = np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1).sum()
            assert abs(refined_area-original_area) < max(1e-7, original_area*1e-5), (mesh['name'], original_area, refined_area)
            for semantic,index in list(attrs.items()):
                source = dict(doc['accessors'][index])
                array = np.array([v[semantic] for v in vertices], dtype=arrays[semantic].dtype)
                source['count'] = len(array)
                source.pop('min',None);source.pop('max',None)
                if semantic == 'POSITION':
                    source['min'],source['max'] = array.min(0).tolist(),array.max(0).tolist()
                attrs[semantic] = append_accessor(doc,binary,source,array.tobytes())
            indices = np.asarray(faces,dtype='<u4').ravel()
            primitive['indices'] = append_accessor(doc,binary,{'componentType':5125,'type':'SCALAR','count':len(indices)},indices.tobytes())
        after = sum(doc['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])
        report.append({'mesh':mesh['name'],'before':before,'after':after})
write_glb(path,doc,binary)
print('KNEE_LODS',report)
