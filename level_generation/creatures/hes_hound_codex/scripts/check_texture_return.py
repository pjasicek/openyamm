"""Verify Meshy's static texture return matches the frozen upload before using any returned maps."""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes
upload=Glb(PROJECT/'export/hound_neutral_upload.glb')
returned=Glb(PROJECT/'meshy/body_texture_v1/model_urls_glb.glb')
def corners(glb):
    meshes=load_meshes(glb);assert len(meshes)==1
    mesh=meshes[0];p=glb.doc['meshes'][mesh.index]['primitives'];assert len(p)==1
    uv=glb.accessor(p[0]['attributes']['TEXCOORD_0'])
    return mesh.rest[mesh.faces],uv[mesh.faces]
a,ua=corners(upload);b,ub=corners(returned);assert len(a)==len(b)
# The service may recenter and uniformly normalize its static output; the animated master never changes.
ac=(a.min((0,1))+a.max((0,1)))/2;bc=(b.min((0,1))+b.max((0,1)))/2
scale=float(np.max(np.ptp(a.reshape(-1,3),axis=0))/np.max(np.ptp(b.reshape(-1,3),axis=0)))
b=(b-bc)*scale+ac
distance,ids=cKDTree(b.mean(1)).query(a.mean(1));assert len(np.unique(ids))==len(a),'Ambiguous face match'
b=b[ids];ub=ub[ids]
corner_map=np.linalg.norm(a[:,:,None,:]-b[:,None,:,:],axis=-1).argmin(2)
b=np.take_along_axis(b,corner_map[:,:,None],axis=1)
ub=np.take_along_axis(ub,corner_map[:,:,None],axis=1)
geometry=float(np.linalg.norm(a-b,axis=-1).max());uv_error=float(np.max(np.abs(ua-ub)))
report={'upload_sha256':upload.sha256,'return_sha256':returned.sha256,'triangles':len(a),
        'return_scale_to_upload':scale,'max_geometry_error_m':geometry,'max_uv_error':uv_error,
        'maps_only_transfer':True}
(PROJECT/'work/texture_correspondence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));assert geometry<1e-4 and uv_error<1e-4,'Retexture changed geometry or UVs'
