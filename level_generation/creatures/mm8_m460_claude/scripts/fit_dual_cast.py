"""Keep the selected Mixamo two-hand performance and fit only transitions, fingers, feet and robe."""
from pathlib import Path
import bpy,sys,math,json,ast,runpy
import numpy as np
from mathutils import Matrix,Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common,armik
template=p.parent/'mm6_natm_claude/scripts/retarget_mixamo.py'
code=template.read_text().replace("names = [b.name for b in rig.data.bones]", "names = [b.name for b in rig.data.bones if b.name in OFF]")
code=code.replace("['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']", "['B_R_Finger0', 'B_R_Finger01', 'B_R_Finger02']")
sys.argv=[str(template),'--',str(p/'work/pre_dual_cast.blend'),str(p/'work/cast_planted.blend'),
          str(p.parents[2]/'anim_library/mixamo/Standing 2H Magic Attack 01.fbx')+':CastForward:plant']
exec(compile(code,str(template),'exec'),{'__name__':'__main__','__file__':str(template)})
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
def attach(a):
    rig.animation_data.action=None
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    if a:
        rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def snap():return {pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
def ease(x):
    x=max(0,min(1,x));return x*x*x*(x*(6*x-15)+10)
attach(bpy.data.actions['Standing']);scene.frame_set(0);ready=snap()
source=bpy.data.actions['CastForward'];attach(source);frames=[]
for f in range(int(source.frame_range[1])+1):
    scene.frame_set(f);raw=snap();t=f/30;strength=ease(t/.35)*ease((2.7-t)/.45)
    frame={}
    for n,m in raw.items():
        if n.startswith('Robe_') or n=='Staff':m=ready[n]
        if n.startswith('B_R_Finger'):m=ready[n]
        if n in ['B_Neck','B_Head']:
            # Stabilize the gaze inside the Cleric's tall collar while retaining the source head response.
            m=ready[n].to_quaternion().slerp(m.to_quaternion(),.3).to_matrix().to_4x4()
        if n.startswith('B_L_Finger'):
            q=Quaternion().slerp(m.to_quaternion(),.25);m=q.to_matrix().to_4x4()
        q=ready[n].to_quaternion().slerp(m.to_quaternion(),strength)
        frame[n]=q.to_matrix().to_4x4();frame[n].translation=ready[n].translation.lerp(m.translation,strength)
    frames.append(frame)
assert len(frames)==82
# Preserve the performance's arm paths; compensate only the fitted wrists and carried staff clearance.
staff=bpy.data.objects['Staff'];staff_rest=rig.data.bones['Staff'].matrix_local
staff_local=np.array([tuple(staff_rest.inverted()@v.co) for v in staff.data.vertices])
corrections=[]
for f,row in enumerate(frames):
    attach(None)
    for n,m in row.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update();before={s:rig.pose.bones[f'B_{s}_Hand'].matrix.to_quaternion() for s in 'LR'}
    for iteration in range(8):
        for side in 'LR':
            pb=rig.pose.bones[f'B_{side}_Hand'];hb=rig.data.bones[pb.name];fb=rig.data.bones[f'B_{side}_Forearm']
            axis=(hb.matrix_local.to_3x3().inverted()@(hb.head_local-fb.head_local)).normalized()
            sw,tw=armik.split_swing_twist(pb.rotation_quaternion,axis);angle=sw.angle
            if angle>math.pi:sw=-sw;angle=sw.angle
            limit=math.radians(55)
            if angle>limit:pb.rotation_quaternion=Quaternion().slerp(sw,limit/angle)@Quaternion(axis,tw)
        bpy.context.view_layer.update()
        m=rig.pose.bones['Staff'].matrix;xyz=staff_local@np.array(m.to_3x3()).T+np.array(m.translation)
        if xyz[:,2].min()>=.008:break
        axis=m.to_3x3().col[2].normalized();h=m.translation.z
        zmax=min(1.,max(0.,(h-.018)/abs(float(staff_local[:,2].min()))))
        zmin=-min(1.,max(0.,(h-.018)/float(staff_local[:,2].max())))
        z=max(zmin,min(zmax,axis.z));horizontal=Vector((axis.x,axis.y,0)).normalized()
        if horizontal.length<.1:horizontal=Vector((-1,0,0))
        target=horizontal*math.sqrt(max(0,1-z*z))+Vector((0,0,z))
        hand=rig.pose.bones['B_R_Hand'];hm=hand.matrix.copy();tr=hm.translation.copy()
        hm=axis.rotation_difference(target).to_matrix().to_4x4()@hm;hm.translation=tr;hand.matrix=hm
        bpy.context.view_layer.update()
    corrections.append({s:math.degrees(before[s].rotation_difference(rig.pose.bones[f'B_{s}_Hand'].matrix.to_quaternion()).angle) for s in 'LR'})
    frames[f]=snap()
for role in ['Attack','Cast']:
    old=bpy.data.actions.get(role)
    if old:bpy.data.actions.remove(old)
    a=bpy.data.actions.new(role);a.use_fake_user=True;attach(None);rig.animation_data.action=a;previous={}
    for f,row in enumerate(frames):
        for n,m in row.items():
            pb=rig.pose.bones[n];q=m.to_quaternion()
            if n in previous and q.dot(previous[n])<0:q=-q
            previous[n]=q;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q
            pb.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis' or n=='Staff' or n.startswith('Robe_'):
                pb.location=m.translation;pb.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=81
for a in list(bpy.data.actions):
    if a.name not in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:bpy.data.actions.remove(a)
attach(None)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cast_blended.blend'))
FA=.6;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist','exec'),globals())
for role in ['Attack','Cast']:bake_twist(bpy.data.actions[role])
attach(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cast_grounded.blend'))
# The planted lower body retains its fitted standing robe and feet; no new cloth simulation is needed.
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for role in ['Attack','Cast']:
    a=bpy.data.actions[role];attach(a);rows=[]
    for f in range(82):
        scene.frame_set(f);row=snap();w=ease(f/7)*ease((81-f)/10)
        for n in row:
            if n.startswith('Robe_'):
                q=ready[n].to_quaternion().slerp(row[n].to_quaternion(),w);m=q.to_matrix().to_4x4();m.translation=ready[n].translation.lerp(row[n].translation,w);row[n]=m
        if f in [0,81]:row={n:m.copy() for n,m in ready.items()}
        rows.append(row)
    previous={}
    for f,row in enumerate(rows):
        for n,m in row.items():
            pb=rig.pose.bones[n];q=m.to_quaternion()
            if n in previous and q.dot(previous[n])<0:q=-q
            previous[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis' or n=='Staff' or n.startswith('Robe_'):
                pb.location=m.translation;pb.keyframe_insert('location',frame=f)
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
attach(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cast_fitted.blend'))
attach(bpy.data.actions['Attack']);points=[]
for f in range(82):
    scene.frame_set(f);points.append({n:list(rig.pose.bones[n].matrix.translation) for n in ['B_L_Hand','B_R_Hand','Socket_LeftPalm','Socket_Staff_Head']})
(p/'review/cast_revision/fitted_points.json').write_text(json.dumps(points,indent=2)+'\n')
(p/'review/cast_revision/wrist_fitting.json').write_text(json.dumps(corrections,indent=2)+'\n')
common.workbench_clay(scene)
for f in [0,10,20,28,34,38,45,60,81]:
    scene.frame_set(f);common.render_views(str(p/f'review/cast_revision/fitted_{f:02d}'),.92,2.6,views=('front','left','three_quarter'),resolution=(440,560))
