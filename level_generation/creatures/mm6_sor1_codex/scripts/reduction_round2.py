"""Protected 10% LOD0 reduction candidate and eight-view textured comparison, no endpoint mutation."""
import bpy,bmesh,numpy as np,math,json,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/round2/reduction';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/production_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
me=body.data;co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);norm=np.array([v.normal[:] for v in me.vertices]);protected=np.isin(pv,[2,3,4,5,7,8,9,10,13,14,15,101,102])
for side in 'LR':
 for name in ['UpperArm','Forearm','Hand','Thigh','Calf']:
  point=np.array(rig.data.bones['B_'+side+'_'+name].head_local);protected|=np.linalg.norm(co-point,axis=1)<(.065 if name=='UpperArm' else .035)
# Protect eight-view silhouette edges; UV boundaries are retained by the dissolve step.
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.normal_update()
for e in bm.edges:
 if len(e.link_faces)!=2:protected[[v.index for v in e.verts]]=True;continue
 for angle in np.arange(8)*math.pi/4:
  direction=Vector((math.sin(angle),-math.cos(angle),0))
  if e.link_faces[0].normal.dot(direction)*e.link_faces[1].normal.dot(direction)<=0:
   protected[[v.index for v in e.verts]]=True;break
bm.free()
original=me.copy();before=sum(len(f.vertices)-2 for f in me.polygons)
vg=body.vertex_groups.new(name='_reducible');vg.add(np.where(~protected)[0].tolist(),1,'REPLACE')
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();edges=[e for e in bm.edges if all(not protected[v.index] for v in e.verts)]
bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.5),use_dissolve_boundaries=False,verts=[],edges=edges,delimit={'UV','MATERIAL','SEAM','SHARP'});bm.to_mesh(me);bm.free()
mod=body.modifiers.new('ProtectedCollapse','DECIMATE');mod.ratio=.90;mod.vertex_group='_reducible';mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
body.vertex_groups.remove(body.vertex_groups['_reducible']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
candidate=body.data;after=sum(len(f.vertices)-2 for f in candidate.polygons)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round2_reduction_90.blend'))
staff.hide_render=True
for o in bpy.data.objects:
 if o.type=='MESH' and o!=body:o.hide_render=True
common.workbench_clay(scene,textured=True);scene.render.film_transparent=True
scene.render.resolution_x=scene.render.resolution_y=768;scene.render.resolution_percentage=100
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(0)
cam=common.ortho_camera('ReductionCamera',(0,-6,.85),(math.pi/2,0,0),2.05);scene.camera=cam
for label,mesh in [('reference',original),('candidate_90',candidate)]:
 body.data=mesh
 for i in range(8):
  a=i*math.pi/4;cam.location=(6*math.sin(a),-6*math.cos(a),.85);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(out/f'{label}_{i}.png');bpy.ops.render.render(write_still=True)
body.data=candidate
(out/'candidate.json').write_text(json.dumps({'before_triangles':before,'after_triangles':after,'protected_vertices':int(protected.sum()),'total_vertices':len(protected),'candidate':'work/round2_reduction_90.blend','method':'0.5 degree planar dissolve with UV/material/seam/sharp delimiters, then 10 percent collapse; face/hands/shoulder accents, joint loops, soles and eight-view silhouette weighted protection; weights limited to eight and normalized','views':8,'resolution':768,'orthographic_height_m':2.05},indent=2))
print('REDUCTION',before,after,flush=True)
