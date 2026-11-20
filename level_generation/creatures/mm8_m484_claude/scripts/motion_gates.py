import bpy,json,sys,math,bmesh
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_cloth.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene
ng=[g.name for g in b.vertex_groups];pv=np.array([v.value for v in b.data.attributes['piece'].data]);foot={sd:[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if ng[g.group] in [f'B_{sd}_Foot',f'B_{sd}_Toe0'])>.5] for sd in 'RL'}
def co(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return a
report={}
for nm in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];w={sd:[] for sd in 'RL'};rows=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=f%1);c=co(b);ap=co(ax);rows.append([float(f),float(c[foot['R'],2].min()),float(c[foot['L'],2].min()),float(c[:,2].min()),float(ap[:,2].min())])
  for sd in 'RL':w[sd].append(armik.wrist_cost(r,sd,armik.W(r,f'B_{sd}_Hand').to_3x3()))
 report[nm]={'wrist':{sd:{'swing_max':max(v[0] for v in vals),'twist_range':[min(v[1] for v in vals),max(v[1] for v in vals)]} for sd,vals in w.items()},'floor_rows':rows};print('MOTION',nm,report[nm]['wrist'],'floor',np.min(rows,0).tolist(),np.max(rows,0).tolist(),flush=True)
closed={}
for part in [0,1]:
 bm=bmesh.new();bm.from_mesh(b.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]!=part],context='VERTS');closed[str(part)]={'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges)};bm.free()
report['closed_skin']=closed;print('CLOSED',closed);(P/'review/motion_gates.json').write_text(json.dumps(report,indent=2))
