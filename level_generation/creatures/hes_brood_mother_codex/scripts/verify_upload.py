"""Verify the precise static upload against the gated animated rest mesh and viewer manifest."""
import contextlib
import hashlib
import importlib.util
import io
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

P=Path(__file__).resolve().parents[1]
REPO=P.parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes

rig=Glb(P/'work/texture_ready.glb');upload=Glb(P/'texturing/brood_mother_upload.glb')
meshes=load_meshes(rig);static=load_meshes(upload)
triangles=np.concatenate([m.rest[m.faces] for m in meshes])
uploaded=np.concatenate([m.rest[m.faces] for m in static])
assert len(triangles)==len(uploaded)<=15000
dist,ids=cKDTree(uploaded.mean(1)).query(triangles.mean(1))
assert len(set(ids))==len(ids),'Static upload face mapping must be bijective'
errors=[]
for k in range(3):
 errors.append(np.linalg.norm(triangles-np.roll(uploaded[ids],k,axis=1),axis=2).max(1))
error=float(np.min(errors,axis=0).max())
assert error<1e-5,error
assert not upload.doc.get('skins') and not upload.doc.get('animations') and not upload.doc.get('materials')
assert all('TEXCOORD_0' not in prim['attributes'] for mesh in upload.doc['meshes'] for prim in mesh['primitives'])
assert {n for n,*_ in rig.clips()}=={'Standing','Fidget','Attack','Hit','Death','Dead'}
gates=json.loads((P/'review/texture_ready_gates.json').read_text())
sockets=json.loads((P/'review/texture_ready_sockets.json').read_text())
for report in (gates,sockets):
 assert report['status']=='pass' and report['sha256']==rig.sha256
assert len(gates['clips'])==6
weight_error=max(float(abs(rig.accessor(prim['attributes']['WEIGHTS_0']).sum(1)-1).max())
                 for mesh in rig.doc['meshes'] for prim in mesh['primitives'])
assert weight_error<1e-5
source=REPO/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'
spec=importlib.util.spec_from_file_location('winding',source);winding=importlib.util.module_from_spec(spec);spec.loader.exec_module(winding)
out=io.StringIO()
with contextlib.redirect_stdout(out):bad=winding.check(rig.path)
assert bad==0
(P/'review/winding.txt').write_text(out.getvalue())
points=np.concatenate([m.rest for m in meshes])
report={'rig':'work/texture_ready.glb','rig_sha256':rig.sha256,
 'upload':'texturing/brood_mother_upload.glb','upload_sha256':upload.sha256,
 'editable_master':'work/texture_ready.blend',
 'editable_sha256':hashlib.sha256((P/'work/texture_ready.blend').read_bytes()).hexdigest(),
 'triangles':len(triangles),'face_mapping':'bijective, same winding, cyclic vertex order allowed',
 'maximum_face_vertex_error_m':error,'raw_weight_sum_error':weight_error,
 'bounds_blender_m':[points.min(0).tolist(),points.max(0).tolist()],
 'clips':{n:float(t1-t0) for n,a,t0,t1 in rig.clips()},'inverted_closed_parts':bad,
 'motion_gates':gates['status'],'socket_gates':sockets['status'],'status':'pass'}
(P/'review/upload_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
