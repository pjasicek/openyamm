"""Inspect the three reported faults without modifying the selected master."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/feedback_20261011';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
co=np.array([v.co[:] for v in me.vertices]);vg={g.index:g.name for g in o.vertex_groups}
def action(a):
 r.animation_data.action=a
 if a is not None:r.animation_data.action_slot=a.slots[0]
def evaluated():
 ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ob.to_mesh();a=np.array([v.co[:] for v in m.vertices]);ob.to_mesh_clear();return a
def camera(name,c,d,scale):
 cam=common.ortho_camera(name,Vector(c)+Vector(d),(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-Vector(d)).to_track_quat('-Z','Y')
 sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=700;sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
report={'pieces':{},'tabard_motion':{},'hand_rest':{}}
for n in [1,4,5,9,10,11,13,14,18]:
 ids=np.where(pv==n)[0]
 if len(ids):report['pieces'][n]={'vertices':len(ids),'bounds':[co[ids].min(0).tolist(),co[ids].max(0).tolist()]}
tab=np.where(pv==9)[0]
for a in bpy.data.actions:
 if a.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 action(a);traj=[];bones=[]
 for f in range(max(2,int(a.frame_range[1]))+1):
  sc.frame_set(f);m=np.array(r.pose.bones['B_Pelvis'].matrix.inverted());X=evaluated()[tab];traj.append(X@m[:3,:3].T+m[:3,3])
  bones.append({b.name:{'location':list(b.location),'quat':list(b.rotation_quaternion)} for b in r.pose.bones if b.name.startswith('Tabard_')})
 X=np.array(traj);speed=np.linalg.norm(np.diff(X,axis=0),axis=2);jerk=np.linalg.norm(np.diff(X,n=2,axis=0),axis=2)
 report['tabard_motion'][a.name]={'max_delta_mm':float(speed.max()*1000),'max_second_delta_mm':float(jerk.max()*1000),'worst_frame':int(np.unravel_index(np.argmax(jerk),jerk.shape)[0]+1)}
 np.save(out/(a.name+'_tabard_before.npy'),X)
 if a.name=='Standing':(out/'standing_tabard_bones.json').write_text(json.dumps(bones,indent=1))
action(None)
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
for b in r.data.bones:
 if b.name.startswith('B_L_Finger') or b.name=='B_L_Hand':
  report['hand_rest'][b.name]={'head':list(b.head_local),'tail':list(b.tail_local)}
# Material-coloured pieces expose intersecting layers independently of texture.
o.data.materials.clear()
colors=[(.55,.55,.55,1),(.4,.1,.1,1),(.2,.6,.2,1),(.1,.35,.8,1),(.7,.55,.1,1)]
for i,c in enumerate(colors):
 m=bpy.data.materials.new('diagnostic'+str(i));m.diffuse_color=c;o.data.materials.append(m)
for f in me.polygons:
 n=int(pv[f.vertices[0]]);f.material_index={1:0,9:1,11:2,10:3,18:4}.get(n,0)
common.workbench_clay(sc,textured=False);sc.display.shading.show_cavity=False
for ob in sc.objects:
 if ob.type=='MESH' and ob!=o:ob.hide_render=True
camera('hand_rest_front',(.55,-.075,.875),(0,-1,0),.27)
camera('hand_rest_back',(.55,-.075,.875),(0,1,0),.27)
camera('belt_rest',(-.01,-.10,1.00),(0,-1,.12),.55)
action(bpy.data.actions['Standing']);sc.frame_set(0)
c=(r.pose.bones['B_L_Hand'].head+r.pose.bones['B_L_Finger2'].head)/2
camera('hand_standing_back',c,(0,1,.15),.26)
camera('belt_standing',(-.01,-.10,1.02),(0,-1,.12),.55)
(out/'diagnosis.json').write_text(json.dumps(report,indent=1))
print('DIAGNOSIS',json.dumps(report),flush=True)
