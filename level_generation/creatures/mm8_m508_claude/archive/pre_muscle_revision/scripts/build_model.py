"""MM8 Air Elemental: fitted torso plus accepted MM6 Air layered wind and Djinn upper-body clips.
Each opaque/effect part owns its LOD chain; width scaling stays on leaf bones.
"""
import bpy,bmesh,json,math,os
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];TEXTURES=str(P/'textures')
PROFILE=json.loads((P/'textures/profile.json').read_text());BODY_COLORS=json.loads((P/'textures/body_colors.json').read_text())
FPS=30;HIDDEN=.0001;N=6
DURATIONS={'Standing':3.,'Walking':1.2,'Running':.8,'Attack':1.5,'Cast':1.5,'Hit':22/30,'Fidget':2.4,'Death':.8,'Dead':1.}
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
    material = bpy.data.materials.new('AirElemental_Body')
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
        element.color = tuple(srgb_to_linear(c) for c in color) + (1.0,)
    geometry = nodes.new('ShaderNodeNewGeometry')
    key = nodes.new('ShaderNodeVectorMath')
    key.operation = 'DOT_PRODUCT'
    key.inputs[1].default_value = Vector((0.25, -0.55, 0.8)).normalized()
    shade = nodes.new('ShaderNodeMapRange')
    shade.inputs['From Min'].default_value = -1.0
    shade.inputs['From Max'].default_value = 1.0
    shade.inputs['To Min'].default_value = 0.65
    shade.inputs['To Max'].default_value = 1.12
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.15
    ao_range = nodes.new('ShaderNodeMapRange')
    ao_range.inputs['To Min'].default_value = 0.8
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
    head=nodes.new('ShaderNodeMapRange');head.inputs['From Min'].default_value=1.78;head.inputs['From Max'].default_value=1.92;head.inputs['To Min'].default_value=.55;head.inputs['To Max'].default_value=.12
    links.new(separate.outputs['Z'],head.inputs['Value'])
    calm=nodes.new('ShaderNodeMix');calm.data_type='FLOAT';calm.inputs['A'].default_value=.60
    links.new(head.outputs['Result'],calm.inputs['Factor']);links.new(noise.outputs['Fac'],calm.inputs['B']);links.new(calm.outputs['Result'],ramp.inputs['Fac'])
    links.new(geometry.outputs['Normal'], key.inputs[0])
    links.new(key.outputs['Value'], shade.inputs['Value'])
    links.new(ao.outputs['AO'], ao_range.inputs['Value'])
    links.new(ramp.outputs['Color'], multiply.inputs['A'])
    links.new(shade.outputs['Result'], multiply.inputs['B'])
    links.new(multiply.outputs['Result'], multiply2.inputs['A'])
    links.new(ao_range.outputs['Result'], multiply2.inputs['B'])
    links.new(multiply2.outputs['Result'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    image = bpy.data.images.new('m508_body', 1024, 1024)
    target = nodes.new('ShaderNodeTexImage')
    target.image = image
    nodes.active = target
    body.data.materials.clear()
    body.data.materials.append(material)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj == body)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.bake(type='EMIT', margin=8)
    path = os.path.join(TEXTURES, 'm508_body.png')
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
 parent=root
 for i in range(N):
  z=1.41-i*(1.41-.08)/N;b=bones.new(f'Funnel{i}');b.head=(0,0,z);b.tail=(0,0,z-(1.41-.08)/N);b.parent=parent;parent=b
  w=bones.new(f'Wind{i}');w.head=b.head;w.tail=b.tail;w.parent=b
 for side in ['Left','Right']:
  hand=bones[side+'Hand'];center=hand.head.lerp(hand.tail,.8)
  b=bones.new('Burst'+side);b.head=center;b.tail=center+Vector((0,0,.1));b.parent=hand
  socket=bones.new('Socket_Palm_'+side);socket.head=center;socket.tail=center+Vector((0,0,.06));socket.parent=hand;socket.use_deform=False
 for side,x in [('Left',.032),('Right',-.032)]:
  socket=bones.new('Socket_Eye_'+side);socket.head=(x,-.103,1.99);socket.tail=(x,-.163,1.99);socket.parent=bones['Head'];socket.use_deform=False
 b=bones.new('Dispersal');b.head=(0,0,1.12);b.tail=(0,0,1.22);b.parent=root
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
 def strip(self,rows,segments,repeats,phase,inward,weight):
  base=len(self.vertices)
  for z,rx,ry,v in rows:
   for k in range(segments):
    a=2*math.pi*k/segments;self.vertices.append((rx*math.cos(a),ry*math.sin(a),z));self.weights.append(weight(z))
  for j in range(len(rows)-1):
   for k in range(segments):
    nxt=(k+1)%segments;quad=[base+j*segments+k,base+(j+1)*segments+k,base+(j+1)*segments+nxt,base+j*segments+nxt]
    u0=phase+repeats*k/segments;u1=phase+repeats*(k+1)/segments;uv=[(u0,1-rows[j][3]),(u0,1-rows[j+1][3]),(u1,1-rows[j+1][3]),(u1,1-rows[j][3])]
    if inward:quad.reverse();uv.reverse()
    self.faces.extend([(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])]);self.uv.extend([[uv[0],uv[1],uv[2]],[uv[0],uv[2],uv[3]]])
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

