"""Export the posed master for independent runtime-format gates, with component materials for diagnostics."""
import bpy,json,sys,subprocess,math
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1]
arguments=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
blend=arguments[0] if arguments else 'rig_motion.blend'
prefix=arguments[1] if len(arguments)>1 else 'pilot'
bpy.ops.wm.open_mainfile(filepath=str(p/'work'/blend));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sword=bpy.data.objects['SwordMesh']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update();piece=[v.value for v in body.data.attributes['piece'].data]
names=['Skin','Mantle','Belt','BracerR','BracerL','Loincloth','Buckle','Head'];body.data.materials.clear()
for name in names:
 m=bpy.data.materials.new(name);m.use_nodes=True;body.data.materials.append(m)
for f in body.data.polygons:f.material_index=piece[f.vertices[0]]
for o in bpy.data.objects:o.select_set(o in (body,sword))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='LizardmanPilot'
keep=('Standing','Walking','Attack','Attack2','Hit','Fidget','Death','Dead')
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a);continue
 a.frame_end*=4;a.frame_start*=4
 curves=[fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
 groups={}
 for fc in curves:
  for k in fc.keyframe_points:
   k.interpolation='LINEAR';k.co[0]*=4
  fc.update()
  if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
 for group in groups.values():
  if len(group)!=4:continue
  keys=[group[i].keyframe_points for i in range(4)];prev=None
  for j in range(min(map(len,keys))):
   q=[keys[i][j].co[1] for i in range(4)]
   if prev is not None and sum(a*b for a,b in zip(q,prev))<0:
    for i in range(4):keys[i][j].co[1]*=-1
    q=[-v for v in q]
   prev=q
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig;bpy.context.scene.render.fps=120;bpy.context.scene.render.fps_base=1
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
bpy.ops.export_scene.gltf(filepath=str(p/('export/'+prefix+'_combined.glb')),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
hands={}
for side in 'RL':
 hand=rig.data.bones['B_'+side+'_Hand'];inv=hand.matrix_local.inverted();roots=['B_'+side+'_Finger'+str(i) for i in (0,1,2,4)]
 normal=Vector(json.load(open(p/('work/grip_pose_'+side+'.json')))['palm_axis_hand_local'])
 hands[side]={'fingers':roots,'palm_axis':list(normal)}

pelvis=rig.data.bones['B_Pelvis'].matrix_local;point=pelvis.inverted()@Vector((0,-.03,.64));axis=pelvis.to_3x3().inverted()@Vector((0,0,-1))
config={'version':1,'hands':hands,'thresholds':{'wrist_flexion_deg':60},'props':[{'name':'sword','file':'export/'+prefix+'_sword.glb','node':'Socket_Sword','kind':'melee','grip_point':[0,.075,0],'tip':[0,1.42,0],'edge_axis':[1,0,0],'hands':[{'side':'R','surface':{'bounds':[[-.04,-.04,-.00001],[.04,.04,.15001]]}},{'side':'L','grip_point':[0,-.075,0],'surface':{'bounds':[[-.04,-.04,-.15001],[.04,.04,.00001]]},'intervals':{'Death':[[0,3/30]],'Dead':[]}}]}],
 'regions':{'mantle':{'materials':['Mantle']},'loincloth':{'materials':['Loincloth']},'head_obstacles':{'weights':['B_Spine*','B_*_Clavicle','B_*_UpperArm*'],'weight_min':.2}},
 'cloth':[{'name':'mantle','surface':'mantle','samples':{'weights':['B_*_Forearm*','B_*_Hand','B_*_Finger*'],'weight_min':.5},'containment':False,'opening':{'axis':[0,0,-1]}},{'name':'loincloth','surface':'loincloth','samples':{'weights':['B_*_Thigh','B_*_Calf'],'weight_min':.5},'containment':False,'opening':{'node':'B_Pelvis','point':list(point),'axis':list(axis)}}],
 'posture':{'*':{'pelvis_min_m':.5,'pelvis_max_m':1.3,'trunk_lean_deg':65},'Death':{'pelvis_min_m':.02,'pelvis_max_m':1.3,'trunk_lean_deg':180},'Dead':{'pelvis_min_m':.02,'pelvis_max_m':.5,'trunk_lean_deg':180}},'refine_hz':48}
limits=json.load(open(p/'work/source_motion_limits.json'))
if 'attack_source_limits' in bpy.context.scene:limits['Attack']=json.loads(bpy.context.scene['attack_source_limits'])
limits['Attack2']=limits['Attack']
config['source_rotation_limits']={clip:{key:value for key,value in data.items() if key in ('arms','hands')} for clip,data in limits.items()}
# Preserve the verified source's fast cuts; idle and walk keep the common acceleration gate.
config['clip_thresholds']={clip:{'angular_acceleration_deg_s2':max(data['arms_acceleration'],data['hands_acceleration'])*1.1} for clip,data in limits.items() if clip in ('Attack','Attack2','Hit','Death')}
config['props'][0]['impacts']={clip:float(bpy.context.scene.get('attack_impact_seconds',.4895833333)) for clip in ('Attack','Attack2')}
json.dump(config,open(p/(prefix+'.gates.json'),'w'),indent=2)
subprocess.run(['python3',str(p/'scripts/split_pilot.py'),prefix],check=True)
