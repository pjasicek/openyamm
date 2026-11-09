"""Package named skeletal/corrective clips and render visual review views in Blender."""
import bpy
import json
from pathlib import Path
from math import pi
from mathutils import Vector

ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
scene=bpy.data.scenes['Brown ghost sprite studio']
bpy.context.window.scene=scene
rig=scene.objects['Ghost RIG']
obj=next(o for o in scene.objects if o.type=='MESH')
keys=obj.data.shape_keys
pose_plan=json.loads((ROOT/'poses.json').read_text())
# 24 fps clips have new idle/float motion, attack anticipation and follow-through.
# Evaluate genuine intermediate skeletal poses and cloth corrections, not repeated images.
clip_specs=[('Standing','s',49),('Attack','a',31),('Float','w',37),('Hit','n',19),
            ('Death','d',43),('Corpse','x',2),('Fidget','f',37)]
clips={}
for name,kind,count in clip_specs:
    source=[p['frame'] for p in pose_plan if p['kind']==kind]
    clips[name]=[source[0]+(source[-1]-source[0])*i/(count-1) for i in range(count)]
snapshots={}
for f in sorted({f for values in clips.values() for f in values}):
    whole=int(f);scene.frame_set(whole,subframe=f-whole)
    snapshots[f]=({p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy()) for p in rig.pose.bones},
                  {k.name:k.value for k in keys.key_blocks if k.name!='Basis'})
for datablock in [rig,keys]:
    datablock.animation_data.action.use_fake_user=True
    datablock.animation_data.action=None
scene.timeline_markers.clear()
clip_info=[]
start=1
for name,source_frames in clips.items():
    rig.animation_data.action=bpy.data.actions.new(name+' | bones')
    keys.animation_data.action=bpy.data.actions.new(name+' | cloth correctives')
    for frame,source in enumerate(source_frames,1):
        bone_values,key_values=snapshots[source]
        for bone_name,(loc,rot,scale) in bone_values.items():
            p=rig.pose.bones[bone_name];p.location=loc;p.rotation_quaternion=rot;p.scale=scale
            for field in ['location','rotation_quaternion','scale']:p.keyframe_insert(data_path=field,frame=frame)
        for key_name,value in key_values.items():
            k=keys.key_blocks[key_name];k.value=value;k.keyframe_insert(data_path='value',frame=frame)
    for datablock in [rig,keys]:
        action=datablock.animation_data.action
        action.use_fake_user=True
        # Dense sampled keys preserve the newly authored timing without extra overshoot.
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
        track=datablock.animation_data.nla_tracks.new();track.name=name
        strip=track.strips.new(name,start,action)
        strip.action_frame_start=1;strip.action_frame_end=len(source_frames)
        strip.extrapolation='NOTHING';strip.blend_type='REPLACE'
        datablock.animation_data.action=None
    scene.timeline_markers.new(name,frame=start)
    clip_info.append({'name':name,'timeline_start':start,'timeline_end':start+len(source_frames)-1,
                      'source_pose_frames':source_frames,'loop':name in ['Standing','Float','Corpse']})
    start+=len(source_frames)
scene.render.fps=24
scene.frame_start=1;scene.frame_end=start-1
scene['clip_usage']='Timeline markers identify clips. Bone and cloth NLA tracks have matching names and play together.'
rig['animation_clips']=json.dumps(clip_info)
(ROOT/'animations.json').write_text(json.dumps({'fps':24,'source_anchor_count':len(pose_plan),'clips':clip_info},indent=2)+'\n')
# Keep every sampled pose just above the character's ground plane.
clearance=[]
for frame in range(scene.frame_start,scene.frame_end+1):
    scene.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    low=min((evaluated.matrix_world @ Vector(c)).z for c in evaluated.bound_box)
    if low < .01:
        info=next(c for c in clip_info if c['timeline_start']<=frame<=c['timeline_end'])
        action=rig.animation_data.nla_tracks[info['name']].strips[0].action
        local=frame-info['timeline_start']+1
        local_lift=rig.data.bones['root'].matrix_local.inverted().to_3x3() @ Vector((0,0,.01-low))
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        if curve.data_path=='pose.bones["root"].location':
                            for key in curve.keyframe_points:
                                if abs(key.co.x-local)<.01:key.co.y+=local_lift[curve.array_index]
                            curve.update()
        clearance.append({'frame':frame,'lift':.01-low})
(ROOT/'review'/'ground_clearance.json').write_text(json.dumps(clearance,indent=2)+'\n')

# Inspectable references are stored as packed images in the blend, not used as textures.
references=set()
for suffix in ['sa0','sa1','sa2','sa3','sa4','ad0','wa0','dd0']:
    image=bpy.data.images.load(str(ROOT.parents[2]/'assets_dev'/'engine'/'sprites'/f'm242{suffix}.bmp'),check_existing=True)
    image.pack();image.use_fake_user=True;references.add(image)
# Save only this character scene and its dependencies; preserve other open scenes.
bpy.data.libraries.write(str(ROOT/'brown_ghost.blend'),{scene}|references,fake_user=True)
report={'bones':len(rig.data.bones),'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons),
        'corrective_shapes':len(keys.key_blocks)-1,'clips':list(clips),'weighted_vertices':sum(bool(v.groups) for v in obj.data.vertices),
        'materials':[m.name for m in obj.data.materials]}
assert report['weighted_vertices']==report['vertices']
(ROOT/'review'/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

# Set up a closer orthographic presentation of the 3D character.
scene.camera.data.ortho_scale=4.05
scene.camera.location=(0,-10,1.88)
scene.render.resolution_x=512;scene.render.resolution_y=512
scene.cycles.samples=24
scene.frame_set(1)
for angle,label in [(0,'front'),(pi/4,'three_quarter'),(pi/2,'side'),(3*pi/4,'rear_three_quarter'),(pi,'back')]:
    rig.rotation_euler.z=angle
    scene.render.filepath=str(ROOT/'review'/f'{label}.png')
    bpy.ops.render.render(write_still=True)
rig.rotation_euler.z=0
for label,clip,index in [('attack','Attack',17),('float_low','Float',0),('float_high','Float',18),
                         ('hit','Hit',4),('death','Death',30),('corpse','Corpse',0)]:
    info=next(c for c in clip_info if c['name']==clip)
    scene.frame_set(info['timeline_start']+index)
    scene.render.filepath=str(ROOT/'review'/f'{label}.png')
    bpy.ops.render.render(write_still=True)
# Animated preview captures every authored pose, with a slight quarter view.
scene.render.resolution_x=320;scene.render.resolution_y=320
rig.rotation_euler.z=pi/8
(ROOT/'review'/'frames').mkdir(exist_ok=True)
for frame in range(scene.frame_start,scene.frame_end+1):
    if frame%20==1:(ROOT/'review/status.txt').write_text(f'Rendering animation frame {frame}/{scene.frame_end}')
    scene.frame_set(frame)
    scene.render.filepath=str(ROOT/'review'/'frames'/f'{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
rig.rotation_euler.z=0
scene.frame_set(1)
scene.render.resolution_x=512;scene.render.resolution_y=512
bpy.data.libraries.write(str(ROOT/'brown_ghost.blend'),{scene}|references,fake_user=True)