def wind_weight(z):
 x=max(0,min(N-1,(1.41-z)/(1.41-.08)*N));i=min(int(x),N-2);f=x-i
 return {f'Wind{i}':1-f,f'Wind{i+1}':f}

def profile(t):
 k=t*(len(PROFILE['height_m'])-1);i=min(int(k),len(PROFILE['height_m'])-2);f=k-i
 return tuple(PROFILE[n][i]*(1-f)+PROFILE[n][i+1]*f for n in ['height_m','radius_m'])

def build_wind(rig,material,lod,segments,rings,wisps):
 out=EffectMesh('Wind'+lod,rig,material);layers=[]
 for k in range(wisps):
  t=.02+.9*k/wisps;z,r=profile(t);r=r*1.19+.02;v=.505+.21*((k*.618)%1)
  layers.append(([(z+.035,r,r,.503),(z-.035,r*.98,r*.98,.747)],max(8,segments-6),3.,k*.618))
 # A few soft waist wisps overlap the cut instead of presenting a solid horizontal seam.
 for k in range(3):
  z=1.31+k*.055;r=.22+k*.018;v=.52+k*.06
  layers.append(([(z+.05,r,r*.72,.503),(z-.05,r,r*.72,.747)],segments,2.,k*.25))
 for band,rscale,repeats in [(1,1.12,2.),(0,1.,1.)]:
  rows=[]
  for j in range(rings):
   t=j/(rings-1);z,r=profile(t);z+=.08*(1-t);r=max(.006,r*rscale)
   rows.append((z,r,r,.25*band+.003+.244*t))
  layers.append((rows,segments,repeats,0.))
 for inward in [True,False]:
  for rows,sg,repeats,phase in (layers if inward else reversed(layers)):out.strip(rows,sg,repeats,phase,inward,wind_weight)
 return out.finish()

def build_cloud(rig,material,lod,segments,count):
 out=EffectMesh('DeathCloud'+lod,rig,material);rows=[]
 for k in range(count+3):
  t=k/(count+2);z=1.15+.85*math.cos(math.pi*t);r=.015+.50*math.sin(math.pi*t)
  rows.append((z,r,r,.753+.244*t))
 for inward in [True,False]:out.strip(rows,segments,2.,.3,inward,lambda z:{'Dispersal':1.})
 return out.finish()

