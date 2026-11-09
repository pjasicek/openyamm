"""Reject UV foldovers by protecting their source patches before collapse."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
def overlaps(me):
 me.calc_loop_triangles();bad=set();report={}
 for slot in [0,1]:
  hits=np.full((1024,1024),-1,int);count=0
  for tri in me.loop_triangles:
   if me.polygons[tri.polygon_index].material_index!=slot:continue
   v=np.array([tuple(me.uv_layers['UVMap'].data[i].uv)for i in tri.loops]);v[:,1]=1-v[:,1];v*=1024
   lo=np.maximum(np.floor(v.min(0)).astype(int),0);hi=np.minimum(np.ceil(v.max(0)).astype(int),1023)
   if (hi<lo).any():continue
   x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=v;det=np.linalg.det(np.stack([b-a,c-a]))
   if abs(det)<1e-10:continue
   u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;w=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;mask=(u>1e-6)&(w>1e-6)&(u+w<1-1e-6);sub=hits[lo[1]:hi[1]+1,lo[0]:hi[0]+1];previous=sub[mask&(sub>=0)]
   if len(previous):bad.add(tri.polygon_index);bad.update(me.loop_triangles[int(t)].polygon_index for t in previous);count+=len(previous)
   sub[mask]=tri.index
  report[str(slot)]=count
 points=[me.vertices[i].co.copy()for f in bad for i in me.polygons[f].vertices]
 return points,report
curve=json.loads((S.OUT/'body_lod0_curve.json').read_text());extra=[];candidate=P/'work/round4/body_lod0_1.blend';trials=[]
for attempt in range(1,13):
 bpy.ops.wm.open_mainfile(filepath=str(candidate));points,report=overlaps(bpy.data.objects['Body'].data)
 if not points:break
 extra+=points
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/body_lod0_0.blend'));S.reset();body=bpy.data.objects['Body'];kd=KDTree(len(extra))
 for i,p in enumerate(extra):kd.insert(p,i)
 kd.balance();ids=[v.index for v in body.data.vertices if kd.find(v.co)[2]<.018];body.vertex_groups['_reduction_protect'].add(ids,1,'REPLACE')
 S.reduce(body,.925,planar=True);candidate=P/f'work/round4/body_lod0_uv925_{attempt}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate));newpoints,newreport=overlaps(body.data)
 row={'attempt':attempt,'extra_protected_vertices':len(ids),'triangles':S.triangles(body),'overlap_texels':newreport,'blend':str(candidate.relative_to(P))};trials.append(row);print('UVFIX',row,flush=True)
 if not newpoints:break
else:raise AssertionError('Could not carry UVs without overlap')
assert not overlaps(bpy.data.objects['Body'].data)[0]
S.CALIBRATION.clear();folder=S.OUT/'body_lod0'/'uv_protected_0925';S.render(folder,'body',0);metrics=S.evaluate(S.OUT/'body_lod0'/'reference',folder)
row={'step':'uv_protected_0925','triangles':S.triangles(bpy.data.objects['Body']),'ratio_to_original':S.triangles(bpy.data.objects['Body'])/curve['before'],'visual':metrics,'blend':str(candidate.relative_to(P)),'uv_overlap_texels':0}
curve['steps'].append(row)
for old in curve['steps']:
 if old['step'] in [1,2,'refine_05']:old['uv_gate_pass']=False if old['step']==1 else None
row['uv_gate_pass']=True;curve['uv_protection_trials_0925']=trials;(S.OUT/'body_lod0_curve.json').write_text(json.dumps(curve,indent=2)+'\n');print('UV_FINAL',row,flush=True);assert metrics['pass']
selection=json.loads((S.OUT/'selection.json').read_text());selection['body'][0]=row;(S.OUT/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')

