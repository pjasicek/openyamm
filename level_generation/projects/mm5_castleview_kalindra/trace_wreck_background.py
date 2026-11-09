"""Identify distant BModel faces at selected pixels of the retained native river-bank capture."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def trace():
    # The retained snapshot matches this exact gameplay capture, independently of later builds.
    native = PROJECT/'review/ranger_yard_v3/before/implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    capture = json.loads((PROJECT/'review/gameplay/mm5_wreck_background_context_v2.json').read_text())
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==capture['native_sha256']
    save = PROJECT/'review/wreck_background_v1/view.oysav'
    saved = yaml.safe_load(subprocess.check_output(
        [str(PROJECT.parents[2]/'build/tools/openyamm_levelgen_inspect_save'),str(save)],text=True))
    origin = np.array(saved['outdoor']['party_position'],dtype=float)
    origin[2] += 176  # OutdoorGameView default eye height; capture uses the ordinary party camera.
    yaw,pitch = capture['pose'][3:]
    forward = np.array([math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),math.sin(pitch)])
    right = np.array([math.sin(yaw),-math.cos(yaw),0])
    up = np.cross(right,forward)
    payload = parse_odm_file(native)['payload']
    triangles, ids = [], []
    for i,model in enumerate(payload['bmodels']):
        vertices = np.array([[v[a] for a in 'xyz'] for v in model['vertices']])
        for j,face in enumerate(model['faces']):
            if face['attributes']&0x2000:
                continue
            points = vertices[face['vertex_indices']]
            for k in range(1,len(points)-1):
                triangles.append([points[0],points[k],points[k+1]])
                ids.append((i,j))
    tri = np.array(triangles)
    a,ab,ac = tri[:,0],tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    results = []
    for x,y in [(1410,135),(1340,210),(1570,175),(900,150)]:
        direction = forward+right*((x-800)/600*math.tan(math.pi/6))+up*((600-y)/600*math.tan(math.pi/6))
        direction /= np.linalg.norm(direction)
        h = np.cross(np.broadcast_to(direction,ac.shape),ac)
        det = np.sum(ab*h,axis=1)
        valid = np.abs(det)>1e-8
        f = np.divide(1,det,out=np.zeros_like(det),where=valid)
        s = origin-a
        u = f*np.sum(s*h,axis=1)
        q = np.cross(s,ab)
        v = f*np.sum(direction*q,axis=1)
        t = f*np.sum(ac*q,axis=1)
        valid &= (u>=0)&(v>=0)&(u+v<=1)&(t>=0)
        hit = min(np.flatnonzero(valid),key=lambda i:t[i])
        model_index,face_index = ids[hit]
        model = payload['bmodels'][model_index]
        face = model['faces'][face_index]
        results.append({'pixel':[x,y],'nativeModel':model_index,'nativeName':model['name'],'face':face_index,
                        'texture':face['texture_name'],'attributes':face['attributes'],
                        'rayDistance':round(t[hit],2),'position':(origin+t[hit]*direction).round(3).tolist()})
    assert all(r['nativeName'].startswith(('BMODEL_town_corner','BMODEL_town_wall')) for r in results[:3])
    output = PROJECT/'review/wreck_background_v1'
    output.mkdir(exist_ok=True)
    report = {'nativeSha256':digest,'capture':'../gameplay/mm5_wreck_background_context_v2.json',
              'eyePosition':origin.tolist(),'verticalFovDegrees':60,'resolution':[1600,1200],
              'hits':results,'conclusion':'Pale upper-right silhouettes are the town corner tower and curtain wall.',
              'limits':'Nearest visible BModel intersections at sampled pixels; no terrain/billboard occlusion test. '
                       'The selected pixels are exposed geometry in the inspected screenshot. '
                       'This identifies geometry/materials, not the final regional lighting or skyline acceptance.'}
    (output/'ray_identity.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    trace()
