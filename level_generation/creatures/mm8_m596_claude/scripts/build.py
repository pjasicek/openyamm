"""Build the Crystal Walker's measured rigid crystal segments, rig, native-inspired clips and review renders."""
from pathlib import Path
import json
import math
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector, Euler

P = Path(__file__).resolve().parents[1]
FPS = 24
BONES = {
    'Root': ((0, 0, 0), None),
    'Hips': ((0, .04, .98), 'Root'),
    'Waist': ((0, .02, 1.13), 'Hips'),
    'Chest': ((0, .01, 1.32), 'Waist'),
    'Neck': ((0, .00, 1.51), 'Chest'),
    'Head': ((0, -.08, 1.62), 'Neck'),
}
for side, sign in [('Left', 1), ('Right', -1)]:
    BONES.update({
        side+'Arm': ((sign*.255, .015, 1.48), 'Chest'),
        side+'ForeArm': ((sign*.42, .045, 1.16), side+'Arm'),
        side+'Hand': ((sign*.60, -.11, .86), side+'ForeArm'),
        side+'Thigh': ((sign*.12, .04, .98), 'Hips'),
        side+'Shin': ((sign*.235, -.04, .49), side+'Thigh'),
        side+'Foot': ((sign*.27, .07, .155), side+'Shin'),
    })
CLIPS = {'Standing': 1.5, 'Walking': 1.0, 'Running': .75, 'Attack': 1.5,
         'Cast': 1.5, 'Hit': 19/24, 'Fidget': 15/24, 'Death': 1.0, 'Dead': 1.0}


