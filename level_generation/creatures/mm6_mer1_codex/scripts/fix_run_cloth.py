import bpy,bmesh,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;scene=bpy.context.scene
pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices]);gn={g.index:g.name for g in o.vertex_groups};faces=[tuple(f.vertices)for f in me.polygons]
def curves(a):return [fc for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
def signs():
 flips=0
 for a in bpy.data.actions:
  groups={}
  for fc in curves(a):
   for k in fc.keyframe_points:k.interpolation='LINEAR'
   if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
  for cs in groups.values():
   if len(cs)!=4:continue
   prev=None
   for j in range(min(len(cs[i].keyframe_points)for i in range(4))):
    q=np.array([cs[i].keyframe_points[j].co.y for i in range(4)])
    if prev is not None and q@prev<0:
     q=-q;flips+=1
     for i in range(4):cs[i].keyframe_points[j].co.y=q[i]
    prev=q
  for fc in curves(a):fc.update()
 print('SIGN corrections',flips,flush=True)
signs()
def action(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def coeval():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();return c
# Push the closed skirt outward at the specific boot crossings, bending adjacent waist chains together.
clothfaces=[fc for fc in faces if pv[fc[0]]==2];bootids=np.where(np.isin(pv,[6,7])&np.array([v.co.z>.32 for v in me.vertices]))[0]
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();part=bm.verts.layers.int['piece'];hem=sorted({v.index for e in bm.edges if e.is_boundary and all(v[part]==2 and v.co.z<.36 for v in e.verts)for v in e.verts});nbr={i:[q.index for e in bm.verts[i].link_edges if (q:=e.other_vert(bm.verts[i])).co.z>bm.verts[i].co.z+.01]for i in hem};hem=[i for i in hem if nbr[i]];bm.free()
clothcor=0;action(bpy.data.actions['Running']);a=bpy.data.actions['Running']
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 scene.frame_set(int(f),subframe=float(f%1))
 for it in range(12):
  co=coeval();tree=BVHTree.FromPolygons(co,clothfaces);worst=None
  for i in bootids:
   loc,n,fi,d=tree.find_nearest(co[i],.15)
   if loc is None or (co[i]-loc).dot(n)<.7*d or d<.0005:continue
   hi=min(hem,key=lambda j:(co[j]-co[i]).length_squared);down=(co[hi]-sum((co[j]for j in nbr[hi]),Vector())/len(nbr[hi])).normalized()
   if (co[i]-co[hi]).dot(down)>=-.002:continue
   if worst is None or d>worst[0]:worst=(d,n,loc,fi)
  if worst is None:break
  d,n,loc,fi=worst;weights={}
  for vi in clothfaces[fi]:
   for e in me.vertices[vi].groups:
    name=gn[e.group]
    if name.startswith('Cloak_'):
     c=int(name.split('_')[1]);weights[c]=weights.get(c,0)+e.weight
  if not weights:break
  c=max(weights,key=weights.get)
  for chain,share in [(c,1),((c-1)%16,.5),((c+1)%16,.5)]:
   name=f'Cloak_{chain}_0';M=r.pose.bones[name].matrix.copy();h=M.translation.copy();u=loc-h;v=loc+n*(d+.003)*share-h
   if u.length<.025:continue
   q=u.normalized().rotation_difference(v.normalized());M=q.to_matrix().to_4x4()@M;M.translation=h;r.pose.bones[name].matrix=M;bpy.context.view_layer.update()
  clothcor=max(clothcor,d)
 for pb in r.pose.bones:
  if pb.name.startswith('Cloak_'):pb.keyframe_insert('rotation_quaternion',frame=float(f))

print('Run cloth maximum correction',clothcor,flush=True);signs();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction_master.blend'))
import runpy
sys.argv=['audit_motion.py','--','work/reduction_master.blend','master_final'];runpy.run_path(str(P/'scripts/audit_motion.py'),run_name='__main__')
