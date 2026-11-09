"""One-bone Brood actors from the frozen hes_egg_mound source; no Meshy or shared-project writes."""
import json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
NAMES=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['egg_cluster','brood_sac','ganglion']


def select(objects,active=None):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=active or objects[0]


def triangles(o):return sum(len(f.vertices)-2 for f in o.data.polygons)


def material(name,energy=False,magenta=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 for suffix in ['basecolor','normal','mr']:
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures'/('brood_'+suffix+'.png')),check_existing=True)
  t.image.colorspace_settings.name='sRGB' if suffix=='basecolor' else 'Non-Color'
  if suffix=='basecolor':l.new(t.outputs['Color'],p.inputs['Base Color'])
  elif suffix=='normal':
   normal=n.new('ShaderNodeNormalMap');l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
  else:
   sep=n.new('ShaderNodeSeparateColor');l.new(t.outputs['Color'],sep.inputs['Color']);l.new(sep.outputs['Green'],p.inputs['Roughness']);l.new(sep.outputs['Blue'],p.inputs['Metallic'])
 if energy:
  p.inputs['Emission Color'].default_value=(*((0.18,0.006,0.075) if magenta else (0.22,0.035,0.002)),1)
  p.inputs['Emission Strength'].default_value=1
 return m


def source():
 bpy.ops.import_scene.gltf(filepath=str(P/'source/hes_egg_mound_export.glb'))
 o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
 bm.verts.ensure_lookup_table();bm.to_mesh(o.data);bm.free()
 for loop in o.data.uv_layers.active.data:loop.uv.x*=0.5
 return o


def egg(src,dimensions,centre):
 # Source component 10 is the largest complete egg, measured in source_components.json.
 keep=set(json.loads((P/'work/source_components.json').read_text())[10]['vertices'])
 bm=bmesh.new();bm.from_mesh(src.data);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in keep],context='VERTS')
 me=bpy.data.meshes.new('Egg');bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new('Egg',me);bpy.context.scene.collection.objects.link(o)
 lo=Vector([min(v.co[i] for v in me.vertices) for i in range(3)])
 hi=Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
 for v in me.vertices:
  for i in range(3):v.co[i]=(v.co[i]-(lo[i]+hi[i])/2)/(hi[i]-lo[i])*dimensions[i]+centre[i]
 for f in me.polygons:f.use_smooth=True
 return o


def swatch(o,region):
 # Swatches are well inside their padded rectangles in the shared atlas.
 uv={'bone':(0.625,0.5),'resin':(0.86,0.75),'nerve':(0.86,0.25)}[region]
 layer=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
 for face in o.data.polygons:
  for i,li in enumerate(face.loop_indices):
   a=2*math.pi*i/len(face.loop_indices);layer.data[li].uv=(uv[0]+.045*math.cos(a),uv[1]+.045*math.sin(a))


def tube(points,radius,region):
 curve=bpy.data.curves.new('Support','CURVE');curve.dimensions='3D';curve.resolution_u=3
 curve.bevel_depth=radius;curve.bevel_resolution=1;curve.use_fill_caps=True
 s=curve.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for i,(b,co) in enumerate(zip(s.bezier_points,points)):
  b.co=co;b.handle_left_type=b.handle_right_type='AUTO';b.radius=0.65 if i in [0,len(points)-1] else 1
 o=bpy.data.objects.new('Support',curve);bpy.context.scene.collection.objects.link(o);select([o])
 bpy.ops.object.convert(target='MESH');o=bpy.context.object;swatch(o,region)
 for f in o.data.polygons:f.use_smooth=True
 return o


