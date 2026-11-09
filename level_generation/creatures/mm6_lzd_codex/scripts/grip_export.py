"""Exported left finger clearance and both hands' adjacency ownership."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[g.name for g in body.vertex_groups];me=body.data;W=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
bad={}
for side in 'LR':
 hand=W[:,names.index(f'B_{side}_Hand')]>.5;distal=[i for i,n in enumerate(names)if n.startswith(f'B_{side}_Finger')and n.endswith('2')and len(n.rsplit('Finger',1)[1])==2];tip=W[:,distal].sum(1)>.5;bad[side]=sum(bool((hand[e.vertices[0]]and tip[e.vertices[1]])or(hand[e.vertices[1]]and tip[e.vertices[0]]))for e in me.edges)
assert max(bad.values())==0,bad
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();inverse=rig.pose.bones['Bow'].matrix.inverted();co=np.array([tuple(inverse@(body.matrix_world@v.co))for v in m.vertices]);ev.to_mesh_clear();radii={}
for digit in [0,1,2,4]:
 ids=[i for i,n in enumerate(names)if n.startswith(f'B_L_Finger{digit}')];mask=(W[:,ids].sum(1)>.6)&(abs(co[:,2])<.075);assert mask.any(),digit;radii[str(digit)]=float(np.linalg.norm(co[mask,:2],axis=1).min())
motion=json.loads((P/'review/round3_motion_gate.json').read_text());contact=max(v for c in motion['clips'].values()for v in c['grip_distance_max_m'].values())
report={'direct_hand_to_distal_edges':bad,'exported_finger_skin_radius_m':radii,'actual_wrap_contact_max_m':contact,'passed':contact<=.003 and max(bad.values())==0}
(P/'review/grip_export.json').write_text(json.dumps(report,indent=2));print('GRIP_EXPORT',report);assert report['passed'],report