def crystal_mesh(level):
    vertices, faces, owners = [], [], []
    sides = [8, 6, 4][level]

    def loft(name, points, radii, n=None):
        n = n or sides
        start = len(vertices)
        points = [Vector(p) for p in points]
        axis = (points[-1]-points[0]).normalized()
        if name.endswith('Foot'):
            axis=Vector((0,0,1))
        u = axis.cross(Vector((0, 1, 0)))
        if u.length < .1:
            u = axis.cross(Vector((1, 0, 0)))
        u.normalize()
        v = axis.cross(u).normalized()
        for j, (point, radius) in enumerate(zip(points, radii)):
            for i in range(n):
                angle = 2*math.pi*i/n + (0.12 if j % 2 else 0)
                variation=1+.10*math.sin(i*2.17+j*1.31) if n>4 else 1
                vertices.append(tuple(point + u*(math.cos(angle)*radius[0]*variation)
                                      + v*(math.sin(angle)*radius[1]*variation)))
                owners.append(name)
        for j in range(len(points)-1):
            for i in range(n):
                a = start+j*n+i
                b = start+j*n+(i+1)%n
                c = b+n
                d = a+n
                if (Vector(vertices[a])-Vector(vertices[c])).length < (Vector(vertices[b])-Vector(vertices[d])).length:
                    faces.extend([(a,b,c),(a,c,d)])
                else:
                    faces.extend([(a,b,d),(b,c,d)])
        # Alternate ears avoid a high-valence fan on either closed end.
        for ring in [list(range(start,start+n)),list(range(start+(len(points)-1)*n,len(vertices)))]:
            while len(ring)>2:
                faces.append((ring[-1],ring[0],ring[1]));ring.pop(0)
                if len(ring)>2:
                    faces.append((ring[0],ring[-2],ring[-1]));ring.pop()

    loft('Hips', [(0,.045,.91),(0,.04,1.02),(0,.03,1.12)], [(.11,.09),(.19,.12),(.12,.10)])
    loft('Waist', [(0,.025,1.04),(0,.02,1.17),(0,.015,1.34)], [(.11,.09),(.10,.085),(.11,.08)])
    loft('Chest', [(0,.015,1.18),(0,-.01,1.40),(0,-.025,1.50)], [(.12,.09),(.25,.13),(.21,.10)])
    loft('Neck', [(0,.00,1.45),(0,-.04,1.58),(0,-.08,1.65)], [(.07,.07),(.06,.07),(.085,.075)])
    # Wedge face projects forward; crown roots follow the skull, not the neck.
    loft('Head', [(0,-.07,1.57),(0,-.10,1.67),(0,-.07,1.75)], [(.055,.08),(.135,.18),(.09,.10)])
    loft('Head', [(0,-.15,1.68),(0,-.245,1.65),(0,-.27,1.62)], [(.10,.075),(.055,.04),(.004,.004)], 4)
    for i, angle in enumerate([-105,-75,-45,-15,15,45,75,105]):
        a=math.radians(angle)
        root=Vector((math.sin(a)*.09,.005,1.69+math.cos(a)*.075))
        tip=Vector((math.sin(a)*.22,.09+math.cos(a)*.12,1.69+math.cos(a)*.205))
        loft('Head',[root,root.lerp(tip,.38),tip],[(.035,.035),(.038,.03),(.002,.002)],4)
    for side, sign in [('Left',1),('Right',-1)]:
        arm=Vector(BONES[side+'Arm'][0]); elbow=Vector(BONES[side+'ForeArm'][0]); wrist=Vector(BONES[side+'Hand'][0])
        loft(side+'Arm',[arm.lerp(elbow,-.08),arm.lerp(elbow,.28),elbow.lerp(arm,.02)],[(.10,.085),(.09,.07),(.045,.045)])
        loft(side+'Arm',[arm+Vector((0,.01,-.04)),arm+Vector((sign*.05,.02,.11))],[(.075,.07),(.002,.002)],4)
        loft(side+'ForeArm',[elbow.lerp(wrist,-.06),elbow.lerp(wrist,.36),wrist.lerp(elbow,-.02)],[(.055,.05),(.070,.055),(.035,.035)])
        palm=wrist+Vector((sign*.035,-.02,-.06))
        loft(side+'Hand',[wrist+Vector((0,0,.025)),palm,palm+Vector((sign*.015,-.01,-.035))],[(.04,.04),(.09,.045),(.08,.04)])
        # Three rigid, curved talons: two long outer fingers and an opposed inner hook.
        for j, offset in enumerate([-.085,.005,.085]):
            base=palm+Vector((sign*offset,-.015,-.01))
            direction=-1 if j==0 else 1
            length=.19 if j==0 else .25
            points=[base,base+Vector((sign*direction*.055,-.035,-.065)),
                    base+Vector((sign*direction*.055,-.065,-length*.70)),
                    base+Vector((-sign*direction*.012,-.10,-length))]
            if level==2: points.pop(1)
            radii=[(.035,.032),(.032,.028),(.020,.018),(.0015,.0015)]
            if level==2:radii.pop(1)
            loft(side+'Hand',points,radii,6 if level==0 else 4)
        hip=Vector(BONES[side+'Thigh'][0]);knee=Vector(BONES[side+'Shin'][0]);ankle=Vector(BONES[side+'Foot'][0])
        loft(side+'Thigh',[hip+Vector((0,0,.045)),hip.lerp(knee,.27),knee.lerp(hip,-.035)],[(.10,.09),(.10,.075),(.045,.045)])
        loft(side+'Shin',[knee.lerp(ankle,-.05),knee.lerp(ankle,.50),ankle+Vector((0,0,-.025))],[(.055,.05),(.045,.045),(.075,.075)])
        loft(side+'Foot',[(sign*.27,-.035,.012),(sign*.27,-.015,.095),ankle+Vector((0,0,.035))],[(.15,.19),(.115,.13),(.07,.07)])
    mesh=bpy.data.meshes.new('CrystalWalker'+('_LOD'+str(level) if level else ''))
    mesh.from_pydata(vertices,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    uv=mesh.uv_layers.new(name='UVMap')
    for i, poly in enumerate(mesh.polygons):
        assert len({owners[v] for v in poly.vertices})==1, 'Facet crosses a joint'
        poly.use_smooth=False
        points=[mesh.vertices[v].co for v in poly.vertices]
        u=(points[1]-points[0]).normalized();v=poly.normal.cross(u)
        coords=np.array([[(point-points[0]).dot(u),(point-points[0]).dot(v)] for point in points])
        coords-=coords.min(axis=0)
        assert coords.max()*350<240, 'Face exceeds its atlas tile'
        tile=(i*23+7)%64
        for loop,co in zip(poly.loop_indices,coords):
            uv.data[loop].uv=((tile%8*256+8+co[0]*350)/2048,(tile//8*256+8+co[1]*350)/2048)
    return mesh, owners


def material():
    mat=bpy.data.materials.new('AmethystCrystal');mat.use_nodes=True;mat.use_backface_culling=True
    nodes=mat.node_tree.nodes;bsdf=nodes.get('Principled BSDF')
    image=bpy.data.images.load(str(P/'textures/crystal_basecolor.png'))
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value=.32;bsdf.inputs['Metallic'].default_value=0
    mat['openyamm_specular']=.6;mat['openyamm_edge_darkening']=.25
    return mat


def ease(x):
    x=max(0,min(1,x));return x*x*(3-2*x)


def curve(t,keys):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b:return x+(y-x)*ease((t-a)/(b-a))
    return keys[-1][1]


def posing(clip,t):
    angles={};trans=Vector((0,0,0))
    def rot(name,x=0,y=0,z=0):angles[name]=(x,y,z)
    if clip in ('Standing','Walking','Running','Fidget'):
        phase=t/(CLIPS[clip])*math.tau
        rot('Chest',0,math.sin(phase)*.8,math.sin(phase)*1)
        if clip in ('Walking','Running'):
            trans.z=-.055+.012*(1-math.cos(phase*2))
            for side,shift in [('Left',0),('Right',math.pi)]:
                swing=math.sin(phase+shift)
                rot(side+'Thigh',swing*22)
                rot(side+'Shin',-max(0,-swing)*28)
                rot(side+'Foot',-swing*22+max(0,-swing)*28)
                rot(side+'Arm',-swing*11,0,0)
                rot(side+'ForeArm',-max(0,swing)*9)
            rot('Hips',0,math.sin(phase)*2,math.sin(phase)*3)
        if clip=='Fidget':
            rot('Head',0,0,math.sin(phase)*18)
            rot('LeftHand',math.sin(phase)*8,0,math.sin(phase)*7)
            rot('RightHand',-math.sin(phase)*8,0,-math.sin(phase)*7)
    if clip in ('Attack','Cast'):
        wind=curve(t,[(0,0),(.30,1),(.72,1),(.94,0),(1.5,0)])
        slash=curve(t,[(0,0),(.76,0),(1.0,1),(1.15,.65),(1.5,0)])
        rot('RightArm',-wind*150+slash*35,-wind*20,wind*12)
        rot('RightForeArm',-wind*35-slash*15)
        rot('RightHand',-wind*12+slash*20,0,-wind*12)
        rot('Chest',-wind*8+slash*24,0,wind*12-slash*18)
        rot('Neck',wind*5-slash*10)
        rot('LeftArm',-wind*15+slash*15,0,-wind*12)
        rot('LeftForeArm',-wind*18)
        trans.z=-slash*.035
        if clip=='Cast':
            rot('LeftArm',-wind*110+slash*20,wind*10,-wind*12)
            rot('LeftForeArm',-wind*25)
    if clip=='Hit':
        amount=curve(t,[(0,0),(.15,1),(.33,.7),(CLIPS[clip],0)])
        rot('Chest',-amount*16,0,-amount*8);rot('Head',-amount*12)
        rot('LeftArm',-amount*25);rot('RightArm',-amount*25)
    if clip in ('Death','Dead'):
        t=1 if clip=='Dead' else t
        fall=curve(t,[(0,0),(.15,.08),(.43,.75),(.70,1),(1,1)])
        rot('Hips',-fall*91)
        rot('Chest',fall*8)
        rot('Neck',fall*8)
        for side,sign in [('Left',1),('Right',-1)]:
            rot(side+'Arm',-fall*20,sign*fall*65,0)
            rot(side+'ForeArm',-fall*14)
            rot(side+'Thigh',fall*30,sign*fall*10,0)
            rot(side+'Shin',-fall*55)
            rot(side+'Foot',fall*20)
        trans.y=fall*.22;trans.z=-fall*.80
    deltas={};world={}
    for name,(head,parent) in BONES.items():
        h=Vector(head);parent_delta=deltas.get(parent,Matrix.Identity(4))
        rotation=Euler(tuple(math.radians(v) for v in angles.get(name,(0,0,0))),'XYZ').to_matrix().to_4x4()
        delta=parent_delta@Matrix.Translation(h)@rotation@Matrix.Translation(-h)
        if name=='Root':delta=Matrix.Translation(trans)
        deltas[name]=delta;world[name]=delta@REST[name]
    if clip in ('Walking','Running'):
        stride,duty,lift=(.90,.62,.13) if clip=='Walking' else (1.30,.48,.22)
        for side,shift in [('Left',0),('Right',.5)]:
            phase=(t/CLIPS[clip]+shift)%1
            hip=Vector(BONES[side+'Thigh'][0]);knee=Vector(BONES[side+'Shin'][0]);ankle=Vector(BONES[side+'Foot'][0])
            hip_new=deltas['Hips']@hip
            if phase<duty:
                travel=(phase-duty/2)*stride;height=0
            else:
                swing=(phase-duty)/(1-duty)
                h00=2*swing**3-3*swing**2+1;h10=swing**3-2*swing**2+swing
                h01=-2*swing**3+3*swing**2;h11=swing**3-swing**2
                travel=(h00-h01)*duty*stride/2+(h10+h11)*stride*(1-duty)
                height=math.sin(swing*math.pi)**2*lift
            ankle_new=ankle+Vector((0,travel,height))
            axis=ankle_new-hip_new;distance=axis.length;axis.normalize()
            a=(knee-hip).length;b=(ankle-knee).length
            assert distance<a+b, f'{clip}: unreachable foot'
            along=(a*a-b*b+distance*distance)/(2*distance)
            pole=Vector((0,-1,0));pole=(pole-axis*pole.dot(axis)).normalized()
            knee_new=hip_new+axis*along+pole*math.sqrt(max(0,a*a-along*along))
            for name,start,end,new_start,new_end in [
                (side+'Thigh',hip,knee,hip_new,knee_new),
                (side+'Shin',knee,ankle,knee_new,ankle_new)]:
                turn=(end-start).rotation_difference(new_end-new_start).to_matrix().to_4x4()
                deltas[name]=Matrix.Translation(new_start)@turn@Matrix.Translation(-start)
                world[name]=deltas[name]@REST[name]
            name=side+'Foot';deltas[name]=Matrix.Translation(ankle_new-ankle)
            world[name]=deltas[name]@REST[name]
    if clip in ('Death','Dead') and fall>.5:
        amount=ease((fall-.5)*2)
        floor=min((deltas[owner]@Vector(vertex)).z for vertex,owner in zip(REST_VERTICES,OWNERS)
                  if not owner.endswith(('Arm','Hand')))
        for side,sign in [('Left',1),('Right',-1)]:
            shoulder=Vector(BONES[side+'Arm'][0]);elbow=Vector(BONES[side+'ForeArm'][0]);wrist=Vector(BONES[side+'Hand'][0])
            shoulder_new=deltas['Chest']@shoulder
            wrist_current=deltas[side+'Hand']@wrist
            wrist_goal=Vector((shoulder_new.x+sign*.61,shoulder_new.y-.18,floor+.11))
            wrist_new=wrist_current.lerp(wrist_goal,amount)
            axis=wrist_new-shoulder_new;distance=axis.length;axis.normalize()
            a=(elbow-shoulder).length;b=(wrist-elbow).length
            along=(a*a-b*b+distance*distance)/(2*distance)
            pole=Vector((0,-1,0));pole=(pole-axis*pole.dot(axis)).normalized()
            elbow_new=shoulder_new+axis*along+pole*math.sqrt(max(0,a*a-along*along))
            hand_rotation=deltas[side+'Hand'].to_quaternion().slerp(Euler((math.pi/2,0,0)).to_quaternion(),amount)
            for name,start,end,new_start,new_end in [
                (side+'Arm',shoulder,elbow,shoulder_new,elbow_new),
                (side+'ForeArm',elbow,wrist,elbow_new,wrist_new)]:
                turn=(end-start).rotation_difference(new_end-new_start).to_matrix().to_4x4()
                deltas[name]=Matrix.Translation(new_start)@turn@Matrix.Translation(-start)
                world[name]=deltas[name]@REST[name]
            name=side+'Hand'
            deltas[name]=Matrix.Translation(wrist_new)@hand_rotation.to_matrix().to_4x4()@Matrix.Translation(-wrist)
            world[name]=deltas[name]@REST[name]
    # Ground with the real rigid mesh; no crystal part ever scales or deforms.
    minimum=min((deltas[owner]@Vector(vertex)).z for vertex,owner in zip(REST_VERTICES,OWNERS))
    lift=-minimum
    for name in world: world[name]=Matrix.Translation((0,0,lift))@world[name]
    for name,(_,parent) in BONES.items():
        rest_relative=REST[parent].inverted()@REST[name] if parent else REST[name]
        pose_relative=world[parent].inverted()@world[name] if parent else world[name]
        rig.pose.bones[name].matrix_basis=rest_relative.inverted()@pose_relative
    bpy.context.view_layer.update()


def render_reviews():
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.view_settings.view_transform='Standard'
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.24,.29,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    for name,loc,power,size in [('Key',(-3,-4,6),350,4),('Fill',(4,-2,3),170,4),('Rim',(1,4,5),300,3)]:
        light=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));scene.collection.objects.link(light)
        light.location=loc;light.data.energy=power;light.data.shape='DISK';light.data.size=size
        light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));scene.collection.objects.link(cam)
    scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.4
    for name,loc in [('front',(0,-8,1.1)),('quarter',(4,-7,2)),('side',(8,0,1.1)),('back',(0,8,1.1))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,.99))-cam.location).to_track_quat('-Z','Y').to_euler()
        rig.animation_data.action=bpy.data.actions['Standing'];scene.frame_set(1)
        scene.render.filepath=str(P/'review'/('model_'+name+'.png'));bpy.ops.render.render(write_still=True)
    cam.location=(4,-7,2);cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler()
    for clip,times in [('Walking',[0,.25,.5,.75]),('Attack',[0,.35,.75,1,1.3]),('Hit',[.15]),('Death',[.2,.45,.7,1]),('Dead',[0])]:
        cam.data.ortho_scale=3.2 if clip=='Attack' else 2.4
        rig.animation_data.action=bpy.data.actions[clip]
        for t in times:
            scene.frame_set(1+int(t*FPS));scene.render.filepath=str(P/'review'/f'{clip}_{t:.2f}.png')
            bpy.ops.render.render(write_still=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.fps=FPS
data=bpy.data.armatures.new('CrystalRig');rig=bpy.data.objects.new('CrystalRig',data);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,(head,parent) in BONES.items():
    bone=data.edit_bones.new(name);bone.head=head;bone.tail=Vector(head)+Vector((0,0,.08))
    if parent:bone.parent=data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');mat=material();objects=[]
for level in range(3):
    mesh,owners=crystal_mesh(level);obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj)
    mesh.materials.append(mat);obj.parent=rig
    for name in BONES:
        indices=[i for i,bone in enumerate(owners) if bone==name]
        if indices:obj.vertex_groups.new(name=name).add(indices,1,'REPLACE')
    mod=obj.modifiers.new('RigidParts','ARMATURE');mod.object=rig
    objects.append(obj);obj.hide_render=level>0;obj.hide_set(level>0)
    if level==0:
        REST_VERTICES=[tuple(v.co) for v in mesh.vertices];OWNERS=owners
