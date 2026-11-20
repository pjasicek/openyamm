"""Re-fit far-LOD sole patches to the unchanged planted Standing pose."""
import bpy,sys,shutil,json,numpy as np,runpy
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
report=[]
for level in [1,2,3]:
 path=P/f'work/round3/body_lod{level}.blend';backup=path.with_name(path.stem+'_before_soles.blend')
 if not backup.exists():shutil.copyfile(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];C.activate('Standing',0);co=np.array([v.co[:]for v in o.data.vertices]);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();posed=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();names=[g.name for g in o.vertex_groups]
 for side in 'LR':
  ids=np.array([v.index for v in o.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith((f'B_{side}_Foot',f'B_{side}_Toe0')))>.3]);low=co[ids,2].min();sole=ids[co[ids,2]<=low+.022]
  # A coherent rest sole, rather than extrapolating a plane through three decimation survivors.
  for vi in sole:o.data.vertices[int(vi)].co.z=.001
  for iteration in range(3):
   bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();posed=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();co=np.array([v.co[:]for v in o.data.vertices]);low=co[ids,2].min();sole=ids[co[ids,2]<=low+.005];y=co[sole,1];heel=sole[y>=np.quantile(y,.7)];toe=sole[y<=np.quantile(y,.3)];h=posed[heel].mean(0);t=posed[toe].mean(0);slope=(t[0]-h[0])/(t[1]-h[1]);center=posed[sole].mean(0);height=center[2]-.001
   for vi in ids:
    fade=float(np.clip((.18-co[vi,2])/.10,0,1))
    if not fade:continue
    delta=np.array([-slope*(posed[vi,1]-center[1]),0.,-height])*fade;M=np.zeros((3,3))
    for g in o.data.vertices[int(vi)].groups:
     n=names[g.group]
     if n in r.data.bones:M+=g.weight*np.array((r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted()).to_3x3())
    o.data.vertices[int(vi)].co+=Vector(np.linalg.solve(M,delta))
  report.append({'level':level,'side':side,'sole_vertices':len(sole),'remaining_yaw_slope_before_last_iteration':float(slope)})
 C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
(P/'review/round3/sole_refit.json').write_text(json.dumps(report,indent=2));runpy.run_path(str(P/'scripts/round3_export_selected.py'),run_name='__main__')
