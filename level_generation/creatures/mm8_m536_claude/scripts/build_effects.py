"""Assemble the opaque Efreeti, separate scrolling flame LODs and measured native flask remains."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;T=P/'textures';profile=json.loads((T/'effect_profile.json').read_text())
for m in list(bpy.data.materials):m.name='Source_'+m.name
for slot,label,name in [(0,'body','Efreeti_A'),(1,'head','EfreetiHead_A')]:
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=1
 def tex(suffix,cs):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/f'm536_{label}_{suffix}.png'),check_existing=True);node.image.colorspace_settings.name=cs;return node
 nt.links.new(tex('basecolor_1k','sRGB').outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough_1k','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);body.data.materials[slot]=mat

# The generated lower cone sits inside the fire; trim it at the native waist transition.
bm=bmesh.new();bm.from_mesh(body.data);uv=bm.loops.layers.uv.active
region=[f for f in bm.faces if all(abs(v.co.x)<.29 and v.co.z<2.13 for v in f.verts)]
geom=set(region)|{e for f in region for e in f.edges}|{v for f in region for v in f.verts}
cut=bmesh.ops.bisect_plane(bm,geom=list(geom),plane_co=(0,0,1.93),plane_no=(0,0,1),dist=1e-7)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if abs(v.co.x)<.29 and v.co.z<1.93-1e-6],context='VERTS')
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
for f in bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces']:
 for l in f.loops:
  neighbours=[x[uv].uv.copy() for x in l.vert.link_loops if x.face!=f]
  l[uv].uv=sum(neighbours,Vector((0,0)))/len(neighbours) if neighbours else (.5,.5)
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('Flask');bone.head=(0,0,.008);bone.tail=(0,0,.10);bone.parent=rig.data.edit_bones['Root'];bpy.ops.object.mode_set(mode='OBJECT')
def material(name,texture,flame=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True;n=m.node_tree.nodes;links=m.node_tree.links;bs=n.get('Principled BSDF');im=n.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(T/texture));links.new(im.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Metallic'].default_value=0 if flame else .32;bs.inputs['Roughness'].default_value=1 if flame else .44
 if flame:
  color=n.new('ShaderNodeVertexColor');color.layer_name='Color';mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';links.new(im.outputs['Alpha'],mul.inputs[0]);links.new(color.outputs['Alpha'],mul.inputs[1]);links.new(mul.outputs[0],bs.inputs['Alpha']);links.new(im.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1;m.surface_render_method='BLENDED'
 return m
flame=material('EfreetiFlame','m536_flame.png',True);fringe=material('EfreetiFringe','m536_fringe.png',True);flaskmat=material('EfreetiFlask','m536_flask.png')
heights=np.array([rig.data.bones[f'Vortex_{i:02}'].head_local.z for i in range(8)])
def weights(z):
 u=float(np.interp(z,heights[::-1],np.arange(8)[::-1]));k=min(int(u),6);return [(f'Vortex_{k:02}',1-u+k),(f'Vortex_{k+1:02}',u-k)]
def mesh(name,verts,faces,uvs,slots,groups,mats):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();uv=me.uv_layers.new(name='UVMap')
 for mat in mats:me.materials.append(mat)
 for f,us,slot in zip(me.polygons,uvs,slots):
  f.material_index=slot;f.use_smooth=False
  for l,u in zip(f.loop_indices,us):uv.data[l].uv=u
 o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.parent=rig
 if name.startswith('FlameTail'):
  colors=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for v,c in zip(me.vertices,colors.data):
   a=min(1,max(0,(2.0-v.co.z)/.08),max(0,(v.co.z-.07)/.10));c.color=(1,1,1,a)
 mod=o.modifiers.new('Skin','ARMATURE');mod.object=rig
 for i,gs in enumerate(groups):
  for name,w in gs:
   if w>1e-6:
    g=o.vertex_groups.get(name) or o.vertex_groups.new(name=name);g.add([i],float(w),'REPLACE')
 return o
pt=profile['tail'];zsrc=np.array(pt['height']);rsrc=np.array(pt['radius']);tailobjects=[]
for lod,(segments,rings,fins) in enumerate([(24,20,10),(16,14,7),(10,9,5)]):
 verts=[];faces=[];uvs=[];slots=[];groups=[]
 zs=np.linspace(zsrc[0],zsrc[-1],rings);rs=np.interp(zs,zsrc[::-1],rsrc[::-1]);vs=(zsrc[0]-zs)/((zsrc[0]-zsrc[-1])*pt['tile_share']);offset=np.interp(zs,[.07,1.95],[.42,0])**1.2
 def face(ids,uv,slot,reverse=False):
  if reverse:ids,uv=ids[::-1],uv[::-1]
  for idx in [(0,1,2),(0,2,3)]:faces.append([ids[i] for i in idx]);uvs.append([uv[i] for i in idx]);slots.append(slot)
 # Inside first, then outside: fixed back-to-front order for any side view.
 for inward in [True,False]:
  base=len(verts)
  for z,r,y in zip(zs,rs,offset):
   for k in range(segments):
    a=2*math.pi*k/segments;verts.append((r*math.cos(a),y+r*math.sin(a),z));groups.append(weights(z))
  for j in range(rings-1):
   for k in range(segments):
    ids=[base+j*segments+k,base+(j+1)*segments+k,base+(j+1)*segments+(k+1)%segments,base+j*segments+(k+1)%segments];uv=[(k/segments,1-vs[j]),(k/segments,1-vs[j+1]),((k+1)/segments,1-vs[j+1]),((k+1)/segments,1-vs[j])];face(ids,uv,0,inward)
 for fin in range(fins):
  a=2*math.pi*(fin+.5)/fins;strip=fin%8;u0=strip/8+1.5/1024;u1=(strip+1)/8-1.5/1024
  for reverse in [False,True]:
   base=len(verts)
   for z,r,y in zip(zs,rs,offset):
    for f in [pt['fringe_inner'],pt['fringe_outer']]:verts.append((f*r*math.cos(a),y+f*r*math.sin(a),z));groups.append(weights(z))
   for j in range(rings-1):
    face([base+2*j,base+2*(j+1),base+2*(j+1)+1,base+2*j+1],[(u0,1-vs[j]-.37*fin),(u0,1-vs[j+1]-.37*fin),(u1,1-vs[j+1]-.37*fin),(u1,1-vs[j]-.37*fin)],1,reverse)
 tailobjects.append(mesh('FlameTail'+('' if lod==0 else f'_LOD{lod}'),verts,faces,uvs,slots,groups,[flame,fringe]))
 # Lower LODs remain exportable but hidden in the editable scene.
 if lod:tailobjects[-1].hide_render=True;tailobjects[-1].hide_set(True)
fp=profile['flask'];verts=[];faces=[];uvs=[];groups=[];segments=20
for j,(z,r) in enumerate(zip(fp['z'],fp['radius'])):
 for k in range(segments):
  a=2*math.pi*k/segments;fluting=1+.07*math.cos(a*8) if z>.69 else 1;verts.append((r*fluting*math.cos(a),r*fluting*math.sin(a),z));groups.append([('Flask',1.)])
for j in range(len(fp['z'])-1):
 for k in range(segments):
  ids=[j*segments+k,(j+1)*segments+k,(j+1)*segments+(k+1)%segments,j*segments+(k+1)%segments];uv=[(k/segments,1-j/(len(fp['z'])-1)),(k/segments,1-(j+1)/(len(fp['z'])-1)),((k+1)/segments,1-(j+1)/(len(fp['z'])-1)),((k+1)/segments,1-j/(len(fp['z'])-1))]
  for ix in [(0,1,2),(0,2,3)]:faces.append([ids[i] for i in ix]);uvs.append([uv[i] for i in ix])
for row in [0,len(fp['z'])-1]:
 c=len(verts);verts.append((0,0,fp['z'][row]));groups.append([('Flask',1.)])
 for k in range(segments):
  ix=[c,row*segments+k,row*segments+(k+1)%segments]
  if row:ix=ix[::-1]
  faces.append(ix);uvs.append([(.5,1-row/(len(fp['z'])-1))]*3)
flask=mesh('FlaskRemains',verts,faces,uvs,[0]*len(faces),groups,[flaskmat])
for f in flask.data.polygons:f.use_smooth=True
def ss(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
# The bottle grows as the body contracts. Root height follows scale so the long tail cannot sink through the floor.
for action in bpy.data.actions:
 rig.animation_data.action=action;lo,hi=action.frame_range;frames=sorted(set(list(np.arange(lo,hi,.5))+[float(hi)]));saved=[]
 for frame in frames:
  sc.frame_set(int(frame),subframe=frame%1);t=(frame-lo)/30;u=1 if action.name=='Dead' else ss((t-.28)/.35) if action.name=='Death' else 0
  pb=rig.pose.bones['BodyRoot'];loc=pb.location.copy()
  if action.name in ['Death','Dead']:
   scale=pb.scale.x;target=1.78*scale+.32*(1-scale)+.08*math.sin(math.pi*(1-scale));delta=target-pb.matrix.translation.z;loc+=rig.data.bones['BodyRoot'].matrix_local.to_3x3().transposed()@Vector((0,0,delta))
  saved.append((frame,max(.0001,u),loc))
 for frame,u,loc in saved:
  pb=rig.pose.bones['Flask'];pb.scale=(u,u,u);pb.keyframe_insert('scale',frame=frame,group='Flask')
  if action.name in ['Death','Dead']:
   pb=rig.pose.bones['BodyRoot'];pb.location=loc;pb.keyframe_insert('location',frame=frame,group='BodyRoot')
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
report={'bones':len(rig.data.bones),'body_triangles':len(body.data.polygons),'flame_lod_triangles':[len(o.data.polygons) for o in tailobjects],'flask_triangles':len(flask.data.polygons),'effect_source':'textures/effect_profile.json','blend_order':'one shell: inside before outside, then radial fringe; no specular, no creature edge darkening'}
(P/'work/assembly.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/assembled.blend'));print('ASSEMBLED',report)
