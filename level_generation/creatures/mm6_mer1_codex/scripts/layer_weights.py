import bpy,bmesh,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_corrected.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=o.data;pv=np.array([a.value for a in me.attributes['piece'].data]);gn={g.index:g.name for g in o.vertex_groups}
with bpy.data.libraries.load(str(P/'work/skirt_v1.blend'),link=False)as(src,dst):dst.objects=['Body']
source=dst.objects[0];names={g.index:g.name for g in source.vertex_groups}
def put(i,w):
 for e in me.vertices[i].groups[:]:o.vertex_groups[e.group].remove([i])
 total=sum(w.values());assert total>0
 for n,x in w.items():
  if x>1e-8:o.vertex_groups[n].add([i],float(x/total),'REPLACE')
for v in me.vertices:
 if pv[v.index]in[8,9]:put(v.index,{names[e.group]:e.weight for e in source.data.vertices[v.index].groups})
bpy.data.objects.remove(source,do_unlink=True)
# The original mantle already closes the shoulder. Remove the unnecessary bridge that strained at the arm root.
pairs=json.loads((P/'review/rig_surface_corrections.json').read_text())['seam_pairs'];remove={b for a,b in pairs};bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index in remove],context='VERTS');bm.to_mesh(me);bm.free();pv=np.array([a.value for a in me.attributes['piece'].data])
# Outer cloth needs 12 mm thickness/clearance from the moving boot cuffs; the belt rim remains anchored.
for v in me.vertices:
 if pv[v.index]==2:
  q=Vector((v.co.x,v.co.y-.015,0));w=min(1,max(0,(.87-v.co.z)/.10));v.co+=q.normalized()*(.012*w)
 if pv[v.index]in[10,16]:v.co.y-=.04
 if pv[v.index]==13:v.co.y-=.04*min(1,max(0,(.91-v.co.z)/.05))
# Completely covered trouser surfaces share the overlying coat's deformation, as the boot-top underlayer.
# This avoids two independently deformed layers crossing inside a single closed garment.
faces=[tuple(f.vertices)for f in me.polygons if pv[f.vertices[0]]==2];tree=BVHTree.FromPolygons([tuple(v.co)for v in me.vertices],faces)
for v in me.vertices:
 if pv[v.index]!=5:continue
 loc,n,fi,d=tree.find_nearest(v.co);vs=[me.vertices[i]for i in faces[fi]];weights=barycentric_transform(loc,*[x.co for x in vs[:3]],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));w={}
 for vertex,share in zip(vs,weights):
  for e in vertex.groups:w[gn[e.group]]=w.get(gn[e.group],0)+max(0,share)*e.weight
 put(v.index,w)
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_layers.blend'))
