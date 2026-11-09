"""Native cdr1 head sweep and articulated wings, v6 softer wing fold and explicit head preparation; preserve other clips."""
import bpy
import json
import math
from pathlib import Path
import numpy as np
from mathutils import Vector, Quaternion

P = Path(__file__).resolve().parents[1]
BASE = P / 'work/before_motion_v6/export/mm6_cdr1.blend'
OUT = P / 'review/motion_v6'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
sc = bpy.context.scene
sc.render.fps = 48
axes = {n:b.matrix_local.to_3x3().inverted() for n,b in rig.data.bones.items()}
rig.animation_data.action = None
for track in rig.animation_data.nla_tracks:
    track.mute = True

# t, trunk pitch, neck bend, head nod, head turn, flap, outer bend, membrane roll, jaw, lift, foreleg reach
ATTACK = np.array([
    [0.000,-.27,-.08,-.06, .00,-.48,-.05,1.15,.03,.17, .00],
    [0.125,-.21, .16,-.06, .50,-.32, .90, .30,.28,.18,-.12],
    [0.250,-.08, .62,-.40, .30,-.25,1.30, .00,.45,.19,-.24],
    [0.375, .06,1.00,-.80, .00,-.20,1.55,-.15,.56,.19,-.30],
    [0.500,-.10, .68,-.40,-.35,-.28,1.40,-.08,.40,.19,-.20],
    [0.625,-.23, .18, .02,-.48,-.30,1.15, .20,.20,.18,-.08],
    [0.750,-.27,-.06,-.02,-.14,-.32, .30, .75,.32,.17, .00],
    [1.000,-.27,-.08,-.06, .00,-.48,-.05,1.15,.03,.17, .00],
])
FLIGHT = np.array([
    [0.000,-.27,-.08,-.06,0,-.48,-.05,1.15,.03,.17, .00],
    [0.125,-.27,-.08,-.06,0,-.05, .02, .95,.03,.20, .03],
    [0.250,-.27,-.08,-.06,0, .37, .10, .90,.03,.21, .03],
    [0.375,-.27,-.08,-.06,0, .66, .18, .90,.03,.19, .00],
    [0.500,-.27,-.08,-.06,0, .35, .13, .90,.03,.16,-.03],
    [0.625,-.27,-.08,-.06,0,-.06, .00, .95,.03,.15,-.03],
    [0.750,-.27,-.08,-.06,0,-.48,-.05,1.15,.03,.17, .00],
])

def curve(table, t, loop=False):
    """Cubic Hermite through observed poses, with continuous velocity between anchors."""
    xs=table[:,0];ys=table[:,1:];t=float(np.clip(t,xs[0],xs[-1]))
    i=min(len(xs)-2,max(0,int(np.searchsorted(xs,t,side='right')-1)))
    slopes=np.zeros_like(ys)
    slopes[1:-1]=(ys[2:]-ys[:-2])/(xs[2:]-xs[:-2])[:,None]
    if loop:
        slopes[0]=slopes[-1]=(ys[1]-ys[-2])/((xs[1]-xs[0])+(xs[-1]-xs[-2]))
    u=(t-xs[i])/(xs[i+1]-xs[i]);dt=xs[i+1]-xs[i]
    return (2*u**3-3*u**2+1)*ys[i]+(u**3-2*u**2+u)*dt*slopes[i]+(-2*u**3+3*u**2)*ys[i+1]+(u**3-u**2)*dt*slopes[i+1]

def rot(name, axis, angle):
    rig.pose.bones[name].rotation_quaternion @= Quaternion(axes[name]@Vector(axis),float(angle))

