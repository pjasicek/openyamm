"""Project coarse-mesh vertices out of measured floor/head contacts, leaving animation and weights fixed."""
import bpy,json,sys,math,os,runpy,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/round3';D=R/'far_repaired88';D.mkdir(exist_ok=True);source=Path(os.environ['FIGC_REPAIR_SOURCE']);bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;objects=[bpy.data.objects[n] for n in ['Body','Axe','Shield']];body=objects[0];pv=[a.value for a in body.data.attributes['piece'].data];head=[v.index for v in body.data.vertices if pv[v.index] in [3,10,11,15,16] or (pv[v.index]==0 and v.co.z>1.48)];shoulders=[tuple(f.vertices) for f in body.data.polygons if all(pv[i] in [7,8] for i in f.vertices)];initial={o.name:np.array([tuple(v.co) for v in o.data.vertices]) for o in objects};changes=[]
def inside(p,tree):
 votes=0
 for d in [Vector((.932,.217,.291)).normalized(),Vector((-.313,.901,.299)).normalized(),Vector((.243,-.372,.896)).normalized()]:
  origin=p+d*1e-6;hits=0
  for _ in range(40):
   hit=tree.ray_cast(origin,d,5)[0]
   if hit is None:break
   hits+=1;origin=hit+d*1e-5
  votes+=hits%2
 return votes>=2
for sweep in range(6):
 corrections=0
 for role in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
  act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for frame in np.arange(0,float(act.frame_range[1])+.001,.625):
   scene.frame_set(int(frame),subframe=float(frame%1));matrices={b.name:rig.matrix_world@b.matrix@rig.data.bones[b.name].matrix_local.inverted()@rig.matrix_world.inverted() for b in rig.pose.bones};coords={};transforms={}
   for ob in objects:
    names=[g.name for g in ob.vertex_groups];co=[];ms=[]
    for v in ob.data.vertices:
     M=Matrix(np.zeros((4,4)).tolist())
     for g in v.groups:M+=matrices[names[g.group]]@ob.matrix_world*g.weight
     p=M@v.co
     if p.z<.0015:
      q=p.copy();q.z=.0015;v.co=M.inverted()@q;p=q;corrections+=1
     co.append(p);ms.append(M)
    coords[ob.name]=co;transforms[ob.name]=ms
   co=coords['Body'];tree=BVHTree.FromPolygons(co,shoulders)
   for i in head:
    p=co[i];hit,n,fi,d=tree.find_nearest(p,.05)
    if hit is not None and d>.0085 and (p-hit).dot(n)<-.707*d and inside(p,tree):body.data.vertices[i].co=transforms['Body'][i].inverted()@(p+n*(d-.0085));corrections+=1
 for ob in objects:ob.data.update()
 changes.append({'sweep':sweep,'projections':corrections});print('CONTACT_REPAIR',changes[-1],flush=True)
 if corrections==0:break
record={'sweeps':changes,'maximum_rest_displacement_mm':{o.name:float(np.linalg.norm(np.array([tuple(v.co) for v in o.data.vertices])-initial[o.name],axis=1).max()*1000) for o in objects}};(D/'repair.json').write_text(json.dumps(record,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(D/'lod3.blend'));os.environ.update(FIGC_EXPORT_SOURCE=str(D/'lod3.blend'),FIGC_EXPORT_DIR=str(D/'export'));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=D/'renders';C.O.mkdir(exist_ok=True);C.PHYSICAL=False;C.TIER_DIR=R/'reference_tier_textures';C.cal['body_diameter_m']=1.763883397;folder=C.render(D/'export/mm6_figc_lod0.glb',3,'repaired');subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'switch_height/reference_lod3'),str(folder),str(D/'metrics.json')],check=True)
