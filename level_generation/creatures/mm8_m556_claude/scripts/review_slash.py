"""Measure the authored edge path and clearance in every release subframe."""
from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Wasp_Rig'];body=bpy.data.objects['Wasp'];sc=bpy.context.scene;sc.render.fps=48
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
bind=rig.data.bones['Sword'].matrix_local.inverted();names={g.index:g.name for g in body.vertex_groups};tip=Vector((.263,-.466,.459));heel=Vector((.263,-.145,.459));grip=Vector((.263,-.091,.459));edge=Vector((1,0,0));rows=[];clearances=[];collisions=[];surface_clearances=[]
# Ignore the gripping hand and arm; the blade must clear the head, torso and shield throughout the cut.
excluded={'Sword','Hand_L','ForeArm_L','Claw1_L','Claw2_L','Claw3_L'}
indices=[f.index for f in body.data.polygons if all(not any(names[g.group] in excluded and g.weight>.1 for g in body.data.vertices[v].groups) for v in f.vertices)]
blade_ids={v.index for v in body.data.vertices if v.co.y<-.16 and any(names[g.group]=='Sword' and g.weight>.99 for g in v.groups)}
blade_edges=[e.vertices[:] for e in body.data.edges if all(v in blade_ids for v in e.vertices)]
for t in np.arange(0,1.25001,1/192):
 frame=t*48;sc.frame_set(int(frame),subframe=frame-int(frame));mat=rig.pose.bones['Sword'].matrix@bind;h=mat@heel;v=mat@tip;g=mat@grip
 forward=rig.pose.bones['Thorax'].matrix@rig.data.bones['Thorax'].matrix_local.inverted();f=forward.to_3x3()@Vector((0,-1,0));yaw=float(np.degrees(np.arctan2(f.x,-f.y)))
 row=dict(t=float(t),tip=list(v),heel=list(h),grip=list(g),blade_edge=list((mat.to_3x3()@edge).normalized()),thorax_yaw_degrees=yaw,thorax=list(rig.pose.bones['Thorax'].head));rows.append(row)
 if .40<=t<=1.10:
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());vs=[v.co[:] for v in ev.data.vertices];tree=BVHTree.FromPolygons(vs,[body.data.polygons[i].vertices[:] for i in indices]);dist=min(tree.find_nearest(h.lerp(v,q))[3] for q in np.linspace(.08,1,24));clearances.append((float(t),float(dist)))
  surface_clearances.append((float(t),min(tree.find_nearest(ev.data.vertices[i].co)[3] for i in blade_ids)))
  for ia,ib in blade_edges:
   va=ev.data.vertices[ia].co;vb=ev.data.vertices[ib].co;delta=vb-va
   if delta.length>1e-7 and tree.ray_cast(va,delta.normalized(),delta.length)[0] is not None:collisions.append((float(t),ia,ib))
cut=[r for r in rows if .65<=r['t']<=1.01];tips=np.array([r['tip'] for r in cut]);heels=np.array([r['heel'] for r in cut]);delta=np.diff(tips,axis=0);directions=(tips-heels);directions/=np.linalg.norm(directions,axis=1)[:,None];speed=np.linalg.norm(delta,axis=1);transverse=np.linalg.norm(np.cross(delta,directions[:-1]),axis=1)/np.maximum(speed,1e-9);edgealign=np.abs(np.sum(np.array([r['blade_edge'] for r in cut[:-1]])*delta,axis=1))/np.maximum(speed,1e-9)
report=dict(rows=rows,release_tip_displacement=(tips[-1]-tips[0]).tolist(),release_path_length_m=float(speed.sum()),release_transverse_fraction=float(np.average(transverse,weights=speed)),edge_alignment=float(np.average(edgealign,weights=speed)),body_yaw_range_degrees=[min(r['thorax_yaw_degrees'] for r in rows),max(r['thorax_yaw_degrees'] for r in rows)],minimum_blade_body_clearance=min(clearances,key=lambda x:x[1]),frames_checked=len(rows),blade_body_intersections=collisions,minimum_blade_vertex_clearance=min(surface_clearances,key=lambda x:x[1]))
(P/'review/slash_path.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
assert tips[-1,0]-tips[0,0]<-.4 and tips[-1,2]-tips[0,2]<-.35,'Sword must sweep diagonally across and down'
assert report['release_transverse_fraction']>.65,'Slash must move across the blade, not thrust along it'
assert np.ptp([r['thorax_yaw_degrees'] for r in rows])>45,'Torso must contribute a visible wind-up and release'

assert not collisions,('Sword intersects body/shield',collisions[:5])
assert report['edge_alignment']>.8,'The cutting edge must lead the sweep'
