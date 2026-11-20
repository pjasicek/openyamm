"""Taper covered trousers within the robe, retaining closed geometry and visible boots."""
import bpy,sys,shutil,json,numpy as np,runpy
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
records=[]
for level in [-1,0,1,2,3]:
 path=P/('work/round3/master.blend'if level<0 else f'work/round3/body_lod{level}.blend');backup=path.with_name(path.stem+'_before_clearance.blend')
 if not backup.exists():shutil.copyfile(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));C.reset();o=bpy.data.objects['Body'];part=[a.value for a in o.data.attributes['piece'].data];count=0
 for v in o.data.vertices:
  if part[v.index]not in [6,7]:continue
  t=float(np.clip((v.co.z-.34)/.20,0,1));t=t*t*(3-2*t)
  if t:v.co.x*=1-.45*t;v.co.y*=1-.45*t;count+=1
 if level==1:
  fit=np.load(P/'work/round3/shirt_fit_lod1.npz');kd=KDTree(len(fit['rest']))
  for i,c in enumerate(fit['rest']):kd.insert(c,i)
  kd.balance()
  for v in o.data.vertices:
   if part[v.index]!=1:continue
   c,i,d=kd.find(v.co)
   if d>2e-5:continue
   for group in list(v.groups):
    if o.vertex_groups[group.group].name!='_reduction_protect':o.vertex_groups[group.group].remove([v.index])
   for j,w in zip(fit['joints'][i],fit['weights'][i]):
    if w>1e-8:o.vertex_groups[str(fit['bones'][j])].add([v.index],float(w),'REPLACE')
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path));records.append({'level':level,'tapered_covered_vertices':count})
(P/'review/round3/leg_clearance.json').write_text(json.dumps({'method':'Taper covered trousers, preserving boot soles and all closed faces. Smooth transition above 0.34m, full factor 0.55 above 0.54m.','records':records},indent=2));runpy.run_path(str(P/'scripts/round3_export_selected.py'),run_name='__main__')
