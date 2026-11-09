"""Joint-attached crossed flame plumes with static soft outlines and animated extinction."""
import bpy, bmesh, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
# Each disconnected flame patch has one leaf control, so extinction collapses the entire patch.
patches=[('Chest',(0,.075,.135),(0,-.115,.16),.070,.071,0.0),
         ('Head',(0,-.115,.172),(0,-.180,.172),.028,.035,.23),
         ('Tail',(0,.08,.10),(0,.19,.07),.052,.020,.46)]
for sd,sg in [('L',1),('R',-1)]:
 for k in range(3):
  n=sd+'Wing'+str(k);b=rig.data.bones[n];h=b.head_local.copy();t=b.tail_local.copy();v=t-h
  patches.append((n,list(h-v*.18),list(t+v*.18),.040 if k<2 else .053,.038,.15*k+(.31 if sg<0 else 0)))
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,*_ in patches:
 p=rig.data.edit_bones[n];b=rig.data.edit_bones.new('Fire_'+n);b.head=p.head.copy();b.tail=p.tail.copy();b.matrix=p.matrix.copy();b.parent=p
bpy.ops.object.mode_set(mode='OBJECT')
materials=[]
for name,file,opacity in [('Phoenix_Flame','phoenix_plume.png',.80)]:
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False
 nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures'/file));tex.extension='REPEAT'
 nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1.;bs.inputs['Roughness'].default_value=1.
 mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=opacity;nt.links.new(tex.outputs['Alpha'],mul.inputs[0]);nt.links.new(mul.outputs[0],bs.inputs['Alpha']);nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
 mat.surface_render_method='DITHERED';materials.append(mat)
verts=[];faces=[];uvs=[];slots=[];owners=[];alphas=[]
def vertex(p,n,alpha=1.):verts.append(list(p));owners.append('Fire_'+n);alphas.append(alpha);return len(verts)-1
def face(ids,uv,slot):faces.append(ids);uvs.append(uv);slots.append(slot)
def shell(n,a,b,ry,rz,phase):
 a=Vector(a);b=Vector(b)
 if n=='Chest':a=Vector((0,.025,.085));b=Vector((0,.035,.305));width=.175
 elif n=='Head':a=Vector((0,-.147,.155));b=Vector((0,-.140,.245));width=.072
 elif n=='Tail':width=.092
 else:
  a.z+=.025;b.z+=.025;width=.13 if n.endswith('2') else .14
 axis=(b-a).normalized();side=Vector((0,1,0)) if abs(axis.x)>.5 else Vector((1,0,0));side=(side-axis*side.dot(axis)).normalized();up=axis.cross(side).normalized()
 for plane in range(PLANES):
  theta=plane*math.pi/PLANES+phase;across=side*math.cos(theta)+up*math.sin(theta);rows=[]
  for j in range(5):
   t=j/4;c=a.lerp(b,t);alpha=1.
   rows.append([vertex(c-across*width/2,n,alpha),vertex(c+across*width/2,n,alpha)])
  for j in range(4):
   ids=[rows[j][0],rows[j][1],rows[j+1][1],rows[j+1][0]]
   uv=[(0,j/4),(1,j/4),(1,(j+1)/4),(0,(j+1)/4)]
   face(ids,uv,0)
counts=[]
for lod,PLANES in [(0,4),(1,3),(2,2),(3,1)]:
 name='PhoenixFlames'+(f'_LOD{lod}' if lod else '')
 verts=[];faces=[];uvs=[];slots=[];owners=[];alphas=[]
 for patch in patches:shell(*patch)
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();obj=bpy.data.objects.new(name,me);sc.collection.objects.link(obj)
 for mat in materials:me.materials.append(mat)
 colors=me.color_attributes.new(name='FlameOpacity',type='FLOAT_COLOR',domain='POINT')
 for i,alpha in enumerate(alphas):colors.data[i].color=(1,1,1,alpha)
 me.color_attributes.active_color=colors
 layer=me.uv_layers.new(name='UVMap')
 for f,uv,slot in zip(me.polygons,uvs,slots):
  f.material_index=slot
  for li,p in zip(f.loop_indices,uv):layer.data[li].uv=p
 for n,*_ in patches:
  name='Fire_'+n;g=obj.vertex_groups.new(name=name);g.add([i for i,owner in enumerate(owners) if owner==name],1.,'REPLACE')
 mod=obj.modifiers.new('PhoenixFireSkin','ARMATURE');mod.object=rig;obj.parent=rig;obj.hide_render=lod>0;counts.append(sum(len(f.vertices)-2 for f in me.polygons))
# Extend each existing action rather than replacing or retiming any body curve.
for action in bpy.data.actions:
 rig.animation_data_create();rig.animation_data.action=action
 for f in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
  t=f/32
  if action.name=='Dead':size=.00001
  elif action.name=='Death':
   u=max(0,min(1,(t-.18)/.42));size=max(.00001,1-u*u*(3-2*u))
  elif action.name in ('Attack','Cast'):size=1+.16*math.exp(-((t-.875)/.14)**2)
  else:size=1.
  for n,*_ in patches:
   pb=rig.pose.bones['Fire_'+n];pb.rotation_mode='QUATERNION';pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);flicker=1+.13*math.sin(2*math.pi*3*t+sum(map(ord,n)))*math.sin(math.pi*f/float(action.frame_range[1]))**2
   pb.scale=(size*flicker,)*3
   for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(prop,frame=f)
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'Fire_' in fc.data_path:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
triangles=counts[0];assert triangles<4000 and len(rig.data.bones)<128
(P/'work/flames.json').write_text(json.dumps({'patches':[p[0] for p in patches],'triangles':triangles,'lod_triangles':counts,'bones':len(rig.data.bones),'texture_sources':['textures/phoenix_plume.png'],'extinction_seconds':[.18,.60],'attack_pulse_seconds':.875,'scroll_uv_per_second':[0,0],'motion':'Loop-closed leaf-bone flicker. Static UVs retain soft plume boundaries; skinned vertex alpha is not rendered by the current runtime.'},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/flame_master.blend'));print('PHOENIX FLAMES',triangles,'triangles',len(rig.data.bones),'bones',flush=True)
