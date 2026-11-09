"""Fit native blade roll with actual posed mesh contacts, retaining the source grip axis."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/clay.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co) for v in me.vertices]);sw=np.where(pv==100)[0];polys=[tuple(p.vertices) for p in me.polygons if pv[p.vertices[0]] not in [100,4]]
w=json.loads((P/'work/weapon_fit.json').read_text());c=Vector(w['centre_rest']);ax=Vector(w['axis_rest']);edge=Vector(w['cut_direction_rest']);inv=rig.data.bones['Sword'].matrix_local.inverted()
ac=bpy.data.actions['Attack'];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];cache=[]
for f in np.arange(0,float(ac.frame_range[1])+.001,30/48):
 scene.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[body.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,polys);M=rig.pose.bones['Sword'].matrix@inv;cache.append((float(f),tree,M.copy()))
rays=[Vector(q).normalized() for q in [(1,.13,.27),(-1,.31,.17),(.19,1,.41),(.23,-1,.37),(.31,.21,1),(.11,.27,-1),(1,1,1)]]
results=[]
for deg in [46,48,50,52,54,56]:
 Q=Quaternion(ax,math.radians(deg));points=[c+Q@(Vector(rest[i])-c) for i in sw];e=Q@edge;tip=c+Q@(ax*.85-edge*.18);worst=0;frame=None;prev=None;lead=[];speeds=[]
 for f,tree,M in cache:
  pt=M@tip
  if prev is not None:
   v=pt-prev
   if (M.to_3x3()@ax).dot(Vector((0,-1,0)))>.5:
    speeds.append((v.length*48,(f-30/96)/30,v.normalized().dot(M.to_3x3()@e)))
  prev=pt
  for p in points:
   pp=M@p;loc,n,fi,d=tree.find_nearest(pp,.10)
   if loc is None or d<=worst or (pp-loc).dot(n)>-.7*d:continue
   exits=0
   for ray in rays:
    hit,normal,_,_=tree.ray_cast(pp+ray*1e-6,ray,10);exits+=hit is not None and normal.dot(ray)>0
   if exits>=5:worst=d;frame=f
 peak=max(speeds);res={'roll_delta_deg':deg,'contact_m':worst,'frame':frame,'blow_s':peak[1],'speed_m_s':peak[0],'signed_edge_lead':peak[2]};results.append(res);print('ROLL',res,flush=True)
valid=[r for r in results if r['contact_m']<.002 and r['signed_edge_lead']>.5]
assert valid,'No blade roll clears armour while cutting with edge'
best=min(valid,key=lambda r:abs(r['roll_delta_deg']));(P/'work/weapon_roll.json').write_text(json.dumps({'selected':best,'candidates':results},indent=2));print('SELECTED',best)
