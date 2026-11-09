"""Fit independently rebaked LOD geometry at the batch's actual switch sizes."""
import bpy,bmesh,sys,json,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_bake as B
from reduction_render import render
rows=[]
for level,ratio,pixels in [(2,.249,220),(3,.099,88)]:
 source=P/'work/final_lod0.blend';ref=P/f'review/reduction/lod{level}_reference'
 render(source,ref,P/'work/reduction/lod0_850charts',pixels)
 bpy.ops.wm.open_mainfile(filepath=str(source));C.reset();report={'level':level,'height_pixels':pixels,'meshes':{}}
 for name,kind in [('Body','body'),('SpearMesh','spear'),('BucklerMesh','buckler')]:
  obj=bpy.data.objects[name];me=obj.data
  if kind!='body':
   bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002);bm.to_mesh(me);bm.free()
  C.protect(obj,kind);contour=list(obj.get('contour_vertices',[]));group=obj.vertex_groups.get('_reduction_protect')
  if group:obj.vertex_groups.remove(group)
  group=obj.vertex_groups.new(name='_reduction_protect');protected=[]
  if kind=='body':
   piece=np.array([x.value for x in me.attributes['piece'].data]);protected=list(np.flatnonzero(np.isin(piece,[1,10])))
   C.activate('Standing',0);r=bpy.data.objects['Rig'];ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());pm=ev.to_mesh();inv=r.pose.bones['Spear'].matrix.inverted();positions=np.array([tuple(inv@v.co)for v in pm.vertices]);ev.to_mesh_clear();C.reset()
   radial=np.linalg.norm(positions[:,:2],axis=1);gn={g.index:g.name for g in obj.vertex_groups}
   for digit in range(5):
    ids=[v.index for v in me.vertices if any(gn[g.group].startswith(f'B_R_Finger{digit}')and g.weight>.3 for g in v.groups)and abs(positions[v.index,2])<.07]
    protected+=sorted(ids,key=lambda i:abs(radial[i]-.016))[:2]
   for side in [-1,1]:
    ids=[v.index for v in me.vertices if piece[v.index]==0 and v.co.z<.009 and v.co.x*side>0]
    if ids:
     for axis in [0,1]:
      protected.extend([min(ids,key=lambda i:me.vertices[i].co[axis]),max(ids,key=lambda i:me.vertices[i].co[axis])])
  else:
   r=bpy.data.objects['Rig'];inv=r.data.bones['Spear'if kind=='spear'else'Buckler'].matrix_local.inverted();co=np.array([tuple(inv@v.co)for v in me.vertices])
   if kind=='spear':
    for z in [-.07,.07]:
     ids=np.flatnonzero(abs(co[:,2]-z)<.04)
     if len(ids):
      for axis in [0,1]:protected.extend([int(ids[np.argmin(co[ids,axis])]),int(ids[np.argmax(co[ids,axis])])])
   else:
    ids=np.flatnonzero(co[:,1]>.021)
    if len(ids):protected=[int(ids[np.argmax(co[ids,1])])]
  group.add(list(range(len(me.vertices))),.2 if level==1 else .05,'REPLACE')
  if protected:group.add(list(set(map(int,protected))),1.,'REPLACE')
  C.activate('Standing',0);ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());pm=ev.to_mesh();pos=np.array([tuple(v.co)for v in pm.vertices]);ev.to_mesh_clear();C.reset()
  grid={};cell=1.7129090557573363/pixels*1.25
  for idx in contour:
   key=tuple(np.round(pos[idx]/cell).astype(int));grid.setdefault(key,idx)
  group.add(list(grid.values()),.98,'REPLACE')
  before=C.triangles(obj);C.reduce(obj,ratio,True);report['meshes'][kind]={'triangles':C.triangles(obj),'base':before,'protected_vertices':len(set(protected))}
  B.bake(obj,P/f'work/reduction/lod{level}_weighted'/kind)
 tex=P/f'work/reduction/lod{level}_weighted';dest=P/f'work/lod{level}_weighted.blend';out=P/f'review/reduction/lod{level}_weighted'
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True);render(dest,out,tex,pixels)
 visual=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(ref),str(out)],text=True));v=list(visual['views'].values());unions=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in v];pooled=sum(x['iou']*u for x,u in zip(v,unions))/sum(unions);visual['pooled_iou']=pooled;visual['pass']=pooled>=.97;report['visual']=visual;report['blend']=str(dest.relative_to(P));report['textures']=str(tex.relative_to(P));report['pass']=visual['pass']and all(x['triangles']/x['base']<=[0,.55,.25,.1][level]for x in report['meshes'].values());rows.append(report);(P/'review/reduction/lod_weighted_curve.json').write_text(json.dumps(rows,indent=2));print('LOD_CURVE',level,report['meshes'],pooled,visual['min_ssim'],report['pass'],flush=True)
