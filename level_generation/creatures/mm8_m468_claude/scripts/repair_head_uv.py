"""Separate the recorded overlapping ear patches by integer UV translation; normal tangents stay unchanged."""
from pathlib import Path
import bpy,numpy as np,json,sys,runpy
from mathutils import Vector

p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'));m=bpy.data.objects['Body'].data;uv=m.uv_layers['HeadUV'].data;N=1280
pairs=json.loads((p/'review/uv_diagnostic.json').read_text())['HeadUV']['overlap_pairs'];move=sorted({f for row in pairs for f in row['faces']});h=np.load(p/'work/uvraster_HeadUV.npz')['piece']>=0;mask=np.flipud(h);h=np.zeros((N,N),bool);h[:1024,:1024]=mask;
for _ in range(8):
 old=h.copy();h[1:]|=old[:-1];h[:-1]|=old[1:];h[:,1:]|=old[:,:-1];h[:,:-1]|=old[:,1:]
shifts=[]
for pi in sorted(move,key=lambda i:-m.polygons[i].area):
 poly=m.polygons[pi];P=np.array([tuple(uv[i].uv) for i in poly.loop_indices])*1024;lo=np.floor(P.min(0)).astype(int)-4;hi=np.ceil(P.max(0)).astype(int)+4;w,ht=hi-lo+1
 integral=np.pad(h.astype(int),((1,0),(1,0))).cumsum(0).cumsum(1);areas=integral[ht:,w:]-integral[:-ht,w:]-integral[ht:,:-w]+integral[:-ht,:-w];spots=np.argwhere(areas==0);assert len(spots),('No free head patch rectangle',pi,w,ht)
 y,x=spots[0];d=np.array([x,y])-lo
 for li in poly.loop_indices:uv[li].uv+=Vector(d/1024)
 h[max(0,y-4):min(N,y+ht+4),max(0,x-4):min(N,x+w+4)]=True
 shifts.append({'face':pi,'from':lo.tolist(),'to':[int(x),int(y)],'size':[int(w),int(ht)],'delta':d.tolist()})
for poly in m.polygons:
 if m.attributes['head'].data[poly.index].value:
  for li in poly.loop_indices:uv[li].uv*=1024/N
(p/'work/head_uv_shifts.json').write_text(json.dumps(shifts,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_textured_uv.blend'));print('MOVED_UV_FACES',len(shifts))
sys.argv=['uv_raster.py','--',str(p/'work/rig_textured_uv.blend'),'HeadUV','1024'];runpy.run_path(str(p/'scripts/uv_raster.py'),run_name='__main__')
sys.argv=['bake_ao.py','--',str(p/'work/rig_textured_uv.blend'),'1024'];runpy.run_path(str(p/'scripts/bake_ao.py'),run_name='__main__')
