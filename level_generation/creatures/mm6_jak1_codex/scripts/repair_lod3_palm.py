"""Spend remaining LOD3 triangles on the curved staff palm, fitted to the accepted LOD0 surface."""
import bpy,bmesh,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];W=P/'work/round2/reduction'
def setup(file):
 bpy.ops.wm.open_mainfile(filepath=str(file));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);return body,rig
def posed(body):
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:]for v in m.vertices]);ev.to_mesh_clear();return co
body,rig=setup(P/'work/runtime_master.blend');names={g.index:g.name for g in body.vertex_groups};source=posed(body);source_weights=[{names[g.group]:g.weight for g in v.groups}for v in body.data.vertices];hand=np.array([sum(w for n,w in d.items()if n.startswith('B_R_Hand')or n.startswith('B_R_Finger'))>.3 for d in source_weights]);body.data.calc_loop_triangles();faces=np.array([tuple(f.vertices)for f in body.data.loop_triangles if all(hand[i]for i in f.vertices)]);tree=BVHTree.FromPolygons(source.tolist(),faces.tolist())
body,rig=setup(W/'lod3_reduced01.blend');me=body.data;names={g.index:g.name for g in body.vertex_groups};handgroups={i for i,n in names.items()if n.startswith('B_R_Hand')or n.startswith('B_R_Finger')};bm=bmesh.new();bm.from_mesh(me);deform=bm.verts.layers.deform.active;selected=[f for f in bm.faces if all(sum(v[deform].get(i,0)for i in handgroups)>.3 for v in f.verts)];selected=sorted(selected,key=lambda f:-f.calc_area())[:30];print('PALM FACES',len(selected),flush=True);assert 1<=len(selected)<=30
bmesh.ops.poke(bm,faces=selected,offset=0);bm.to_mesh(me);bm.free();me.calc_loop_triangles();co=posed(body);changes=[]
for v in me.vertices:
 if sum(g.weight for g in v.groups if g.group in handgroups)<=.3:continue
 hit,normal,fi,d=tree.find_nearest(Vector(co[v.index]));assert d<.055,(v.index,d);tri=faces[fi];a,b,c=source[tri];q=np.array(hit);uv=np.linalg.lstsq(np.c_[b-a,c-a],q-a,rcond=None)[0];bary=np.maximum([1-uv.sum(),*uv],0);bary/=bary.sum();weights={}
 for j,factor in zip(tri,bary):
  for name,w in source_weights[j].items():weights[name]=weights.get(name,0)+w*factor
 for group in body.vertex_groups:group.remove([v.index])
 weights={n:w for n,w in sorted(weights.items(),key=lambda r:-r[1])[:8]if w>1e-6};total=sum(weights.values());weights={n:w/total for n,w in weights.items()}
 matrix=np.zeros((4,4))
 for name,w in weights.items():body.vertex_groups[name].add([v.index],float(w),'REPLACE');matrix+=np.array(rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted())*w
 v.co=np.linalg.solve(matrix,np.r_[q,1])[:3];changes.append({'vertex':v.index,'distance_m':float(d)})
me.update();rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
me.calc_loop_triangles();staffgroup=body.vertex_groups['Staff'].index;staff={v.index for v in me.vertices if any(g.group==staffgroup and g.weight>.5 for g in v.groups)};counts=[sum(not all(i in staff for i in f.vertices)for f in me.loop_triangles),sum(all(i in staff for i in f.vertices)for f in me.loop_triangles)];assert counts[0]<=600,counts
me.normals_split_custom_set([(0,0,0)]*len(me.loops));bpy.ops.wm.save_as_mainfile(filepath=str(W/'lod3_reduced01.blend'));(P/'review/round2/reduction/palm_refit.json').write_text(json.dumps({'triangles':counts,'added_palm_faces':len(selected)*2,'projection':'LOD0 posed Standing right hand, surface barycentric weights','vertices':changes},indent=2));print('PALM REFIT',counts,flush=True)
