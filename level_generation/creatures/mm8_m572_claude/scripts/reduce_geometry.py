"""Protected 10% reduction ladder on the weighted animated source; never overwrite its baseline."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
step=int(sys.argv[sys.argv.index('--')+1]);assert 1<=step<=20
OUT=P/'review/reduction';OUT.mkdir(exist_ok=True);label=f'step_{step:02d}';ratio=.47 if step==8 else .9**step
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for obj in bpy.data.objects:
 if obj.type=='LIGHT':obj.hide_render=True
bpy.context.view_layer.update()
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
reference=body.copy();reference.data=body.data.copy();reference.name='Reference';sc.collection.objects.link(reference)
me=body.data;baseline=len(me.polygons);co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data])
fixed=set(np.where((co[:,1]<-.135)|(co[:,2]<.065))[0])
main=np.where(pa==0)[0];tree=kdtree.KDTree(len(main))
for i in main:tree.insert(Vector(co[i]),int(i))
tree.balance()
for part in sorted(set(pa)):
 if part==0:continue
 ids=np.where(pa==part)[0]
 for dx in (-1,0,1):
  for dy in (-1,0,1):
   for dz in (-1,0,1):
    if dx or dy or dz:fixed.add(int(ids[np.argmax(co[ids]@np.array([dx,dy,dz]))]))
 if len(ids)<12:continue
 dist=np.array([tree.find(Vector(co[i]))[2] for i in ids]);fixed.update(int(i) for i in ids[dist>=np.quantile(dist,.88)])
fixed_co=[me.vertices[i].co.copy() for i in fixed]
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
protect=body.vertex_groups.new(name='ReductionProtection');protect.add([int(i) for i in fixed],1.,'REPLACE')
mod=body.modifiers.new('Reduce','DECIMATE');mod.ratio=ratio;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000.;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
body.vertex_groups.remove(body.vertex_groups['ReductionProtection']);bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
me=body.data;me.calc_loop_triangles()
assert len(me.materials)==3
for v in me.vertices:
 w=[g.weight for g in v.groups if g.weight>1e-7];assert len(w)<=4 and abs(sum(w)-1)<1e-5

def surface(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[p.co.copy() for p in m.vertices];f=[list(p.vertices) for p in m.polygons];ev.to_mesh_clear()
 return v,BVHTree.FromPolygons(v,f,all_triangles=True)
report={'step':step,'ratio':ratio,'triangles':len(me.loop_triangles),'source_triangles':baseline,'protected_vertices':len(fixed),'clips':{},'failed_checks':[]}
for act in bpy.data.actions:
 rig.animation_data.action=act;lo,hi=act.frame_range;errors=[];protected_errors=[];minz=1e9;worst={'error':0.}
 for frame in np.linspace(lo,hi,7):
  sc.frame_set(int(frame),subframe=frame%1);rv,rt=surface(reference);cv,ct=surface(body)
  protected_errors.extend(ct.find_nearest(rv[int(i)])[3] for i in fixed)
  for vertices,tree in [(cv,rt),(rv,ct)]:
   for v in vertices:
    err=tree.find_nearest(v)[3];errors.append(err)
    if err>worst['error']:worst={'error':err,'frame':float(frame),'position':list(v)}
  minz=min(minz,min(v.z for v in cv))
 vals=np.percentile(errors,[95,99,100]);report['clips'][act.name]={'surface_error':vals.tolist(),'minimum_z':minz,'worst':worst,'protected_max_error':max(protected_errors)}
 # Interior covert relief is recovered by the source-normal bake; contour tips stay strict.
 if vals[1]>.003 or vals[2]>.009 or max(protected_errors)>.001 or (act.name in ('Death','Dead') and minz<-.002):report['failed_checks'].append(act.name)
reference.hide_render=True;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.render.resolution_x=1000;sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReductionCamera',bpy.data.cameras.new('ReductionCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,clip,frame,target,scale,d in [('flight','Standing',8,(0,0,.20),1.35,(1,-1,.3)),('head','Attack',28,(0,-.18,.13),.28,(1,-1,.05)),('corpse','Dead',0,(0,0,.10),1.15,(1,-1,.5))]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);target=Vector(target);cam.location=target+Vector(d)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 for variant,obj in [('candidate',body),('baseline',reference)]:
  body.hide_render=obj!=body;reference.hide_render=obj!=reference;sc.render.filepath=str(OUT/f'{label}_{name}_{variant}.png');bpy.ops.render.render(write_still=True)
body.hide_render=False;bpy.data.objects.remove(reference,do_unlink=True)
for obj in list(bpy.data.objects):
 if obj.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(obj,do_unlink=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{label}.blend'))
(OUT/f'{label}.json').write_text(json.dumps(report,indent=2)+'\n')
print('REDUCTION',report['triangles'],'failures',report['failed_checks'],'worst',max(v['surface_error'][2] for v in report['clips'].values()))
