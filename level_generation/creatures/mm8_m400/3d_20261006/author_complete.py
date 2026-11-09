import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parent
# Reuse the reviewed pilot construction and its fixed-length chain solvers.
exec((ROOT/'author_pilots.py').read_text().split("\nreview=ROOT/")[0])

def recoil(amount):
    standing()
    world_rotation('Spine02',(1,0,0),-.12*amount)
    world_rotation('Spine01',(1,0,0),-.13*amount)
    world_rotation('Head',(1,0,0),-.22*amount)
    arm('Left',Vector((29,-16+20*amount,104-5*amount)),Vector((40,4,110)))
    arm('Right',Vector((-29,-2+14*amount,92+3*amount)),Vector((-40,4,110)))
    ground()

samples=[]
for f in range(25):
    amount=float(np.interp(f,[0,6,12,18,24],[.15,.6,1,.85,.55]))
    recoil(amount);samples.append(capture())
clips['Hit']=bake('Hit',samples)

samples=[]
for f in range(37):
    if f<=6:
        recoil(float(np.interp(f,[0,6],[.15,.6])))
    else:
        standing();u=min(1,(f-6)/24);rise=min(1,(f-6)/6)
        world_rotation('Spine02',(1,0,0),-.072*(1-rise))
        world_rotation('Spine01',(1,0,0),-.078*(1-rise))
        # Native death falls backwards with raised knees, then extends on the ground.
        rotation=float(np.interp(f,[6,12,18,24,30,36],[0,-1.3,-1.65,-1.55,-math.pi/2,-math.pi/2]))
        bend=float(np.interp(f,[6,12,18,24,30,36],[0,.75,1.05,.12,0,0]))
        world_rotation('LeftUpLeg',(1,0,0),-bend)
        world_rotation('RightUpLeg',(1,0,0),-bend*.85)
        world_rotation('LeftLeg',(1,0,0),bend*1.5)
        world_rotation('RightLeg',(1,0,0),bend*1.3)
        relax=float(np.interp(f,[6,18,24,30,36],[0,0,.6,1.15,1.15]))
        world_rotation('LeftFoot',(1,0,0),relax)
        world_rotation('RightFoot',(1,0,0),relax)
        arm('Left',Vector((29,-4,101)).lerp(Vector((27,-12-8*math.sin(math.pi*u),105)).lerp(Vector((26,0,86)),u*u),rise),Vector((42,-3,120)))
        arm('Right',Vector((-29,6.4,93.8)).lerp(Vector((-27,-12-8*math.sin(math.pi*u),103)).lerp(Vector((-26,0,86)),u*u),rise),Vector((-42,-3,120)))
        world_rotation('Head',(1,0,0),-.05)
        world_rotation('Hips',(1,0,0),rotation)
        world_rotation('Hips',(0,1,0),-.1*u*u)
        hip=rig.pose.bones['Hips'];m=hip.matrix.copy();m.translation.y+=32*u;hip.matrix=m
        ground()
    samples.append(capture())
clips['Death']=bake('Death',samples)
clips['Corpse']=bake('Corpse',[samples[-1]]*7)

review=ROOT/'motion_review_v7';review.mkdir(exist_ok=True)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=440;scene.render.resolution_y=420
scene.render.image_settings.file_format='PNG';camera=scene.camera;camera.data.ortho_scale=2.05
directions={'front':(0,-5,0),'quarter':(-3.535,-3.535,0),'profile':(-5,0,0),'rear_quarter':(-3.535,3.535,0),'back':(0,5,0)}
ends={'Standing':6,'Walk':42,'Fidget':24,'Hit':24,'Death':36,'Corpse':6}
metrics={}
for name,(action,slot) in clips.items():
    activate(action,slot);end=ends[name];rows=[]
    # Evaluate every authored sample plus half-frame deformation around the full set.
    for sample in range(end*2+1):
        frame=sample/2;scene.frame_set(int(frame),subframe=frame%1)
        obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
        points=[obj.matrix_world@v.co for v in mesh.vertices]
        min_z=min(p.z for p in points);max_z=max(p.z for p in points)
        assert all(math.isfinite(x) for p in points for x in p),'Nonfinite deformed vertex'
        assert min_z>-.006,(name,frame,min_z)
        assert max_z<1.9,(name,frame,max_z)
        assert all(abs(x-1)<1e-4 for b in rig.pose.bones for x in b.scale),'Bone scale changed'
        rows.append({'frame':frame,'min_z_m':min_z,'max_z_m':max_z});obj.to_mesh_clear()
        if sample%2 or name!='Fidget':continue
        for view,direction in directions.items():
            # All native views at source anchors; every delivered sample in front/profile.
            if view not in ('front','profile') and sample%12 and frame!=end:continue
            center=Vector((0,.25,.8));camera.location=center+Vector(direction);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
            scene.render.filepath=str(review/f'{name}_{view}_{int(frame):03d}.png');bpy.ops.render.render(write_still=True)
    metrics[name]=rows
(review/'surface_checks.json').write_text(json.dumps(metrics,indent=2))
# The master retains the downloaded source as an action; export only production tracks.
for track in list(rig.animation_data.nla_tracks):
    if track.name not in clips:
        for strip in track.strips:strip.action.use_fake_user=True
        rig.animation_data.nla_tracks.remove(track)
activate(*clips['Standing']);scene.frame_start=0;scene.frame_end=6;scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'animated_master_v7.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'animated_v7.glb'),export_format='GLB',use_selection=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,export_force_sampling=True,export_yup=True,export_all_influences=True)
print('Complete six native-role clips saved and all samples checked',flush=True)
