"""Fit the generated equipment to the measured grips; separate moving bolt/string."""
from pathlib import Path
import bpy,bmesh,sys,json,math,numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/crossbow_raw.blend'))
parts={int(o.name.rsplit('_',1)[1]):o for o in bpy.data.objects if o.type=='MESH'};assert len(parts)==24
# The generated lower duplicate projectile and the undrawn string are replaced by the moving mechanism.
for k in [8,15,17]:bpy.data.objects.remove(parts.pop(k),do_unlink=True)
for o in parts.values():
 for v in o.data.vertices:v.co=Vector((v.co.x*.82,v.co.y*.90+.09,v.co.z*.90+.02))
# A short carved grip below the trigger joins the stock and matches the measured finger axis.
stock=parts[0];face=min(stock.data.polygons,key=lambda f:(f.center-Vector((.015,0,.025))).length);uv=stock.data.uv_layers.active.data;uvc=sum((uv[l].uv for l in face.loop_indices),Vector((0,0)))/len(face.loop_indices)
A=Vector((0,-.35,.937)).normalized();u=Vector((1,0,0));v=A.cross(u);bm=bmesh.new();tex=bm.loops.layers.uv.new('UVMap');rings=[]
for z,radius in [(-.043,.012),(-.036,.015),(.035,.015),(.066,.018)]:
 rings.append([bm.verts.new(A*z+radius*(u*math.cos(i*math.tau/12)+v*math.sin(i*math.tau/12))) for i in range(12)])
for a,b in zip(rings[:-1],rings[1:]):
 for i in range(12):bm.faces.new([a[i],a[(i+1)%12],b[(i+1)%12],b[i]])
bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for f in bm.faces:
 for l in f.loops:l[tex].uv=uvc+Vector((l.vert.co.x,l.vert.co.z))*.04
me=bpy.data.meshes.new('CarvedGrip');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('CarvedGrip',me);bpy.context.collection.objects.link(o);me.materials.append(stock.data.materials[0]);parts[24]=o
# Trigger clears the new wooden neck and sits under the index side of the stock.
for v in parts[3].data.vertices:v.co.y+=.035

def join(obs,name):
 for o in bpy.data.objects:o.select_set(o in obs)
 bpy.context.view_layer.objects.active=obs[0]
 if len(obs)>1:bpy.ops.object.join()
 o=bpy.context.view_layer.objects.active;o.name=o.data.name=name;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 return o
bolt=join([parts[k] for k in [13,14,16]],'BoltMesh');crossbow=join([o for k,o in parts.items() if k not in [13,14,16]],'CrossbowMesh')
# Quiver remains a rigid belt attachment, including the generated pale fletchings and loop.
with bpy.data.libraries.load(str(P/'work/quiver_raw.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('quiver_')]
for o in dst.objects:
 bpy.context.collection.objects.link(o)
 for v in o.data.vertices:
  v.co=Matrix.Rotation(math.radians(-13),3,'X')@(v.co*.80)
  if o.name=='quiver_01':v.co.z=.03+(v.co.z-.03)*2.8;v.co.x*=.45;v.co.y-=.025
q=join(dst.objects,'QuiverMesh')
# Both moving string halves instance this one tiny static tube.
bm=bmesh.new();ret=bmesh.ops.create_cone(bm,cap_ends=True,segments=8,radius1=.003,radius2=.003,depth=1)
for v in bm.verts:v.co=Vector((v.co.x,v.co.z+.5,v.co.y))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));me=bpy.data.meshes.new('StringMesh');bm.to_mesh(me);bm.free();string=bpy.data.objects.new('StringMesh',me);bpy.context.collection.objects.link(string)
mat=bpy.data.materials.new('BowString');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.30,.22,.12,1);bs.inputs['Roughness'].default_value=.92;me.materials.append(mat)
for name,obs in [('crossbow',[crossbow,bolt]),('quiver',[q])]:
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=o not in obs
 common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/f'review/{name}_fitted'),0,.85 if name=='crossbow' else .6,views=('three_quarter','left','front'),resolution=(600,600))
for o in [crossbow,bolt,q,string]:o.hide_render=False
mechanism={'string_tips':[[-.242,.225,.079],[.242,.225,.079]],'nock_drawn':[0,.09,.085],'nock_released':[0,.225,.085],'bolt_release_s':1.0,'bolt_rearm_s':1.56,'crossbow_hand_matrix':json.loads((P/'work/prop_grips.json').read_text())['R'],'quiver_rest_position':[-.36,.04,.958],'quiver_rest_rotation_y_degrees':25,'quiver_rest_rotation_z_degrees':-90,'quiver_belt_anchor':[0,.07,.30],'parts':{o.name:sum(len(f.vertices)-2 for f in o.data.polygons) for o in [crossbow,bolt,q,string]}}
assert mechanism['parts']['CrossbowMesh']<3000 and mechanism['parts']['QuiverMesh']<1200
(P/'work/props.json').write_text(json.dumps(mechanism,indent=2));print('PROPS',mechanism['parts']);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/props.blend'))
