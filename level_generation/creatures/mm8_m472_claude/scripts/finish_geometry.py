"""Retain the concealed trousers as a fitting proxy; export the visible shoes and opaque floor-length robe."""
from pathlib import Path
import bpy,bmesh,json
import numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_polished.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
# Preserve the complete trouser mesh as an editable fitting reference, excluded from renders and exports.
proxy=body.copy();proxy.data=body.data.copy();bpy.context.collection.objects.link(proxy);proxy.name='LegFittingProxy'
bm=bmesh.new();bm.from_mesh(proxy.data);bm.verts.ensure_lookup_table();piece=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[piece]!=12],context='VERTS');bm.to_mesh(proxy.data);bm.free();proxy.hide_render=True;proxy.hide_set(True)
bm=bmesh.new();bm.from_mesh(body.data);piece=bm.verts.layers.int['piece'];parts=[v for v in bm.verts if v[piece]==12];partset=set(parts);edges=[e for e in bm.edges if all(v in partset for v in e.verts)];faces=[f for f in bm.faces if all(v in partset for v in f.verts)]
bmesh.ops.bisect_plane(bm,geom=parts+edges+faces,plane_co=(0,0,.17),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
rim=[e for e in bm.edges if e.is_boundary and all(v[piece]==12 and abs(v.co.z-.17)<.0001 for v in e.verts)]
filled=bmesh.ops.holes_fill(bm,edges=rim,sides=0)['faces'];bmesh.ops.triangulate(bm,faces=filled);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
# The inherited fitting shoes are broad boots; fit the visible slippers to this slim caster.
for v in body.data.vertices:
 if body.data.attributes['piece'].data[v.index].value==12:
  foot=rig.data.bones['B_L_Foot' if v.co.x>0 else 'B_R_Foot'].head_local
  v.co.x=foot.x+(v.co.x-foot.x)*.70
  v.co.y=foot.y+(v.co.y-foot.y)*.80
  v.co.z*=.80
# Add seam allowance only at the moving hem, keeping the waist and upper robe silhouette fitted.
for v in body.data.vertices:
 if body.data.attributes['cloth_region'].data[v.index].value==1 and v.co.z<.30:
  q=Vector((v.co.x,v.co.y+.025,0));q.normalize();v.co+=q*(.035*max(0,1-v.co.z/.30))
# Running opens the lower hem around the advancing shoes; cloth controls may translate without stretching anatomy.
chains=[c for c in json.loads(sc['garment_chains']) if c['kind']=='robe']
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
 for n in c['bones']:rig.data.edit_bones[n].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
a=bpy.data.actions['Running'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
rows=[]
for frame in range(int(a.frame_range[1])+1):
 for c in chains:
  for n in c['bones']:rig.pose.bones[n].location=(0,0,0)
 sc.frame_set(frame);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
 matrices={n:rig.pose.bones[n].matrix.copy() for c in chains for n in c['bones']}
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis=snap[b.name]
 bpy.context.view_layer.update()
 for c in chains:
  direction=Vector((np.sin(c['angle']),np.cos(c['angle']),0))
  for k,n in enumerate(c['bones']):
   M=matrices[n].copy();M.translation+=direction*(.10*(k/3)**2)
   rig.pose.bones[n].matrix=M;bpy.context.view_layer.update()
 rows.append({n:rig.pose.bones[n].location.copy() for n in matrices})
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
for frame,row in enumerate(rows):
 for n,loc in row.items():rig.pose.bones[n].location=loc;rig.pose.bones[n].keyframe_insert('location',frame=frame)
for other in [a for a in bpy.data.actions if a.name in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']]:
 rig.animation_data.action=other
 if other.slots:rig.animation_data.action_slot=other.slots[0]
 for frame in [0,int(other.frame_range[1])]:
  for c in chains:
   for n in c['bones']:rig.pose.bones[n].location=(0,0,0);rig.pose.bones[n].keyframe_insert('location',frame=frame)
# Ground the actual visible surface; the long hair defines contact during the back fall.
report={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 if act.name not in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']:continue
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 lows=[];matrices=[]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);matrices.append(rig.pose.bones['B_Pelvis'].matrix.copy())
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();lows.append(min(v.co.z for v in m.vertices));ev.to_mesh_clear()
 lifts=np.maximum(.003-np.array(lows),0)
 # Spread contact correction over adjacent samples without lowering a colliding frame.
 lifts=np.maximum.reduce([np.roll(lifts,k)*(.5**abs(k)) for k in range(-2,3)])
 assert lifts.max()<.08,(act.name,float(lifts.max()))
 for f,(M,lift) in enumerate(zip(matrices,lifts)):
  sc.frame_set(f);M.translation.z+=float(lift);pb=rig.pose.bones['B_Pelvis'];pb.matrix=M;pb.keyframe_insert('location',frame=f)
 report[act.name]={'visible_floor_lift_m':float(lifts.max())}
 print('VISIBLE_SURFACE',act.name,report[act.name],flush=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
(p/'work/visible_geometry.json').write_text(json.dumps({'hidden_proxy':'LegFittingProxy','shoe_cut_height_m':.17,'floor':report},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_gated.blend'))
