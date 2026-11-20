"""Sample the shared gate's complete pistol volume for a smooth grip-fitting collision field."""
import importlib.util
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gates',P.parent/'claude_shared/gates/run_gates.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
glb=g.Glb(P/'work/attachments/overseer_pulse_pistol.glb');mesh=next(m for m in g.load_meshes(glb) if '/colour' in m.label);surface=g.Surface(mesh,np.ones(len(mesh.rest),bool)).build(mesh.rest)
canonical=g.transform(np.linalg.inv(g.C),mesh.rest);original=np.load(P/'work/weapons/pulse_pistol_grip_mesh.npz')['vertices']
assert np.max(np.abs(np.array([canonical.min(0),canonical.max(0)])-np.array([original.min(0),original.max(0)])))<1e-6
axes=[np.arange(lo,hi+.00125,.0025) for lo,hi in [(-.055,.055),(-.385,.10),(-.10,.285)]]
points=np.stack(np.meshgrid(*axes,indexing='ij'),-1).reshape(-1,3);values=[]
for offset in range(0,len(points),2048):
 distance,_=surface.signed(g.transform(g.C,points[offset:offset+2048]));values.append(np.where(np.isfinite(distance),distance,.05))
 if offset%32768==0:print('PISTOL_SDF',offset,len(points),flush=True)
np.savez_compressed(P/'work/weapons/pulse_pistol_sdf.npz',x=axes[0],y=axes[1],z=axes[2],distance=np.concatenate(values).reshape(*map(len,axes)),source_sha256=glb.sha256)
print('PISTOL_SDF_DONE',flush=True)