REST={b.name:b.matrix_local.copy() for b in data.bones}
for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
rig.animation_data_create();report={}
for clip,duration in CLIPS.items():
    action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data.action=action
    frames=round(duration*FPS)
    previous={}
    for frame in range(frames+1):
        scene.frame_set(frame+1);posing(clip,frame/FPS)
        for bone in rig.pose.bones:
            if bone.name in previous and previous[bone.name].dot(bone.rotation_quaternion)<0:
                bone.rotation_quaternion.negate()
            previous[bone.name]=bone.rotation_quaternion.copy()
            bone.keyframe_insert('location',frame=frame+1,group=bone.name)
            bone.keyframe_insert('rotation_quaternion',frame=frame+1,group=bone.name)
            bone.keyframe_insert('scale',frame=frame+1,group=bone.name)
            assert max(abs(v-1) for v in bone.scale)<1e-5, f'{clip}: nonrigid scale on {bone.name}'
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fcurve in bag.fcurves:
                    for key in fcurve.keyframe_points:key.interpolation='LINEAR'
    report[clip]={'duration':frames/FPS,'frames':frames+1}
rig.animation_data.action=bpy.data.actions['Standing'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/crystal_walker.blend'))
for obj in bpy.data.objects:obj.select_set(obj==rig or obj==objects[0])
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m596_lod0.glb'),use_selection=True,export_format='GLB',
    export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
    export_skins=True,export_all_influences=False,export_attributes=False,export_extras=True,
    export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'work/build_report.json').write_text(json.dumps({'clips':report,'triangles':[len(o.data.polygons) for o in objects],
    'bones':len(data.bones),'rigid_vertex_influences':1,'texels_per_metre':350},indent=2)+'\n')
print('BUILD',report,[len(o.data.polygons) for o in objects],flush=True)
render_reviews()
