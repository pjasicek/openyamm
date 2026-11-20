"""MM8 Fire Elemental: floating figure plus MM6 Fire shell/fin method and Djinn upper-body clips.
Each opaque/effect part owns its LOD chain.
"""
import bpy,bmesh,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];TEXTURES=str(P/'textures')
BODY_COLORS=json.loads((P/'textures/body_colors.json').read_text())
FPS=30;HIDDEN=.0001
DURATIONS={'Standing':3.,'Walking':1.0,'Running':.8,'Attack':1.5,'Cast':1.5,'Hit':22/30,'Fidget':2.4,'Death':22/30,'Dead':1.}
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def action_curves(action):
    return [curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags
            for curve in bag.fcurves]


def assign(rig, action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


def bake_body_texture(body):
    """Pale turbulent colour and broad soft shading, baked for the unlit elemental material."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.cycles.device = 'CPU'
    material = bpy.data.materials.new('FireElemental_Body')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    coords = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 9.0
    noise.inputs['Detail'].default_value = 3.0
    noise.inputs['Roughness'].default_value = 0.6
    ramp = nodes.new('ShaderNodeValToRGB')
    stops = [0.3, 0.45, 0.55, 0.68, 0.8]
    elements = ramp.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, position, color in zip(elements, stops, BODY_COLORS['colors']):
        element.position = position
        element.color = tuple(srgb_to_linear(c*.78) for c in color) + (1.0,)
    geometry = nodes.new('ShaderNodeNewGeometry')
    key = nodes.new('ShaderNodeVectorMath')
    # Azimuth-neutral top light preserves the restored sculpt from front, side and back.
    key.operation = 'MULTIPLY'
    key.inputs[1].default_value = (1, 1, 0)
    radial = nodes.new('ShaderNodeVectorMath');radial.operation='LENGTH'
    radial_gain = nodes.new('ShaderNodeMath');radial_gain.operation='MULTIPLY';radial_gain.inputs[1].default_value=.60
    normal_axes = nodes.new('ShaderNodeSeparateXYZ')
    top_gain = nodes.new('ShaderNodeMath');top_gain.operation='MULTIPLY';top_gain.inputs[1].default_value=.80
    illumination = nodes.new('ShaderNodeMath');illumination.operation='ADD'
    links.new(key.outputs['Vector'],radial.inputs[0]);links.new(radial.outputs['Value'],radial_gain.inputs[0])
    links.new(geometry.outputs['Normal'],normal_axes.inputs[0]);links.new(normal_axes.outputs['Z'],top_gain.inputs[0])
    links.new(radial_gain.outputs[0],illumination.inputs[0]);links.new(top_gain.outputs[0],illumination.inputs[1])
    shade = nodes.new('ShaderNodeMapRange')
    shade.inputs['From Min'].default_value = 0.0
    shade.inputs['From Max'].default_value = 1.0
    shade.inputs['To Min'].default_value = 0.25
    shade.inputs['To Max'].default_value = 1.3
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.15
    ao_range = nodes.new('ShaderNodeMapRange')
    ao_range.inputs['To Min'].default_value = 0.38
    multiply = nodes.new('ShaderNodeMix')
    multiply.data_type = 'RGBA'
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs['Factor'].default_value = 1.0
    multiply2 = nodes.new('ShaderNodeMix')
    multiply2.data_type = 'RGBA'
    multiply2.blend_type = 'MULTIPLY'
    multiply2.inputs['Factor'].default_value = 1.0
    links.new(coords.outputs['Object'], noise.inputs['Vector'])
    separate=nodes.new('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Position'],separate.inputs['Vector'])
    head=nodes.new('ShaderNodeMapRange');head.inputs['From Min'].default_value=1.78;head.inputs['From Max'].default_value=1.92;head.inputs['To Min'].default_value=.85;head.inputs['To Max'].default_value=.45
    links.new(separate.outputs['Z'],head.inputs['Value'])
    calm=nodes.new('ShaderNodeMix');calm.data_type='FLOAT';calm.inputs['A'].default_value=.60
    links.new(head.outputs['Result'],calm.inputs['Factor']);links.new(noise.outputs['Fac'],calm.inputs['B']);links.new(calm.outputs['Result'],ramp.inputs['Fac'])
    links.new(geometry.outputs['Normal'], key.inputs[0])
    links.new(illumination.outputs[0], shade.inputs['Value'])
    links.new(ao.outputs['AO'], ao_range.inputs['Value'])
    links.new(ramp.outputs['Color'], multiply.inputs['A'])
    links.new(shade.outputs['Result'], multiply.inputs['B'])
    links.new(multiply.outputs['Result'], multiply2.inputs['A'])
    links.new(ao_range.outputs['Result'], multiply2.inputs['B'])
    links.new(multiply2.outputs['Result'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    image = bpy.data.images.new('m496_body', 1024, 1024)
    target = nodes.new('ShaderNodeTexImage')
    target.image = image
    nodes.active = target
    body.data.materials.clear()
    body.data.materials.append(material)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj == body)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.bake(type='EMIT', margin=8)
    path = os.path.join(TEXTURES, 'm496_body.png')
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    # Runtime material: the baked texture as base colour.
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(path, check_existing=False)
    links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return material


def add_eyes(body,rig):
 image=body.data.materials[0].node_tree.nodes.get('Image Texture').image
 pixels=np.array(image.pixels[:],dtype=np.float32).reshape(1024,1024,4)
 atlas=bpy.data.images.new('m496_body_atlas',1040,1024)
 data=np.empty((1024,1040,4),np.float32);data[:,16:]=pixels;data[:,:16]=[1.,.88,.30,1.]
 atlas.pixels.foreach_set(data.ravel());atlas.filepath_raw=image.filepath_raw;atlas.file_format='PNG';atlas.save()
 body.data.materials[0].node_tree.nodes.get('Image Texture').image=atlas
 for uv in body.data.uv_layers.active.data:uv.uv.x=(16+1024*uv.uv.x)/1040
 parts=[body]
 for side in ['Left','Right']:
  socket=rig.data.bones['Socket_Eye_'+side];center=socket.head_local.copy()
  # Fit each eye to the front surface, instead of using the template's removed eye helpers.
  nearby=[v.co.y for v in body.data.vertices if abs(v.co.x-center.x)<.025 and abs(v.co.z-center.z)<.025]
  assert nearby
  center.y=min(nearby)-.004
  bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1,location=center)
  eye=bpy.context.object;eye.scale=(.013,.006,.009);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  for uv in eye.data.uv_layers.active.data:uv.uv=(4/1040,4/1024)
  eye.data.materials.append(body.data.materials[0]);group=eye.vertex_groups.new(name='Head');group.add(list(range(len(eye.data.vertices))),1.,'REPLACE');parts.append(eye)
 for obj in bpy.context.scene.objects:obj.select_set(obj in parts)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join()


def lod_body(body, ratio, name):
    copy = body.copy()
    copy.data = body.data.copy()
    copy.name = copy.data.name = name
    bpy.context.collection.objects.link(copy)
    if ratio < 1.0:
        modifier = copy.modifiers.new('Decimate', 'DECIMATE')
        modifier.ratio = ratio
        modifier.use_symmetry = True
        modifier.symmetry_axis = 'X'
        bpy.context.view_layer.objects.active = copy
        bpy.ops.object.modifier_move_to_index(modifier='Decimate', index=0)
        bpy.ops.object.modifier_apply(modifier='Decimate')
    return copy


def ss(x):
 x=max(0.,min(1.,x));return x*x*(3-2*x)

def extend_rig(rig):
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bones=rig.data.edit_bones
 root=bones.new('Root');root.head=(0,0,0);root.tail=(0,0,.1);bones['Hips'].parent=root
 for side in ['Left','Right']:
  hand=bones[side+'Hand'];center=hand.head.lerp(hand.tail,.8)
  b=bones.new('Burst'+side);b.head=center;b.tail=center+Vector((0,0,.1));b.parent=hand
  socket=bones.new('Socket_Palm_'+side);socket.head=center;socket.tail=center+Vector((0,0,.06));socket.parent=hand;socket.use_deform=False
 for side,x in [('Left',.027),('Right',-.027)]:
  socket=bones.new('Socket_Eye_'+side);z=bones['Head'].head.z+.105;socket.head=(x,-.080,z);socket.tail=(x,-.14,z);socket.parent=bones['Head'];socket.use_deform=False
 b=bones.new('AshRoot');b.head=(0,0,0);b.tail=(0,0,.1);b.parent=root
 bpy.ops.object.mode_set(mode='OBJECT')
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'

def effect_material(name,file):
 m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');tx=nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/'textures'/file),check_existing=True)
 m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
 m.node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha']);m.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);m.surface_render_method='BLENDED';m.use_backface_culling=True
 return m

class EffectMesh:
 def __init__(self,name,rig,material):
  self.name=name;self.rig=rig;self.material=material;self.vertices=[];self.faces=[];self.uv=[];self.weights=[]
 def quad(self,center,u,v,bone):
  base=len(self.vertices);self.vertices.extend([center-u-v,center+u-v,center+u+v,center-u+v]);self.weights.extend([{bone:1}]*4)
  for face,uv in [((0,1,2),[(0,0),(1,0),(1,1)]),((0,2,3),[(0,0),(1,1),(0,1)])]:
   self.faces.append(tuple(base+i for i in face));self.uv.append(uv)
 
 def finish(self):
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.vertices,[],self.faces);me.update();uv=me.uv_layers.new(name='UVMap')
  for poly,coords in zip(me.polygons,self.uv):
   poly.use_smooth=True
   for loop,co in zip(poly.loop_indices,coords):uv.data[loop].uv=co
  obj=bpy.data.objects.new(self.name,me);bpy.context.collection.objects.link(obj);obj.parent=self.rig
  for n in sorted({n for w in self.weights for n in w}):
   group=obj.vertex_groups.new(name=n)
   for i,w in enumerate(self.weights):
    if n in w:group.add([i],w[n],'REPLACE')
  mod=obj.modifiers.new('Armature','ARMATURE');mod.object=self.rig;me.materials.append(self.material);return obj

def build_flames(rig,material,lod,segments):
 out=EffectMesh('Flame'+lod,rig,material)
 # Overlapping translucent envelopes follow the figure's anatomy, with one inside and one outside face.
 parts=[('Spine2',rig.data.bones['Hips'].head_local-Vector((0,0,.05)),rig.data.bones['Neck'].head_local,.245,.16),
        ('Head',rig.data.bones['Head'].head_local,rig.data.bones['Head'].tail_local,.11,.105)]
 for side in ['Left','Right']:
  for name,rx,ry in [('Arm',.10,.10),('ForeArm',.075,.075),('Hand',.065,.07),('UpLeg',.12,.12),('Leg',.08,.08),('Foot',.07,.08)]:
   bone=rig.data.bones[side+name];parts.append((side+name,bone.head_local,bone.tail_local,rx,ry))
 for part,(bone,start,end,rx,ry) in enumerate(parts):
  direction=(end-start).normalized();u=direction.cross(Vector((0,1,0)))
  if u.length<.1:u=direction.cross(Vector((1,0,0)))
  u.normalize();v=direction.cross(u).normalized();length=(end-start).length
  rows=5 if lod=='' else 4 if lod=='_LOD1' else 3
  for inward in [True,False]:
   base=len(out.vertices)
   for j in range(rows):
    t=j/(rows-1);center=start.lerp(end,t);radius=(.75+.25*math.sin(math.pi*t))*(1-.75*ss((t-.7)/.3)) if part==0 else .02+.98*math.sin(math.pi*t)**.5 if bone=='Head' else .75+.25*math.sin(math.pi*t)
    for k in range(segments):
     angle=2*math.pi*k/segments;out.vertices.append(center+radius*(rx*math.cos(angle)*u+ry*math.sin(angle)*v));out.weights.append({bone:1.})
   for j in range(rows-1):
    for k in range(segments):
     kn=(k+1)%segments;quad=[base+j*segments+k,base+(j+1)*segments+k,base+(j+1)*segments+kn,base+j*segments+kn]
     uv=[(k/segments,part*.173+j/(rows-1)*length/.75),(k/segments,part*.173+(j+1)/(rows-1)*length/.75),((k+1)/segments,part*.173+(j+1)/(rows-1)*length/.75),((k+1)/segments,part*.173+j/(rows-1)*length/.75)]
     if inward:quad.reverse();uv.reverse()
     out.faces.extend([(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])]);out.uv.extend([[uv[0],uv[1],uv[2]],[uv[0],uv[2],uv[3]]])
 return out.finish()

def build_tongues(rig,material,lod,quads):
 out=EffectMesh('Tongues'+lod,rig,material)
 parts=[('Head',rig.data.bones['Head'].head_local+Vector((0,0,.23)),.20,.29)]
 for side in ['Left','Right']:
  for name,width,height in [('Arm',.10,.18),('ForeArm',.085,.18),('UpLeg',.10,.25),('Leg',.08,.22)]:
   b=rig.data.bones[side+name];parts.append((side+name,b.head_local.lerp(b.tail_local,.55),width,height))
 for bone,center,width,height in parts:
  for k in range(quads):
   angle=k*math.pi/quads;u=Vector((math.cos(angle)*width,math.sin(angle)*width,0));v=Vector((0,0,height));out.quad(center,u,v,bone)
   for triangle in out.uv[-2:]:
    for index,(x,y) in enumerate(triangle):triangle[index]=(.5*x+(.5 if bone=='Head' else 0),y)
 return out.finish()

def build_bursts(rig,material,lod,quads):
 out=EffectMesh('Burst'+lod,rig,material)
 for side in ['Left','Right']:
  n='Burst'+side;c=rig.data.bones[n].head_local
  for k in range(quads):
   a=k*math.pi/quads;out.quad(c+Vector((0,0,.20)),Vector((.23*math.cos(a),.23*math.sin(a),0)),Vector((0,0,.35)),n)
   for triangle in out.uv[-2:]:
    for index,(x,y) in enumerate(triangle):triangle[index]=(x*.5,y)
 return out.finish()

def build_ash(rig,material,lod,segments):
 out=EffectMesh('Ash'+lod,rig,material)
 for j in range(4):
  t=j/3;r=.015+.585*t;z=.09*(1-t*t)+.005
  for k in range(segments):
   a=2*math.pi*k/segments;out.vertices.append((r*math.cos(a),r*.6*math.sin(a),z));out.weights.append({'AshRoot':1.})
 for k in range(1,segments-1):
  tri=(0,k,k+1);out.faces.append(tri);out.uv.append([((out.vertices[i][0]/1.2+.5),out.vertices[i][1]/.72+.5) for i in tri])
 for j in range(3):
  for k in range(segments):
   kn=(k+1)%segments;quad=[j*segments+k,(j+1)*segments+k,(j+1)*segments+kn,j*segments+kn]
   for tri in [(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])]:
    out.faces.append(tri);out.uv.append([((out.vertices[i][0]/1.2+.5),out.vertices[i][1]/.72+.5) for i in tri])
 return out.finish()

def flight_pose(rig, phase):
 """Native m496W: leading left fist, trailing right arm and an asymmetric folded-leg flight cycle."""
 for bone in rig.pose.bones:
  bone.matrix_basis=Matrix.Identity(4)
 root=rig.pose.bones['Root'];pivot=rig.data.bones['Hips'].head_local
 root.rotation_quaternion=Quaternion((1,0,0),math.radians(36)+.025*math.sin(phase))
 offset=pivot-root.rotation_quaternion@pivot+Vector((0,0,.055+.025*math.sin(phase)))
 root.location=root.bone.matrix_local.to_3x3().inverted()@offset
 bpy.context.view_layer.update()

 def rotate_world(name,axis,angle):
  bone=rig.pose.bones[name];head=bone.head.copy()
  bone.matrix=Matrix.Translation(head)@Quaternion(axis,angle).to_matrix().to_4x4()@Matrix.Translation(-head)@bone.matrix
  bpy.context.view_layer.update()

 def aim(name,direction):
  bone=rig.pose.bones[name];current=(bone.tail-bone.head).normalized()
  turn=current.rotation_difference(Vector(direction).normalized())
  rotate_world(name,turn.axis,turn.angle)

 for name,angle in [('Spine',6),('Spine1',4),('Spine2',4),('Neck',-24),('Head',-20)]:
  rotate_world(name,Vector((1,0,0)),math.radians(angle))
 # Keep the leading arm orientation steady through the body's pitch cycle.
 rotate_world('LeftShoulder',Vector((1,0,0)),-.025*math.sin(phase))
 rotate_world('LeftShoulder',Vector((0,1,0)),math.radians(40))
 rotate_world('LeftShoulder',Vector((1,0,0)),math.radians(50))
 for side,direction,flex in [('Left',(.025,-1.,-.035),20),
                             ('Right',(-.025,.88,-.47),20)]:
  upper,lower,hand=[side+part for part in ['Arm','ForeArm','Hand']]
  aim(upper,direction)
  if side=='Left':rotate_world(upper,(rig.pose.bones[upper].tail-rig.pose.bones[upper].head).normalized(),math.radians(-30))
  rest_upper=rig.data.bones[upper];rest_lower=rig.data.bones[lower]
  u=(rest_lower.head_local-rest_upper.head_local).normalized()
  v=(rig.data.bones[hand].head_local-rest_lower.head_local).normalized()
  delta=rig.pose.bones[upper].matrix.to_quaternion()@rest_upper.matrix_local.to_quaternion().inverted()
  rotate_world(lower,delta@u.cross(v).normalized(),math.radians(flex)-u.angle(v))
  for finger in ['Thumb','Index','Middle','Ring','Pinky']:
   for joint,angle in [(1,.50),(2,1.05),(3,.75)]:
    bone=rig.pose.bones.get(side+'Hand'+finger+str(joint))
    if bone:bone.rotation_quaternion=Quaternion((1,0,0),angle*(.40 if finger=='Thumb' else 1.))
 for side in ['Left','Right']:
  if side=='Left':
   thigh=(0,-.20-.045*math.sin(phase),-.34)
   shin=(0,.29,-.21+.12*math.sin(phase))
  else:
   thigh=(0,.12,-.36)
   shin=(0,.31,.11+.02*math.sin(phase+.5))
  aim(side+'UpLeg',thigh);aim(side+'Leg',shin);aim(side+'Foot',(0,.16,-.12))
 bpy.context.view_layer.update()


def animate(rig):
 sources={role:bpy.data.actions[role] for role in DURATIONS if role in bpy.data.actions}
 for role,a in sources.items():a.name='Source_'+role
 for role,seconds in DURATIONS.items():
  source=sources['Standing' if role in ['Death','Dead'] else role];count=round(seconds*FPS);keys=[]
  for f in range(count+1):
   rig.animation_data_clear()
   for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
   assign(rig,source);source_frame=1+f if role not in ['Death','Dead'] else 1
   bpy.context.scene.frame_set(source_frame);bpy.context.view_layer.update()
   t=f/FPS;phase=2*math.pi*f/count;dead=role in ['Death','Dead'];dt=.75 if role=='Dead' else t
   root=rig.pose.bones['Root'];root.location=(.012*math.sin(phase),0,.018*math.sin(phase)) if not dead else (0,0,0)
   if dead:
    hips=rig.pose.bones['Hips'];shrink=max(HIDDEN,1-ss((dt-.22)/.45));hips.scale=(shrink,)*3;hips.location.z+=.1*ss(dt/.6)
    for side,sign in [('Left',1),('Right',-1)]:
     pb=rig.pose.bones[side+'Arm'];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion((0,0,1),sign*.7*ss(dt/.24))
    rig.pose.bones['Spine2'].rotation_quaternion=rig.pose.bones['Spine2'].rotation_quaternion@Quaternion((1,0,0),-.18*ss(dt/.25))
   for side,sign in [('Left',1),('Right',-1)]:
    rig.pose.bones[side+'UpLeg'].rotation_quaternion=Quaternion((1,0,0),-.16-.05*math.sin(phase+sign*.25))
    rig.pose.bones[side+'Leg'].rotation_quaternion=Quaternion((1,0,0),.38+.06*math.sin(phase+sign*.25))
    rig.pose.bones[side+'Foot'].rotation_quaternion=Quaternion((1,0,0),-.18)
   if role in ['Walking','Running']:flight_pose(rig,phase)
   ash=max(HIDDEN,ss((dt-.38)/.30)) if dead else HIDDEN
   rig.pose.bones['AshRoot'].scale=(ash,)*3
   for side in ['Left','Right']:
    burst=0.
    if role in ['Attack','Cast']:burst=ss((t-.22)/.22)*(1-ss((t-.85)/.21))*(.9+.1*math.sin(t*90))
    pb=rig.pose.bones['Burst'+side];pb.scale=(max(HIDDEN,burst),)*3;pb.rotation_quaternion=Quaternion((0,1,0),.3*math.sin(t*75))
   keys.append({pb.name:(pb.location.copy(),pb.rotation_quaternion.copy(),pb.scale.copy()) for pb in rig.pose.bones})
  rig.animation_data_clear();action=bpy.data.actions.new(role);action.use_fake_user=True;assign(rig,action)
  previous={}
  for f,key in enumerate(keys):
   for pb in rig.pose.bones:
    loc,q,scale=key[pb.name]
    if pb.name in previous and q.dot(previous[pb.name])<0:q.negate()
    previous[pb.name]=q.copy();pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
    for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f+1)
  for fc in action_curves(action):
   for kp in fc.keyframe_points:kp.interpolation='LINEAR'
  print('COMPOSE',role,count+1)
 for action in sources.values():bpy.data.actions.remove(action)
 assign(rig,bpy.data.actions['Standing']);bpy.context.scene.frame_set(1)

def unwrap_body(body):
    """Smaller projection charts keep curved muscle surfaces from folding over themselves."""
    bpy.context.view_layer.objects.active=body;body.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=.55, island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh=body.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active.data;n=1024
    owner=np.full((n,n),-1,np.int32);overlaps=set()
    for tri in mesh.loop_triangles:
        a,b,c=[np.array(uv[loop].uv)*n for loop in tri.loops]
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-9:continue
        low=np.maximum(np.floor(np.minimum(np.minimum(a,b),c)).astype(int),0)
        high=np.minimum(np.ceil(np.maximum(np.maximum(a,b),c)).astype(int),n-1)
        x,y=np.meshgrid(np.arange(low[0],high[0]+1)+.5,np.arange(low[1],high[1]+1)+.5)
        u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        inside=(u>1e-6)&(v>1e-6)&(1-u-v>1e-6)
        iy,ix=(y[inside]-.5).astype(int),(x[inside]-.5).astype(int)
        previous=owner[iy,ix]
        if (previous>=0).any():overlaps.add(tri.polygon_index)
        owner[iy,ix]=tri.polygon_index
    assert not overlaps, ('Overlapping UV faces', sorted(overlaps))
    print('BODY UV: no overlapping texel centres at 1024',flush=True)


def main():
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim.blend'));rig=bpy.data.objects['FireElemental_Rig'];body=bpy.data.objects['FireElemental_Body'];rig.animation_data_clear()
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();extend_rig(rig)
 # The waist cap gets a valid unwrap instead of collapsed UVs from the cut.
 unwrap_body(body)
 bake_body_texture(body);add_eyes(body,rig);flamemat=effect_material('FireElemental_Flame','m496_flame.png');fxmat=effect_material('FireElemental_Burst','m496_burst.png');ashmat=effect_material('FireElemental_Ash','m496_ash.png')
 objects=[]
 for level,(ratio,segments) in enumerate([(1.,12),(.5,8),(.25,6),(.08,4)]):
  suffix='' if level==0 else '_LOD'+str(level)
  objects.extend([lod_body(body,ratio,'Body'+suffix),build_flames(rig,flamemat,suffix,segments),build_tongues(rig,fxmat,suffix,3 if level<2 else 2),build_bursts(rig,fxmat,suffix,3 if level<2 else 2),build_ash(rig,ashmat,suffix,8 if level<2 else 4)])
 bpy.data.objects.remove(body,do_unlink=True);animate(rig)
 for o in objects:o.hide_render='_LOD' in o.name
 save_export(rig,objects)

def save_export(rig,objects):
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/m496.blend'))
 for obj in bpy.data.objects:obj.select_set(obj in objects or obj==rig)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m496_raw.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 report={o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects};(P/'work/triangles.json').write_text(json.dumps(report,indent=2));print('TRIANGLES',report)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m496.blend'))
if __name__=='__main__':
 main()
