"""Actual exported triangles versus the all-animation sac bounding cylinder, at 60 Hz."""
import json
import sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,sample_grid
args=sys.argv[sys.argv.index('--')+1:]
g=Glb(P/args[0]);meshes=load_meshes(g)
sac=Glb(P.parent/'hes_sentinel_codex/export/hes_brood_sac.glb');sacmeshes=load_meshes(sac)
radius=height=0.
for name,a,t0,t1 in sac.clips():
 for pose in sac.pose(a,sample_grid(t0,t1,60)):
  for mesh in sacmeshes:
   points=mesh.posed(pose);radius=max(radius,float(np.linalg.norm(points[:,:2],axis=1).max()));height=max(height,float(points[:,2].max()))


def clipped(poly,z,above):
    out=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        ia=(a[2]>=z) if above else (a[2]<=z)
        ib=(b[2]>=z) if above else (b[2]<=z)
        if ia:out.append(a)
        if ia!=ib:out.append(a+(b-a)*((z-a[2])/(b[2]-a[2])))
    return np.array(out)


def radial_gap(poly,centre):
    xy=poly[:,:2]-centre[:2]
    a=xy;b=np.roll(xy,-1,axis=0);d=b-a
    cross=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    if np.all(cross>=-1e-9) or np.all(cross<=1e-9):return 0.
    t=np.clip(-np.sum(a*d,axis=1)/np.maximum(np.sum(d*d,axis=1),1e-20),0,1)
    return float(np.linalg.norm(a+t[:,None]*d,axis=1).min())


assert abs(radial_gap(np.array([[2,0,0],[3,1,0],[3,-1,0]]),np.zeros(3))-2)<1e-9
assert radial_gap(np.array([[-1,-1,0],[1,-1,0],[0,1,0]]),np.zeros(3))==0
layout=json.loads((P/'socket_layout.json').read_text());pads={s['name']:np.array(s['top_centre_blender_m']) for s in layout['sockets']}
report={'asset':args[0],'sha256':g.sha256,'sac_sha256':sac.sha256,'sample_hz':60,
        'sac_radius_m':radius,'sac_height_m':height,'method':'Exact triangle clipping against height slab, radial distance to convex projected polygon; bounding cylinder encloses every sampled sac pose and yaw.',
        'sockets':{},'failures':[]}
for name,c in pads.items():
 cap=next(m for m in meshes if m.label.startswith('Socket_'+name+'/'))
 top=cap.rest[np.abs(cap.rest[:,2]-cap.rest[:,2].max())<1e-6]
 centre=(top[:,:2].min(0)+top[:,:2].max(0))/2
 top_radius=np.linalg.norm(top[:,:2]-centre,axis=1).max()
 assert np.linalg.norm(np.r_[centre,top[:,2].mean()]-c)<1e-5
 assert np.ptp(top[:,2])<1e-6
 assert top_radius*np.cos(np.pi/48)>radius+.04
 report['sockets'][name]={'measured_top_centre_m':np.r_[centre,top[:,2].mean()].tolist(),'cap_inscribed_radius_m':float(top_radius*np.cos(np.pi/48)),
                          'minimum_clear_radius_above_cap_m':1.,'worst':None}
for clip,a,t0,t1 in g.clips():
 times=sample_grid(t0,t1,60)
 for t,pose in zip(times,g.pose(a,times)):
  for mesh in meshes:
   if mesh.label.startswith('Socket_'):continue
   points=mesh.posed(pose);tris=points[mesh.faces];lo=tris.min(1);hi=tris.max(1)
   for name,c in pads.items():
    record=report['sockets'][name];bound=min(record['minimum_clear_radius_above_cap_m'],1.0)
    mask=(hi[:,2]>c[2]+.002)&(lo[:,2]<c[2]+height)
    mask&=(hi[:,0]>c[0]-bound)&(lo[:,0]<c[0]+bound)&(hi[:,1]>c[1]-bound)&(lo[:,1]<c[1]+bound)
    for index in np.where(mask)[0]:
     poly=clipped(tris[index],c[2]+.002,True)
     if len(poly)<3:continue
     poly=clipped(poly,c[2]+height,False)
     if len(poly)<3:continue
     gap=radial_gap(poly,c)
     if gap<record['minimum_clear_radius_above_cap_m']:
      record['minimum_clear_radius_above_cap_m']=gap
      record['worst']={'clip':clip,'time_s':float(t),'mesh':mesh.label,'triangle':int(index)}
 print('SOCKET',clip,{n:round(r['minimum_clear_radius_above_cap_m'],4) for n,r in report['sockets'].items()},flush=True)
for name,record in report['sockets'].items():
 record['clear_radius_is_lower_bound']=record['worst'] is None
 record['sac_clearance_lower_bound_m']=record['minimum_clear_radius_above_cap_m']-radius
 if record['minimum_clear_radius_above_cap_m']<.64:
  report['failures'].append({'socket':name,**record})
report['status']='pass' if not report['failures'] else 'needs_revision'
(P/'review'/ (Path(args[0]).stem+'_sockets.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
