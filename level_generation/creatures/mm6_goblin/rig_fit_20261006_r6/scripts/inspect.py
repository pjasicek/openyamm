import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');OUT=ROOT/'rig_fit_20261006_r6'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'anatomy_20261006_r5/goblin_anatomy_r5.blend'))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];scene=bpy.context.scene
core=body.vertex_groups['Component_0'].index;skin={v.index for v in body.data.vertices if any(g.group==core for g in v.groups)}
region={i for i in skin if .12<abs(body.data.vertices[i].co.x)<.42 and 1.03<body.data.vertices[i].co.z<1.325}
rest=np.array([tuple(v.co) for v in body.data.vertices]);records=[]
for i in sorted(region):
 v=body.data.vertices[i];records.append(dict(i=i,co=list(v.co),weights={body.vertex_groups[g.group].name:g.weight for g in v.groups if body.vertex_groups[g.group].name in arm.data.bones}))
edges=[e for e in body.data.edges if all(i in region for i in e.vertices)]
poses={}
for c,t in [('Standing',0),('Meshy_Walk',.5),('Attack',.25),('Hit',.375)]:
 a=bpy.data.actions[c];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];frame=1+t*192;scene.frame_set(int(frame),subframe=frame-int(frame))
 m=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;points=np.array([tuple(v.co) for v in m.vertices]);rows=[]
 for e in edges:
  i,j=e.vertices;before=np.linalg.norm(rest[i]-rest[j]);after=np.linalg.norm(points[i]-points[j])
  if before>.0001:rows.append(dict(vertices=[i,j],rest_length=float(before),pose_length=float(after),stretch=float(after/before)))
 poses[c]=dict(time=t,largest_edge_stretches=sorted(rows,key=lambda r:r['stretch'],reverse=True)[:20],positions={str(i):points[i].tolist() for i in region})
slices={}
for z in [.836,.785,.72,.697,.655,.624]:
 vs=[v.co for v in body.data.vertices if v.index in skin and abs(v.co.x)<.31 and abs(v.co.y)<.3 and abs(v.co.z-z)<.02]
 slices[str(z)]=dict(count=len(vs),lo=[min(v[i] for v in vs) for i in range(3)],hi=[max(v[i] for v in vs) for i in range(3)])
report=dict(vertices=records,poses=poses,pelvis_slices=slices,bones={b.name:dict(parent=b.parent.name if b.parent else None,head=list(b.head_local),tail=list(b.tail_local),matrix=list(map(list,b.matrix_local))) for b in arm.data.bones if any(x in b.name for x in ['Spine','Shoulder','Arm','Skirt.'])})
(OUT/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(vertices=len(records),pelvis_slices=slices,largest_stretches={c:r['largest_edge_stretches'][:3] for c,r in poses.items()})),flush=True)
# Reproduce the rear shoulder defect in Standing, and distinguish posed skin from rest geometry.
a=bpy.data.actions['Standing'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Shoulder neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1)
for pos,power in [((2,4,4),500),((-3,2,2),300),((1,-3,3),180)]:
 light=bpy.data.lights.new('Shoulder light','AREA');light.energy=power;light.size=4;o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.08,.04,1.12))-o.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('Shoulder camera',bpy.data.cameras.new('Shoulder camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO'
for name,rest_pose,center,offset,scale in [('before_back',False,(.08,.04,1.17),(0,4,.2),.8),('before_rest_back',True,(0,.04,1.18),(0,4,.2),.9),('before_skirt_back',False,(.08,.025,.74),(0,4,-1.3),.9)]:
 arm.data.pose_position='REST' if rest_pose else 'POSE';bpy.context.view_layer.update();target=Vector(center);camera.location=target+Vector(offset);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(OUT/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)