def build_bursts(rig,material,lod,quads):
 out=EffectMesh('Lightning'+lod,rig,material)
 for side in ['Left','Right']:
  n='Burst'+side;c=rig.data.bones[n].head_local
  axes=[(Vector((.33,0,0)),Vector((0,0,.33))),(Vector((0,.33,0)),Vector((0,0,.33))),(Vector((.33,0,0)),Vector((0,.33,0)))]
  for u,v in axes[:quads]:out.quad(c,u,v,n)
 return out.finish()

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
   t=f/FPS;phase=2*math.pi*f/count;dead=role in ['Death','Dead'];dt=.8 if role=='Dead' else t
   root=rig.pose.bones['Root'];root.location=(.012*math.sin(phase),0,.018*math.sin(phase)) if not dead else (0,0,0)
   if dead:
    hips=rig.pose.bones['Hips'];shrink=max(HIDDEN,1-ss((dt-.22)/.40));hips.scale=(shrink,)*3;hips.location.z+=.1*ss(dt/.6)
    for side,sign in [('Left',1),('Right',-1)]:
     pb=rig.pose.bones[side+'Arm'];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion((0,0,1),sign*.7*ss(dt/.24))
    rig.pose.bones['Spine2'].rotation_quaternion=rig.pose.bones['Spine2'].rotation_quaternion@Quaternion((1,0,0),-.18*ss(dt/.25))
   for i in range(N):
    pb=rig.pose.bones[f'Funnel{i}'];amp=(.018 if role=='Running' else .012)*(i+1)/N
    pb.rotation_quaternion=Quaternion((1,0,0),amp*math.sin(phase-i*.5))@Quaternion((0,0,1),amp*.6*math.cos(phase-i*.6))
    width=1+.035*math.sin(phase*2+i*.8)
    if dead:width*=1+.7*ss(dt/.35)
    rig.pose.bones[f'Wind{i}'].scale=(width,1,width)
   if dead:
    shrink=max(HIDDEN,1-ss((dt-.35)/.3));rig.pose.bones['Funnel0'].scale=(shrink,)*3
   for side in ['Left','Right']:
    burst=0.
    if role in ['Attack','Cast']:burst=ss((t-.22)/.22)*(1-ss((t-.85)/.21))*(.9+.1*math.sin(t*90))
    pb=rig.pose.bones['Burst'+side];pb.scale=(max(HIDDEN,burst),)*3;pb.rotation_quaternion=Quaternion((0,1,0),.3*math.sin(t*75))
   cloud=rig.pose.bones['Dispersal'];scale=max(HIDDEN,ss((dt-.12)/.16)*(1-ss((dt-.58)/.20))) if dead else HIDDEN
   cloud.scale=(scale*(1+1.2*ss(dt/.7)),scale*(1-.55*ss(dt/.75)),scale*(1+1.2*ss(dt/.7)))
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

def main():
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim.blend'));rig=bpy.data.objects['AirElemental_Rig'];body=bpy.data.objects['AirElemental_Body'];rig.animation_data_clear()
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();extend_rig(rig)
 # The waist cap gets a valid unwrap instead of collapsed UVs from the cut.
 bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.018);bpy.ops.object.mode_set(mode='OBJECT')
 bake_body_texture(body);windmat=effect_material('AirElemental_Wind','m508_wind.png');fxmat=effect_material('AirElemental_Lightning','m508_lightning.png')
 objects=[]
 for level,(ratio,segments,rings,wisps) in enumerate([(1.,24,12,12),(.5,16,9,8),(.25,10,6,5),(.08,6,3,2)]):
  suffix='' if level==0 else '_LOD'+str(level)
  objects.append(lod_body(body,ratio,'Body'+suffix));objects.append(build_wind(rig,windmat,suffix,segments,rings,wisps));objects.append(build_cloud(rig,windmat,suffix,max(6,segments-6),max(4,8-level)));objects.append(build_bursts(rig,fxmat,suffix,3 if level<2 else 2))
 bpy.data.objects.remove(body,do_unlink=True);animate(rig)
 for o in objects:o.hide_render='_LOD' in o.name
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/m508.blend'))
 for obj in bpy.data.objects:obj.select_set(obj in objects or obj==rig)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m508_raw.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 report={o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects};(P/'work/triangles.json').write_text(json.dumps(report,indent=2));print('TRIANGLES',report)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m508.blend'))
main()