def pose(clip,t,duration):
    for b in rig.pose.bones:
        b.rotation_mode='QUATERNION';b.matrix_basis.identity()
    attack=clip in ('Attack','Cast')
    cycle=t if attack else (t/duration*(2 if clip=='Fidget' else 1))*.75
    phase=(t/duration if attack else cycle/.75)*math.tau
    values=curve(ATTACK,t) if attack else curve(FLIGHT,cycle%.75,True)
    pitch,neck,nod,yaw,flap,bend,roll,jaw,lift,reach=values
    if clip=='Fidget':
        yaw=.14*math.sin(t/duration*math.tau)
    rot('Root',(1,0,0),-.27 if attack else pitch)
    if attack:
        rot('Spine1',(1,0,0),(pitch+.27)*.5)
        rot('Spine2',(1,0,0),(pitch+.27)*.5)
    rig.pose.bones['Root'].location=axes['Root']@Vector((0,0,lift))
    # The neck carries the dip; keeping the hips up avoids a whole-body dive.
    for i in range(1,4):
        rot(f'Neck{i}',(1,0,0),neck/3)
        rot(f'Neck{i}',(0,0,1),yaw/6)
    rot('Head',(0,0,1),yaw/2)
    rot('Head',(1,0,0),nod)
    rot('Jaw',(1,0,0),jaw)
    for i in range(1,10):
        rot(f'Tail{i}',(0,0,1),(.009+.002*i)*math.sin(phase-i*.38))
        rot(f'Tail{i}',(1,0,0),.035+.006*math.sin(phase-i*.38))
    for side,sgn in [('L',1),('R',-1)]:
        rot(side+'Wing0',(0,1,0),sgn*flap)
        span=rig.data.bones[side+'Wing0'].tail_local-rig.data.bones[side+'Wing0'].head_local
        rot(side+'Wing0',span.normalized(),sgn*roll)
        # Keep the leading edge open; share the attack fold with the distal wing.
        fold=max(0.0,bend) if attack else 0.0
        rot(side+'Wing1',(0,1,0),sgn*(bend-.50*fold))
        rot(side+'Wing2',(0,1,0),sgn*(bend*.15+.15*fold))
        rot(side+'ForeUpper',(1,0,0),reach)
        rot(side+'ForeLower',(1,0,0),-.08+reach*.15)
        rot(side+'HindUpper',(1,0,0),-.10)
        rot(side+'HindLower',(1,0,0),.16)
    bpy.context.view_layer.update()

def vertices():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    result=np.array([(ev.matrix_world@v.co)[:] for v in me.vertices]);ev.to_mesh_clear();return result

def render_probes():
    sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE';sc.display.shading.light='STUDIO'
    sc.render.film_transparent=True;sc.render.resolution_x=640;sc.render.resolution_y=540;sc.render.resolution_percentage=100
    cam=bpy.data.objects.new('MotionCamera',bpy.data.cameras.new('MotionCamera'));sc.collection.objects.link(cam);sc.camera=cam
    cam.data.type='ORTHO';cam.data.ortho_scale=3.5
    rows=[]
    for clip in ['Attack']:
        for i,t in enumerate([0,.0625,.125,.1875,.25,.375,23/48,.625,.75]):
            pose(clip,t,1.0 if clip=='Attack' else .75)
            row={'clip':clip,'t':t,'min_z':float(vertices()[:,2].min()),'head':list(rig.pose.bones['Head'].head),'mouth':list(rig.pose.bones['Socket_Mouth'].head)};rows.append(row)
            for view,offset in [('front',(0,-6,0)),('right',(6,0,0)),('quarter',(4,-6,0))]:
                target=Vector((0,-.4,1.25));cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
                sc.render.filepath=str(OUT/f'probe_{clip}_{view}_{i}.png');bpy.ops.render.render(write_still=True)
    (OUT/'probe.json').write_text(json.dumps(rows,indent=2));print('PROBES',rows)

render_probes()
sc.frame_end=116

durations={'Attack':1.0,'Cast':1.0}
for name,duration in durations.items():
    old=bpy.data.actions.get(name)
    if old:bpy.data.actions.remove(old)
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    for frame in range(round(duration*48)+1):
        pose(name,frame/48,duration)
        for b in rig.pose.bones:
            b.keyframe_insert('location',frame=frame);b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('scale',frame=frame)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_v6.blend'))
for ob in bpy.data.objects:ob.select_set(ob in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/motion_v6_clips.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='NONE',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(OUT/'authored.json').write_text(json.dumps({'durations':durations,'fps':48,'impact':.75,'attack_anchors':ATTACK.tolist(),'flight_anchors':FLIGHT.tolist()},indent=2))
print('AUTHORED',durations)
