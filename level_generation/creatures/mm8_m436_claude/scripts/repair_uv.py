"""Separate measured UV overlaps by integer translations without changing tangent orientation."""
from pathlib import Path
import bpy,numpy as np,json,sys,runpy
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'));m=bpy.data.objects['Body'].data;N=1024
report=json.loads((p/'review/uv_diagnostic.json').read_text())
for name in ['UVMap','HeadUV']:
 uv=m.uv_layers[name].data;pairs=[set(row['faces']) for row in report[name]['overlap_pairs']];move=[]
 while pairs:
  counts={f:sum(f in pair for pair in pairs) for pair in pairs for f in pair};chosen=max(counts,key=counts.get);move.append(chosen);pairs=[pair for pair in pairs if chosen not in pair]
 h=np.flipud(np.load(p/f'work/uvraster_{name}.npz')['piece']>=0).copy();shifts=[]
 for _ in range(4):
  old=h.copy();h[1:]|=old[:-1];h[:-1]|=old[1:];h[:,1:]|=old[:,:-1];h[:,:-1]|=old[:,1:]
 for pi in sorted(move,key=lambda i:-m.polygons[i].area):
  poly=m.polygons[pi];P=np.array([tuple(uv[i].uv) for i in poly.loop_indices])*N;lo=np.maximum(0,np.floor(P.min(0)).astype(int)-2);hi=np.minimum(N-1,np.ceil(P.max(0)).astype(int)+2);w,ht=hi-lo+1
  integral=np.pad(h.astype(int),((1,0),(1,0))).cumsum(0).cumsum(1);areas=integral[ht:,w:]-integral[:-ht,w:]-integral[ht:,:-w]+integral[:-ht,:-w];spots=np.argwhere(areas==0);assert len(spots),('No free patch rectangle',name,pi,w,ht)
  y,x=spots[0];d=np.array([x,y])-lo
  for li in poly.loop_indices:uv[li].uv+=Vector(d/N)
  h[max(0,y-4):min(N,y+ht+4),max(0,x-4):min(N,x+w+4)]=True
  shifts.append({'face':pi,'from':lo.tolist(),'to':[int(x),int(y)],'size':[int(w),int(ht)],'delta':d.tolist()})
 (p/f'work/uv_shifts_{name}.json').write_text(json.dumps(shifts,indent=2));print('MOVED_UV_FACES',name,len(shifts))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
for name in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(p/'work/rig_textured_uv.blend'),name,'1024'];runpy.run_path(str(p/'scripts/uv_raster.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/validate_uv.py'),run_name='__main__')
sys.argv=['bake_ao.py','--',str(p/'work/rig_textured_uv.blend'),'1024'];runpy.run_path(str(p/'scripts/bake_ao.py'),run_name='__main__')
