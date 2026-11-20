"""Validate final exported rest contacts, exact transition boundaries and unchanged binding calibration."""
import bpy,json,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;report={'clip_boundaries':{},'head_contact_method':'nearest-surface candidate, confirmed inside by at least three of four ray-parity directions (quiver has a double-sided open lip)','head_contacts_cm':{},'calibration':{}}
def act(n,f):
 a=bpy.data.actions[n];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f))
act('Standing',0);ref={b.name:(b.matrix.to_quaternion(),b.head.copy())for b in r.pose.bones}
for name in ['Walking','Attack','Cast','Hit','Death','Fidget']:
 end=bpy.data.actions[name].frame_range[1];out=[]
 for f in ([0]if name=='Death'else[0,end]):
  act(name,f);angles=[];pos=[];relative=[];root_delta=r.pose.bones['B_Pelvis'].head-ref['B_Pelvis'][1]
  for b in r.pose.bones:
   if b.name=='Arrow' or b.name=='Socket_Arrow_Release':continue
   q,v=ref[b.name];da=math.degrees(q.rotation_difference(b.matrix.to_quaternion()).angle);angles.append(min(da,360-da));pos.append((b.head-v).length);relative.append((b.head-v-root_delta).length)
  out.append({'frame':float(f),'max_joint_rotation_difference_deg':max(angles),'max_joint_position_difference_m':max(pos),'max_relative_position_difference_m':max(relative)})
  assert max(angles)<.1 and max(pos)<.003 and max(relative)<1e-5,(name,f,max(angles),max(pos))
 report['clip_boundaries'][name]=out
feet={s:[]for s in 'LR'}
for f in range(25):
 act('Walking',f)
 for s in 'LR':feet[s].append((r.pose.bones[f'B_{s}_Foot'].head-r.pose.bones['B_Pelvis'].head).y)
stride=float(2*np.mean([max(v)-min(v)for v in feet.values()]));report['calibration']={'measured_stride_m':stride,'previous_binding_stride_m':1.5946765,'new_binding_stride_m':stride,'retained_scale':106.382287,'upright_height_world':1.6989782874*106.382287,'native_height_world':256*.699997}
# Hair/head against the quiver and carried arrows through every exported motion's authored samples.
body=bpy.data.objects['Body'];piece=[x.value for x in body.data.attributes['piece'].data];gn={g.index:g.name for g in body.vertex_groups};heads=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if gn[g.group]=='B_Head')>.5];faces=[tuple(f.vertices)for f in body.data.polygons if all(piece[i]in([4]+list(range(13,20)))for i in f.vertices)]
for a in bpy.data.actions:
 worst=0;worst_info=None;raw_worst=0
 for f in np.linspace(0,float(a.frame_range[1]),math.ceil(a.frame_range[1]*48/30)+1):
  act(a.name,float(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy()for x in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(v,faces)
  for i in heads:
   p,n,idx,d=tree.find_nearest(v[i],.03)
   if p is not None and (v[i]-p).dot(n)<-.7*d and d>worst:
    raw_worst=max(raw_worst,d)
    # The open quiver lip has coincident inner/outer faces. A single nearest normal is not an inside test.
    inside=0
    for direction in [(1,.371,.123),(-1,.217,.623),(.137,1,.341),(.539,-1,.269)]:
     direction=Vector(direction).normalized();start=v[i].copy();count=0
     for k in range(20):
      hit,normal,face,distance=tree.ray_cast(start,direction)
      if hit is None:break
      count+=1;start=hit+direction*.00001
     inside+=count%2
    if inside>=3:worst=d;worst_info={'frame':float(f),'vertex':i,'piece':piece[i],'point':list(v[i]),'nearest':list(p),'hit_piece':piece[faces[idx][0]]}
 report['head_contacts_cm'][a.name]=worst*100
 print('HEAD CONTACT',a.name,worst,worst_info,'raw_nearest_normal_depth',raw_worst);assert worst<=.01,(a.name,worst)
(P/'review/round2/transitions_and_head.json').write_text(json.dumps(report,indent=2));print('ROUND1 TRANSITIONS',report)
# Final exported model views, including an explicit horizontal floor witness beneath both feet.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_arc1_a.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
for mat in bpy.data.materials:
 if mat.node_tree:
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
common.workbench_clay(sc,textured=True);a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
sc.render.film_transparent=True;common.render_views(str(P/'review/round2/standing_alpha'),.85,1.85,views=('front',),resolution=(680,1000));sc.render.film_transparent=False
# A horizontal line at Z=0 remains visible in orthographic side and front sole closeups.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.003));ground=bpy.context.object;ground.scale=(1,.6,.005);ma=bpy.data.materials.new('Floor');ma.diffuse_color=(.12,.23,.17,1);ground.data.materials.append(ma)
common.render_views(str(P/'review/round2/soles'),.12,.50,views=('front','left'),resolution=(800,600))
