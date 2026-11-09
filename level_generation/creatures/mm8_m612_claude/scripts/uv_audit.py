import json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
d,b=read_glb(P/'export/mm8_m612.glb');p=d['meshes'][0]['primitives'][0]
uv=accessor_array(d,b,p['attributes']['TEXCOORD_0']);pos=accessor_array(d,b,p['attributes']['POSITION'])
faces=accessor_array(d,b,p['indices']).reshape(-1,3)
assert np.isfinite(uv).all() and uv.min()>=-1e-5 and uv.max()<=1.00001
tri=uv[faces]*[2080,1024];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];area=np.abs(e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0])*.5
geo=np.linalg.norm(np.cross(pos[faces[:,1]]-pos[faces[:,0]],pos[faces[:,2]]-pos[faces[:,0]]),axis=1)*.5
counts=np.zeros((1024,2080),np.uint16)
for a,v in zip(area,tri):
    if a<1:continue
    lo=np.maximum(np.floor(v.min(0)).astype(int),0);hi=np.minimum(np.ceil(v.max(0)).astype(int),[2080,1024])
    x,y=np.meshgrid(np.arange(lo[0],hi[0])+.5,np.arange(lo[1],hi[1])+.5);pts=np.stack([x,y],-1)
    ds=[]
    for i in range(3):
        e=v[(i+1)%3]-v[i];delta=pts-v[i]
        ds.append((e[0]*delta[...,1]-e[1]*delta[...,0])/max(np.linalg.norm(e),1e-12))
    ds=np.stack(ds);inside=(ds>1).all(0)|(ds< -1).all(0)
    counts[lo[1]:hi[1],lo[0]:hi[0]]+=inside
covered=int((counts>0).sum());overlap=int((counts>1).sum())
report={'triangles':len(faces),'zero_area_geometry':int((geo<1e-12).sum()),'zero_area_uv':int((area<1e-8).sum()),
    'uv_area_pixels_p1_p50_p99':np.percentile(area,[1,50,99]).tolist(),'interior_texels':covered,
    'overlapping_interior_texels':overlap,'overlap_fraction':overlap/max(covered,1),
    'atlas':[2080,1024],'boundary_exclusion_pixels':1,'note':'Interior overlap test excludes shared chart edges.'}
assert report['zero_area_geometry']==0 and report['zero_area_uv']==0,report
assert report['overlap_fraction']<.001,report
(P/'work/uv_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