def build(name):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene;scene.render.fps=30
 src=source();base=material('Brood');energy=material('Brood_Energy',True,name=='ganglion')
 src.data.materials.clear();src.data.materials.append(base);src.data.materials.append(energy)
 if name=='egg_cluster':
  body=src
  # Complete egg surfaces glow; resin/scaffold remains non-emissive.
  comps=json.loads((P/'work/source_components.json').read_text());eggs=set(v for c in comps if c['closed'] and c['tris']>=60 for v in c['vertices'])
  for f in body.data.polygons:f.material_index=int(all(v in eggs for v in f.vertices))
 else:
  pieces=[]
  if name=='brood_sac':
   pieces.append((egg(src,(0.40,0.36,0.63),(0,0,0.72)),energy))
   for i in range(3):
    a=2*math.pi*i/3;c,s=math.cos(a),math.sin(a)
    pieces.append((tube([(0.34*c,0.34*s,0.04),(0.19*c,0.19*s,0.21),(0.10*c,0.10*s,0.43),(0.14*c,0.14*s,0.62)],0.055,'resin'),base))
    pieces.append((tube([(0.29*c,0.29*s,0.035),(0.25*c,0.25*s,0.48),(0.22*c,0.22*s,0.86),(0.10*c,0.10*s,1.06)],0.025,'bone'),base))
    pieces.append((tube([(0,0,0.055),(0.19*c,0.18*s,0.03),(0.39*c,0.39*s,0.024)],0.027,'resin'),base))
  else:
   # Broad, folded nerve mass on an open bone plinth; unequal lobes avoid a stack of eggs.
   for x,y,z,dx,dy,dz in [(-.20,-.16,.62,.43,.43,.31),(.17,-.18,.65,.46,.42,.34),(-.24,.16,.68,.40,.45,.33),(.19,.15,.70,.45,.45,.34),(-.08,.02,.83,.44,.40,.30),(.02,-.24,.78,.40,.32,.27),(-.08,.26,.78,.40,.32,.27)]:
    pieces.append((egg(src,(dx,dy,dz),(x,y,z)),energy))
   for i in range(6):
    a=2*math.pi*i/6;c,s=math.cos(a),math.sin(a)
    pieces.append((tube([(0.42*c,0.42*s,0.03),(0.27*c,0.27*s,0.21),(0.29*c,0.29*s,0.47),(0.36*c,0.36*s,0.57)],0.045,'bone'),base))
   ring=[(.31*math.cos(i*math.pi/4),.31*math.sin(i*math.pi/4),.43) for i in range(9)]
   pieces.append((tube(ring,0.045,'bone'),base))
   for i in range(5):
    x=(i-2)*.095
    pieces.append((tube([(x,.17,.57),(x,.37,.30),(x+.12,.55,.12),(x+.18,.70,.04)],.028,'resin'),base))
   for i in range(5):
    y=-.24+i*.12
    pieces.append((tube([(-.34,y,.65),(-.20,y-.02,.81),(0,y+.03,.91),(.19,y,.84),(.35,y,.70)],.020,'nerve'),energy))
  for o,m in pieces:o.data.materials.clear();o.data.materials.append(m)
  bpy.data.objects.remove(src,do_unlink=True)
  select([o for o,_ in pieces]);bpy.ops.object.join();body=bpy.context.object
 body.name=body.data.name='BroodBody'
 # Recalculate closed-piece winding; leave open organic edges present in the approved source.
 bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
 lo=Vector([min(v.co[i] for v in body.data.vertices) for i in range(3)])
 hi=Vector([max(v.co[i] for v in body.data.vertices) for i in range(3)])
 h={'egg_cluster':.75,'brood_sac':1.2,'ganglion':1.5}[name]
 factor=h/(hi.z-lo.z);centre=Vector(((hi.x+lo.x)/2,(hi.y+lo.y)/2,lo.z))
 for v in body.data.vertices:v.co=(v.co-centre)*factor
 select([body]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 # One deform bone at ground level; scaling cannot lift the lowest point off the floor.
 rig=bpy.data.objects.new('BroodRig',bpy.data.armatures.new('BroodRig'));scene.collection.objects.link(rig)
 select([rig]);bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('B_Root');bone.head=(0,0,0);bone.tail=(0,0,h*.4);bpy.ops.object.mode_set(mode='OBJECT')
 group=body.vertex_groups.new(name='B_Root');group.add(list(range(len(body.data.vertices))),1,'REPLACE')
 mod=body.modifiers.new('Rig','ARMATURE');mod.object=rig;body.parent=rig
 rig.animation_data_create();pb=rig.pose.bones['B_Root'];pb.rotation_mode='QUATERNION'
 poses={'Standing':[(f,(1+.012*math.sin(2*math.pi*f/90),1+.022*math.sin(2*math.pi*f/90),1+.012*math.sin(2*math.pi*f/90))) for f in range(91)],
        'Hit':[(0,(1,1,1)),(3,(1.045,.91,1.045)),(7,(.985,1.025,.985)),(12,(1,1,1))],
        'Death':[(0,(1,1,1)),(5,(1.035,1.02,1.035)),(21,(1.15,.38,1.15)),(36,(1.14,.32,1.14))],
        'Dead':[(0,(1.14,.32,1.14)),(30,(1.14,.32,1.14))]}
 gates={}
 for clip,keys in poses.items():
  a=bpy.data.actions.new(clip);a.use_fake_user=True;rig.animation_data.action=a
  for frame,scale in keys:
   pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=scale
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=frame)
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
  a.use_frame_range=True;a.frame_start=0;a.frame_end=keys[-1][0]
  mins=[]
  for frame in range(keys[-1][0]+1):
   scene.frame_set(frame);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   mins.append(min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
  assert min(mins)>-1e-5 and max(mins)<1e-5,(clip,min(mins),max(mins))
  gates[clip]={'frames':keys[-1][0]+1,'duration':keys[-1][0]/30,'floor_min':min(mins),'floor_max':max(mins)}
 rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0)
 select([body,rig],rig)
 out=P/'export'/('hes_'+name+'_lod0.glb')
 bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export'/('hes_'+name+'.blend')))
 info={'name':name,'triangles':triangles(body),'height':h,'bone_count':1,'clips':gates,'source':'source/hes_egg_mound_export.glb','floor_pass':True}
 (P/'review'/(name+'_build.json')).write_text(json.dumps(info,indent=2)+'\n');print('BROOD_BUILD',json.dumps(info))

for name in NAMES:
 assert name in ['egg_cluster','brood_sac','ganglion'],name
 build(name)
