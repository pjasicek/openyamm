"""Fit the far mesh back to the accepted surface without adding vertices or changing weights."""
import bpy,math,json,os,runpy,subprocess,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/round3';O=R/'far_snap';O.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=O/'renders';C.O.mkdir(exist_ok=True);C.PHYSICAL=False;C.TIER_DIR=P/'work'
def pose():
 rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);bpy.context.view_layer.update();return rig
bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'));pose();trees={};floors={}
for name in ['Body','Axe','Shield']:
 ob=bpy.data.objects[name];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[ob.matrix_world@v.co for v in m.vertices];trees[name]=BVHTree.FromPolygons(co,[tuple(f.vertices) for f in m.polygons]);floors[name]=min(v.z for v in co);ev.to_mesh_clear()
records=[]
for bias in [0.,.002,.004,.006,.008]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'far_fit_correct/lod3.blend'));rig=pose()
 for name in ['Body','Axe','Shield']:
  ob=bpy.data.objects[name];names=[g.name for g in ob.vertex_groups];matrices={b.name:rig.matrix_world@b.matrix@rig.data.bones[b.name].matrix_local.inverted()@rig.matrix_world.inverted()@ob.matrix_world for b in rig.pose.bones};grip=rig.matrix_world@rig.pose.bones['B_R_Hand' if name=='Axe' else 'B_L_Hand'].head
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();current=[ob.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear()
  for v,p in zip(ob.data.vertices,current):
   if name=='Body' and any(('Hand' in names[g.group] or 'Finger' in names[g.group]) and g.weight>.3 for g in v.groups):continue
   if name!='Body' and (p-grip).length<.13:continue
   hit,n,fi,d=trees[name].find_nearest(p)
   if d>.04:continue
   q=hit+n*bias;q.z=max(q.z,floors[name]);M=Matrix(np.zeros((4,4)).tolist())
   for g in v.groups:M+=matrices[names[g.group]]*g.weight
   assert (M@v.co-p).length<.0001
   v.co=M.inverted()@q
  ob.data.update()
 path=O/f'bias_{bias:.3f}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));E=O/f'export_{bias:.3f}';os.environ.update(FIGC_EXPORT_SOURCE=str(path),FIGC_EXPORT_DIR=str(E));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');out=C.render(E/'mm6_figc_lod0.glb',3,f'bias_{bias:.3f}');mp=O/f'bias_{bias:.3f}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'export_comparison/reference_lod3'),str(out),str(mp)],check=True);m=json.loads(mp.read_text());pooled=sum(v['iou']*v['reference_foreground_pixels'] for v in m['views'])/sum(v['reference_foreground_pixels'] for v in m['views']);record={'bias_m':bias,'triangles':893,'pooled_iou':pooled,'minimum_iou':m['minimum_iou'],'blend':str(path.relative_to(P))};records.append(record);(O/'curve.json').write_text(json.dumps(records,indent=2));print('FAR_SNAP',record,flush=True)
