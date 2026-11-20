"""Compare dense hand-surface samples against the original grip shaft envelopes at 48 Hz."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/round3';eq=json.loads((P/'work/equipment.json').read_text());left=json.loads((P/'work/grip_pose_left.json').read_text());bary=np.array([(i/4,j/4,1-(i+j)/4) for i in range(5) for j in range(5-i)]);result={}
for label,path in [('accepted',R/'before/work/export_validation.blend'),('selected',P/'work/export_validation.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;me.calc_loop_triangles();piece=[x.value for x in me.attributes['piece'].data]
 triangles={s:np.array([tuple(t.vertices) for t in me.loop_triangles if all(piece[i]==p for i in t.vertices)]) for s,p in [('L',1),('R',2)]}
 leftrest=rig.matrix_world@rig.data.bones['B_L_Hand'].matrix_local
 axes={'R':(Vector(eq['axe_centre']),Vector(eq['axe_axis']),.0115,'Axe'),'L':(leftrest@Vector(left['handle_centre_hand_local']),(leftrest.to_3x3()@Vector(left['handle_axis_hand_local'])).normalized(),.011,'Shield')};rows={}
 for role in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];row={'L':1e9,'R':1e9,'frames':0}
  for f in np.arange(0,min(float(a.frame_range[1]),26 if role=='Death' else 1e6)+.001,.625):
   bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([tuple(ob.matrix_world@v.co) for v in em.vertices]);ev.to_mesh_clear()
   for side,(center,axis,radius,bone) in axes.items():
    deform=(rig.matrix_world@rig.pose.bones[bone].matrix)@rig.data.bones[bone].matrix_local.inverted()@rig.matrix_world.inverted();c=np.array(deform@center);ax=np.array((deform.to_3x3()@axis).normalized());pts=np.einsum('bk,nkj->nbj',bary,co[triangles[side]]).reshape(-1,3);v=pts-c;t=v@ax;v=v[np.abs(t)<.06];t=t[np.abs(t)<.06];distance=np.linalg.norm(v-t[:,None]*ax,axis=1);row[side]=min(row[side],float(distance.min()-radius)*1000)
   row['frames']+=1
  rows[role]=row
 result[label]=rows
result['method']='15 barycentric samples per hand triangle, ±60 mm along shaft, 48 Hz held intervals; signed clearance from 11.5/11 mm shaft envelopes. Diagnostic, not per-digit actual-prop surface certification.'
result['maximum_clearance_loss_mm']=max(result['accepted'][role][s]-result['selected'][role][s] for role in result['accepted'] for s in ['L','R']);(R/'gates/grip_envelopes.json').write_text(json.dumps(result,indent=2)+'\n');print('GRIP_ENVELOPES',result,flush=True)
