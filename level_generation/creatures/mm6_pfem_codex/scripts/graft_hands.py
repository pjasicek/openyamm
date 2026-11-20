"""Replace the six-digit body-generation hands with the separately generated five-digit hand component."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_before_hand_component.blend'))
body=bpy.data.objects['Body'];J=json.load(open(p/'work/joints_final.json'))['joints']
# Stable pre-graft checkpoint retained for replay.
# Measure the new body's real cuff sections before deleting the rejected hands.
bm=bmesh.new();bm.from_mesh(body.data);layer=bm.verts.layers.int['piece']
rings={}
for side,part in [('R',3),('L',4)]:
 pts=[v.co.copy() for v in bm.verts if v[layer]==part and v.is_boundary]
 assert len(pts)>=8,(side,len(pts))
 rings[side]=np.array(pts)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer] in (3,4)],context='VERTS')
bm.to_mesh(body.data);bm.free()
with bpy.data.libraries.load(str(p/'work/hand_source.blend'),link=False) as (source,dest):
 dest.objects=list(source.objects)
template=next(o for o in dest.objects if o and o.type=='MESH')
if template is None:raise RuntimeError('Missing hand mesh')
for side,part in [('R',3),('L',4)]:
 me=template.data.copy();bm=bmesh.new();bm.from_mesh(me)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,-.38),plane_no=(0,0,1),clear_inner=True)
 boundary=[v for v in bm.verts if v.is_boundary]
 wr=np.array([tuple(v.co) for v in boundary]).mean(0)
 maxz=max(v.co.z for v in bm.verts)
 scale=.174/(maxz-wr[2])
 # New hand follows the forearm in rest; the fitted hand frame handles the source clip's palm roll.
 W=rings[side].mean(0);E=np.array(J[f'{side}_Forearm'])
 f=(W-E);f/=np.linalg.norm(f)
 thumb=np.array([0.,-1.,0.]);thumb-=f*(thumb@f);thumb/=np.linalg.norm(thumb)
 xaxis=-thumb if side=='R' else thumb
 yaxis=np.cross(f,xaxis);R=np.column_stack([xaxis,yaxis,f])
 # Match the cuff ellipse, then fade into the generated palm over 2.8 cm.
 cuff=(rings[side]-W)@R
 rx,ry=np.max(abs(cuff[:,0])),np.max(abs(cuff[:,1]))
 bco=np.array([tuple(v.co) for v in boundary])-wr
 sx,sy=max(abs(bco[:,0]))*scale,max(abs(bco[:,1]))*scale
 attr=bm.verts.layers.int.get('piece') or bm.verts.layers.int.new('piece')
 for v in bm.verts:
  local=(np.array(v.co)-wr)*scale
  if side=='L':local[0]*=-1
  w=max(0,min(1,local[2]/.028));w=w*w*(3-2*w)
  local[0]*=(rx/sx)*(1-w)+w
  local[1]*=(ry/sy)*(1-w)+w
  v.co=Vector(W+R@local-f*.0025);v[attr]=part
 for face in bm.faces:face.smooth=True
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new('Hand_'+side,me);bpy.context.collection.objects.link(ob)
 print('HAND FIT',side,'wrist',W.tolist(),'source wrist',wr.tolist(),'scale',scale,'cuff radii',rx,ry)
bpy.data.objects.remove(template,do_unlink=True)
for o in bpy.data.objects:o.select_set(o==body or o.name in ('Hand_R','Hand_L'))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
me=body.data;orig=me.attributes.get('orig_co') or me.attributes.new('orig_co','FLOAT_VECTOR','POINT')
orig.data.foreach_set('vector',np.array([tuple(v.co) for v in me.vertices]).ravel())
# A shared clay material makes component boundaries visible through shading, without palette confusion.
me.materials.clear();mat=bpy.data.materials.new('Clay');mat.diffuse_color=(.7,.66,.61,1);me.materials.append(mat)
for face in me.polygons:face.material_index=0;face.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/new_hands_body'),.83,1.8,views=('front','back'),resolution=(600,900))
for side,part,x in [('R',3,-.465),('L',4,.462)]:
 body.hide_render=True;tmp=body.copy();tmp.data=body.data.copy();bpy.context.collection.objects.link(tmp);tmp.hide_render=False
 bm=bmesh.new();bm.from_mesh(tmp.data);la=bm.verts.layers.int['piece']
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]!=part],context='VERTS');bm.to_mesh(tmp.data);bm.free()
 common.render_views(str(p/f'review/hand_component_{side}'),.893,.23,views=('left','right','front'),resolution=(600,600),target=(x,-.056))
 bpy.data.objects.remove(tmp,do_unlink=True);body.hide_render=False
