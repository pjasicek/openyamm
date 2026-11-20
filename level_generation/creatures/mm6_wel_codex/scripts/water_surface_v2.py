"""Retain UVs and the selected rig; cut only the submerged tail below the native waterline."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/revisions/water_v1/work/textured_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/anim_foam.blend'),link=False) as (src,dst):dst.actions=src.actions
shift=rig.data.bones['Root'].matrix_local.to_3x3().transposed()@Vector((0,0,-.255))
for a in bpy.data.actions:
 a.use_fake_user=True
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if fc.data_path=='pose.bones["Root"].location':
      for key in fc.keyframe_points:
       key.co.y+=shift[fc.array_index];key.handle_left.y+=shift[fc.array_index];key.handle_right.y+=shift[fc.array_index]
 rig.animation_data.action=a
 lo,hi=a.frame_range
 for f in range(int(lo),int(hi)+1):
  u=(f-lo)/(hi-lo);k=np.clip((u-.55)/.45,0,1);k=k*k*(3-2*k)
  rig.pose.bones['FoamRoot'].location=(0,0,-4.4*(1 if a.name=='Dead' else k if a.name=='Death' else 0))
  rig.pose.bones['FoamRoot'].keyframe_insert('location',frame=f,group='FoamRoot')
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.context.view_layer.update()
skin={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted() for g in body.vertex_groups if g.name in rig.data.bones}
foam=body.vertex_groups.get('FoamRoot') or body.vertex_groups.new(name='FoamRoot');skin[foam.index]=Matrix.Identity(4)
def matrix(weights):
 m=Matrix(np.zeros((4,4)).tolist())
 for index,w in weights.items():
  if index in skin:m+=skin[index]*w
 return m
bm=bmesh.new();bm.from_mesh(body.data);deform=bm.verts.layers.deform.active;part=bm.verts.layers.int.get('part')
for v in bm.verts:v.co=matrix(v[deform])@v.co
before=len(bm.faces)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,.008),plane_no=(0,0,1),clear_inner=True)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
anchored=0
for v in bm.verts:
 if v[part]==5 and v.co.z<.18:
  weights=dict(v[deform]);w=max(0,1-(v.co.z-.008)/.172);w=w**.5
  keep=sorted(weights.items(),key=lambda x:x[1],reverse=True)[:3];total=sum(x[1] for x in keep)
  v[deform].clear()
  for i,k in keep:v[deform][i]=k/total*(1-w)
  v[deform][foam.index]=w;anchored+=1
 v.co=matrix(v[deform]).inverted_safe()@v.co
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
# Overlapping shallow foam collars surround the upright trunk and the remaining tail crest.
ob=bpy.data.objects['Foam'];bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap');d=bm.verts.layers.deform.new();segments=40
for cx,cy,rx,ry in [(-.01,-.12,.30,.34),(-.01,.38,.28,.49),(-.01,.78,.22,.32)]:
 grid=[]
 for ring in range(3):
  radius=.40+.30*ring;grid.append([])
  for k in range(segments):
   theta=2*math.pi*k/segments;v=bm.verts.new((cx+rx*radius*math.cos(theta),cy+ry*radius*math.sin(theta),.008+.022*(1-radius)))
   v[d][0]=1;grid[-1].append(v)
 for ring in range(2):
  for k in range(segments):
   f=bm.faces.new((grid[ring][k],grid[ring+1][k],grid[ring+1][(k+1)%segments],grid[ring][(k+1)%segments]))
   for loop in f.loops:loop[uv].uv=(.5+(loop.vert.co.x-cx)/rx*.49,.5+(loop.vert.co.y-cy)/ry*.49)
bm.to_mesh(ob.data);bm.free();ob.data.update()
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/surface_v2.blend'))
(P/'review/feedback_v2/waterline.json').write_text(json.dumps({'submerged_height_m':.255,'before_faces':before,'after_faces':len(body.data.polygons),'waterline_anchored_vertices':anchored,'geometry_cut_plane_m':.008},indent=2))
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
common.workbench_clay(sc)
for role,frames in [('Standing',[0]),('Walking',[0,17,33,50]),('Attack',[33,49,60,61])]:
 rig.animation_data.action=bpy.data.actions[role]
 for f in frames:
  sc.frame_set(f+1);common.render_views(str(P/'review/feedback_v2'/f'surface_{role}_{f:02}'),1.,2.7,views=('front','left'),resolution=(650,700),target=(0,.20))
