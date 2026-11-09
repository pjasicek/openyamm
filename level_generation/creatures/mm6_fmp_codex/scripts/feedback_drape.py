"""Replace the collapsed lower death skirt with a consistent, smoothly flattened cloth tube."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/feedback_v3'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/feedback_motion.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];s=bpy.context.scene;m=o.data
piece=np.array([x.value for x in m.attributes['piece'].data]);chains=json.loads(s['skirt_chains']);bones=[n for c in chains for n in c['bones']]
faces={k:[list(f.vertices) for f in m.polygons if piece[f.vertices[0]] in k] for k in [(1,7),(5,6)]}
def coords():
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();co=np.array([v.co[:] for v in me.vertices]);e.to_mesh_clear();return co
def action(name):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];return a
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
restpel=r.data.bones['B_Pelvis'].matrix_local;axis=Vector((-.004,-.025,1.035));rows=[]
action('Death')
for f in range(121):
 s.frame_set(f);r.animation_data.action=None
 old={n:r.pose.bones[n].matrix.copy() for n in bones};T=r.pose.bones['B_Pelvis'].matrix@restpel.inverted();start=T@axis
 foot=(r.pose.bones['B_L_Foot'].head+r.pose.bones['B_R_Foot'].head)/2
 h=foot-start;h.z=0;h.normalize();w=h.cross(Vector((0,0,1)));Rworld=Matrix((w,Vector((0,0,1)),-h)).transposed()
 blend=smooth((f-20)/30)
 for c in chains:
  pts=[]
  for x,y,z in c['pts']:
   along=axis.z-z;t=along/.915
   center=start+h*along;center.z=(1-t)*start.z+t*.145
   target=center+w*(x-axis.x)*.9+Vector((0,0,(y-axis.y)*.32))
   target.z=max(.024,target.z)
   # Keep the waist ring attached exactly; let the drape settle over the next row.
   target=(T@Vector((x,y,z))).lerp(target,smooth(along/.28));pts.append(target)
  for k,n in enumerate(c['bones']):
   rb=r.data.bones[n];rotation=Rworld@rb.matrix_local.to_3x3();direction=(pts[k+1]-pts[k]).normalized()
   rotation=(rotation@Vector((0,1,0))).rotation_difference(direction).to_matrix()@rotation
   M=old[n].to_quaternion().slerp(rotation.to_quaternion(),blend).to_matrix().to_4x4();M.translation=old[n].translation.lerp(pts[k],blend)
   r.pose.bones[n].matrix=M;bpy.context.view_layer.update()
 rows.append({n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in bones});action('Death')
for f,row in enumerate(rows):
 for n,(q,loc) in row.items():
  b=r.pose.bones[n];b.rotation_quaternion=q;b.location=loc;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
s.frame_set(120);held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in (0,60):
 for n,(q,loc) in held.items():
  b=r.pose.bones[n];b.rotation_quaternion=q;b.location=loc;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=60
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
action('Death');report=[]
for f in np.arange(0,120.001,.5):
 s.frame_set(int(f),subframe=f%1);co=coords();cb=BVHTree.FromPolygons(co,faces[(1,7)]);sb=BVHTree.FromPolygons(co,faces[(5,6)]);overlap=cb.overlap(sb)
 report.append({'frame':float(f),'pairs':len(overlap),'floor':float(co[:,2].min())})
(R/'drape_fit.json').write_text(json.dumps(report,indent=2));print('DRAPE',report[::24],flush=True)
action('Standing');s.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/feedback_drape.blend'))
sys.path.insert(0,str(P/'scripts'));import common
common.workbench_clay(s);s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.6,.6,.6);s.render.resolution_x=900;s.render.resolution_y=900
action('Dead');s.frame_set(0)
for n,eye,target,scale in [('dead_top',(0,.50,4),(0,.50,.1),1.8),('dead_side',(3,.4,.8),(0,.4,.2),1.8),('dead_feet',(0,.88,4),(0,.88,.1),.85)]:
 cam=common.ortho_camera('probe',eye,(0,0,0),scale);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam;s.render.filepath=str(R/f'drape_{n}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
