"""Transfer corrected motion and fit reduced foot/grip geometry without changing shared UVs."""
import bpy,sys,runpy,json,math,shutil,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
for name in ['round4_author.py','round4_repair.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
selection=json.loads((P/'review/round4/lod_selection.json').read_text());reports={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round4/prefit_lod{level}.blend'));r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];sc=bpy.context.scene
 r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/round4/repaired.blend'),link=False)as(src,dst):dst.actions=src.actions
 for action in bpy.data.actions:action.use_fake_user=True
 a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 me=ob.data;pv=np.array([x.value for x in me.attributes['piece'].data]);gn=[g.name for g in ob.vertex_groups]
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();xyz=[v.co.copy()for v in mesh.vertices];ev.to_mesh_clear()
 matrices={g.index:np.array(r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted())for g in ob.vertex_groups if g.name in r.pose.bones}
 def move(v,target):
  skin=sum((matrices[g.group]*g.weight for g in v.groups if g.group in matrices),np.zeros((4,4)));v.co=Vector((np.linalg.inv(skin)@np.r_[np.array(target),1])[:3]);xyz[v.index]=target.copy()
 # Match the low-detail toe direction to the near foot, with ankle transition above the sole.
 yaw={1:{'L':10,'R':10},3:{'L':10,'R':7}}.get(level,{})
 for side,degrees in yaw.items():
  center=r.pose.bones[f'B_{side}_Foot'].head;Q=Matrix.Rotation(math.radians(degrees),3,'Z')
  for v in me.vertices:
   w=sum(g.weight for g in v.groups if gn[g.group]in[f'B_{side}_Foot',f'B_{side}_Toe0'])
   if w>.1:move(v,xyz[v.index].lerp(center+Q@(xyz[v.index]-center),min(1,w/.8)))
 fitted=0
 if level>=2:
  me.calc_loop_triangles();inv=r.data.bones['Bow'].matrix_local.inverted();faces=[list(f.vertices)for f in me.loop_triangles if all(pv[i]==201 and abs((inv@me.vertices[i].co).z)<.105 for i in f.vertices)];tree=BVHTree.FromPolygons(xyz,faces)
  hand=[v for v in me.vertices if pv[v.index]==3 and sum(g.weight for g in v.groups if gn[g.group]=='B_L_Hand'or gn[g.group].startswith('B_L_Finger'))>.8]
  fullfaces=[list(f.vertices)for f in me.loop_triangles if all(pv[i]==201 for i in f.vertices)];solid=BVHTree.FromPolygons(xyz,fullfaces)
  bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3])
  weights=np.zeros((len(me.vertices),5));parts=['B_L_Hand','B_L_Finger0','B_L_Finger1','B_L_Finger2','B_L_Finger4']
  for v in me.vertices:
   for j,name in enumerate(parts):weights[v.index,j]=sum(g.weight for g in v.groups if gn[g.group]==name or ('Finger'in name and gn[g.group].startswith(name)))
  tris=[list(f.vertices)for f in me.loop_triangles if all(weights[i].sum()>.3 for i in f.vertices)]
  for iteration in range(10):
   # Resolve coarse triangle interiors as well as their vertices against the wrapped grip.
   for ids in tris:
    for bc in bary:
     point=Vector(bc@np.array([xyz[i]for i in ids]));hit,n,_,d=solid.find_nearest(point)
     if d<.018 and (point-hit).dot(n)<-d*.7:
      delta=hit+n*.0006-point
      for i,w in zip(ids,bc):
       if w:move(me.vertices[i],xyz[i]+delta*(w/float(bc@bc))*.6);fitted+=1
   for j in range(5):
    best=(1e9,None,None,None,None)
    for ids in tris:
     for bc in bary:
      if float(bc@weights[ids,j])<=.3:continue
      point=Vector(bc@np.array([xyz[i]for i in ids]));hit,n,_,d=tree.find_nearest(point)
      if d<best[0]:best=(d,ids,bc,point,hit+n*.001)
    d,ids,bc,point,target=best
    if ids and d>.0018:
     for i,w in zip(ids,bc):
      if w:move(me.vertices[i],xyz[i]+(target-point)*(w/float(bc@bc)));fitted+=1
 # Preserve the already fitted corpse floor after toe-direction correction.
 a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 if level==1:
  for f in [45,45.625,46,46.5]:
   sc.frame_set(int(f),subframe=f%1);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();points=[v.co.copy()for v in mm.vertices];ev.to_mesh_clear()
   matrices={g.index:np.array(r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted())for g in ob.vertex_groups if g.name in r.pose.bones}
   for v in me.vertices:
    if pv[v.index]!=202 and points[v.index].z<.0005:move(v,points[v.index]+Vector((0,0,.0005-points[v.index].z)))
 me.update();r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();path=P/selection[str(level)]['blend'];bpy.ops.wm.save_as_mainfile(filepath=str(path));reports[str(level)]={'foot_yaw_rotation_deg':yaw,'grip_vertices_fit':fitted}
 if level==0:
  shutil.copyfile(path,P/'work/master.blend');runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__');shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
 else:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r;ob.name=ob.data.name='Lizard'
  bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/round4/lod_refit.json').write_text(json.dumps(reports,indent=2))
