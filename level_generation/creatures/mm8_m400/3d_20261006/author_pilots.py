import bpy,bmesh,json,math
from pathlib import Path
from collections import defaultdict
from mathutils import Vector,Matrix,Quaternion
import numpy as np

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rig_v1.blend'))
scene=bpy.context.scene;scene.render.fps=48
rig=bpy.data.objects['Lizardman_Rig'];body=bpy.data.objects['Lizardman_Body']
walk=bpy.data.actions['Meshy_Walk_Source']
walk_slot=next(t.strips[0].action_slot for t in rig.animation_data.nla_tracks if t.strips[0].action==walk)
rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)

# Average weights for exact coincident chart vertices before joining them. Their original
# per-corner UVs remain distinct, but the surface can no longer tear at an exported UV seam.
copies=defaultdict(list)
for v in body.data.vertices:copies[tuple(round(x,5) for x in v.co)].append(v)
for vertices in copies.values():
    if len(vertices)<2:continue
    weights=defaultdict(float)
    for v in vertices:
        for g in v.groups:weights[g.group]+=g.weight/len(vertices)
    weights=dict(sorted(weights.items(),key=lambda p:p[1],reverse=True)[:8]);total=sum(weights.values())
    ids=[v.index for v in vertices]
    for g in body.vertex_groups:g.remove(ids)
    for index,value in weights.items():body.vertex_groups[index].add(ids,value/total,'REPLACE')
bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
bm.to_mesh(body.data);bm.free();body.data.update()
for p in body.data.polygons:p.use_smooth=True
if body.data.has_custom_normals:body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))

def weight(vertex,name,value=1):
    for g in body.vertex_groups:g.remove([vertex])
    group=body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    group.add([vertex],value,'REPLACE')

for v in body.data.vertices:
    side='Left' if v.co.x>0 else 'Right'
    if v.co.z<12:weight(v.index,side+'Foot')
    elif 20<v.co.z<43:weight(v.index,side+'Leg')
    elif v.co.z>141:weight(v.index,'Head')

# Identify the actual four digit branches from mesh connectivity, not assumed human fingers.
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
digit_specs=[];hand_frames={}
for side in ('Left','Right'):
    wrist=rig.data.bones[side+'Hand'].head_local.copy()
    gid=body.vertex_groups[side+'Hand'].index
    hand={v.index for v in body.data.vertices if any(g.group==gid and g.weight>.45 for g in v.groups)}
    axis=(sum((body.data.vertices[i].co for i in hand),Vector())/len(hand)-wrist).normalized()
    found=None;thumb=None
    print('Hand',side,'vertices',len(hand),'wrist',list(wrist),'axis',list(axis),flush=True)
    for threshold in np.arange(3,24,.5):
        remaining={i for i in hand if (body.data.vertices[i].co-wrist).dot(axis)>threshold};components=[]
        while remaining:
            stack=[remaining.pop()];seen=set(stack)
            while stack:
                current=stack.pop()
                for e in bm.verts[current].link_edges:
                    index=e.other_vert(bm.verts[current]).index
                    if index in remaining:remaining.remove(index);seen.add(index);stack.append(index)
            if len(seen)>=8:components.append(seen)
        print('Digit cutoff',side,float(threshold),sorted([len(c) for c in components],reverse=True),flush=True)
        if thumb is None and len(components)==2:
            thumb=min(components,key=len).copy()
        if thumb is not None:
            fingers=[c-thumb for c in components if len(c-thumb)>=8]
            if len(fingers) in (3,4):
                while len(fingers)>3:
                    centers=[sum((body.data.vertices[i].co for i in c),Vector())/len(c) for c in fingers]
                    a,b=min(((a,b) for a in range(len(fingers)) for b in range(a+1,len(fingers))),key=lambda pair:(centers[pair[0]]-centers[pair[1]]).length)
                    fingers[a]|=fingers[b];del fingers[b]
                found=(float(threshold),[thumb]+fingers);break
    assert found is not None, f'{side}: four separated mesh digit branches not found'
    threshold,components=found
    components=[components[0]]+sorted(components[1:],key=lambda c:abs(sum(body.data.vertices[i].co.x for i in c)/len(c)))
    palm_normal=Vector((0,-1,0));palm_normal=(palm_normal-axis*palm_normal.dot(axis)).normalized()
    hand_frames[side]={'axis':list(axis),'normal':list(palm_normal)}
    for j,component in enumerate(components):
        rows=sorted(component,key=lambda i:(body.data.vertices[i].co-wrist).dot(axis))
        root=sum((body.data.vertices[i].co for i in rows[:max(3,len(rows)//8)]),Vector())/max(3,len(rows)//8)
        tip=sum((body.data.vertices[i].co for i in rows[-max(3,len(rows)//8):]),Vector())/max(3,len(rows)//8)
        name=side+('Thumb' if j==0 else f'Digit{j}')
        digit_specs.append({'name':name,'side':side,'root':list(root),'tip':list(tip),'indices':sorted(component),'threshold_cm':threshold})
bm.free()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:b.tail=b.head+(b.tail-b.head)*.01
for d in digit_specs:
    root,tip=Vector(d['root']),Vector(d['tip']);joint=root.lerp(tip,.62)
    b=rig.data.edit_bones.new(d['name']);b.head=root;b.tail=joint;b.parent=rig.data.edit_bones[d['side']+'Hand'];b.align_roll(Vector(hand_frames[d['side']]['normal']))
    end=rig.data.edit_bones.new(d['name']+'_Tip');end.head=joint;end.tail=tip;end.parent=b;end.use_connect=True;end.align_roll(Vector(hand_frames[d['side']]['normal']))
bpy.ops.object.mode_set(mode='OBJECT')
for d in digit_specs:
    root,tip=Vector(d['root']),Vector(d['tip']);direction=tip-root
    g1=body.vertex_groups.new(name=d['name']);g2=body.vertex_groups.new(name=d['name']+'_Tip')
    for i in d['indices']:
        amount=max(0,min(1,(body.data.vertices[i].co-root).dot(direction)/direction.length_squared))
        tip_weight=max(0,min(1,(amount-.4)/.32))
        weight(i,d['name'],1-tip_weight)
        if tip_weight:g2.add([i],tip_weight,'REPLACE')

# Keep the narrow apron and lower tunic attached to the pelvis rather than stretched between legs.
material=body.data.materials[0]
base_node=next(n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.colorspace_settings.name=='sRGB')
pixels=np.asarray(base_node.image.pixels[:],dtype=np.float32).reshape(base_node.image.size[1],base_node.image.size[0],4)
uv=body.data.uv_layers.active.data;cloth=set()
for loop in body.data.loops:
    point=body.data.vertices[loop.vertex_index].co
    if not 70<point.z<103 or abs(point.x)>27:continue
    u,v=uv[loop.index].uv;color=pixels[min(pixels.shape[0]-1,max(0,int(v*pixels.shape[0]))),min(pixels.shape[1]-1,max(0,int(u*pixels.shape[1])))][:3]
    r,g,b=color
    if (g>r*1.12 and g>b*1.15) or (r>g*1.2 and r>b*1.5):cloth.add(loop.vertex_index)
for i in cloth:weight(i,'Hips')

def activate(action,slot):
    rig.animation_data.action=action;rig.animation_data.action_slot=slot
    for t in rig.animation_data.nla_tracks:t.mute=True

def reset():
    rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()

def world_rotation(name,axis,angle):
    b=rig.pose.bones[name];m=b.matrix.copy();m=Matrix.Translation(m.translation)@Quaternion(axis,angle).to_matrix().to_4x4()@Matrix.Translation(-m.translation)@m;b.matrix=m
    bpy.context.view_layer.update()

def aim(name,end):
    b=rig.pose.bones[name];rest_axis=b.matrix.to_3x3()@Vector((0,1,0));target=(end-b.head).normalized()
    q=rest_axis.rotation_difference(target);m=b.matrix.copy();pos=m.translation.copy()
    b.matrix=Matrix.Translation(pos)@q.to_matrix().to_4x4()@Matrix.Translation(-pos)@m
    bpy.context.view_layer.update()

def arm(side,target,pole,hand_axis=None,hand_normal=None):
    upper=rig.pose.bones[side+'Arm'];lower=rig.pose.bones[side+'ForeArm'];hand=rig.pose.bones[side+'Hand']
    shoulder=upper.head.copy();a=(rig.data.bones[side+'ForeArm'].head_local-rig.data.bones[side+'Arm'].head_local).length
    b=(rig.data.bones[side+'Hand'].head_local-rig.data.bones[side+'ForeArm'].head_local).length
    delta=target-shoulder;distance=max(abs(a-b)+.1,min(a+b-.1,delta.length));direction=delta.normalized()
    elbow_axis=(pole-shoulder);elbow_axis=(elbow_axis-direction*elbow_axis.dot(direction)).normalized()
    along=(a*a-b*b+distance*distance)/(2*distance);height=math.sqrt(max(0,a*a-along*along));elbow=shoulder+direction*along+elbow_axis*height
    aim(side+'Arm',elbow);aim(side+'ForeArm',shoulder+direction*distance)
    if hand_axis is not None:
        old_axis=Vector(hand_frames[side]['axis']);old_normal=Vector(hand_frames[side]['normal'])
        def basis(y,z):
            y=y.normalized();z=(z-y*z.dot(y)).normalized();x=y.cross(z).normalized();return Matrix((x,y,z)).transposed()
        delta=basis(hand_axis,hand_normal)@basis(old_axis,old_normal).inverted()
        rotation=delta@rig.data.bones[side+'Hand'].matrix_local.to_3x3()
        matrix=rotation.to_4x4();matrix.translation=hand.head;hand.matrix=matrix;bpy.context.view_layer.update()

def standing():
    reset();world_rotation('Spine01',(1,0,0),.07);world_rotation('Head',(1,0,0),.18)
    arm('Left',Vector((35,-16,104)),Vector((30,0,114)))
    arm('Right',Vector((-35,-2,92)),Vector((-28,-6,110)))
    for d in digit_specs:
        rig.pose.bones[d['name']].rotation_mode='QUATERNION';rig.pose.bones[d['name']].rotation_quaternion=Quaternion((1,0,0),.13)
    bpy.context.view_layer.update()

def ground():
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
    minimum=min((evaluated.matrix_world@v.co).z for v in mesh.vertices);evaluated.to_mesh_clear()
    hip=rig.pose.bones['Hips'];matrix=hip.matrix.copy();matrix.translation.z-=minimum/rig.matrix_world.to_scale().z;hip.matrix=matrix
    bpy.context.view_layer.update();return minimum

def capture():
    return {b.name:([*b.location],[*b.rotation_quaternion],[*b.scale]) for b in rig.pose.bones}

def bake(name,poses):
    action=bpy.data.actions.new(name);slot=action.slots.new('OBJECT',rig.name)
    bag=action.layers.new('Production').strips.new(type='KEYFRAME').channelbag(slot,ensure=True)
    for bone in rig.pose.bones:
        for prop,index in [('location',0),('rotation_quaternion',1),('scale',2)]:
            values=[p[bone.name][index] for p in poses]
            if prop=='rotation_quaternion':
                for i in range(1,len(values)):
                    if sum(a*b for a,b in zip(values[i],values[i-1]))<0:values[i]=[-x for x in values[i]]
            for component in range(len(values[0])):
                curve=bag.fcurves.new('pose.bones['+json.dumps(bone.name)+'].'+prop,index=component)
                curve.keyframe_points.add(len(poses));curve.keyframe_points.foreach_set('co',[x for i,v in enumerate(values) for x in (i,v[component])])
                for key in curve.keyframe_points:key.interpolation='LINEAR'
    track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,action);strip.action_slot=slot;track.mute=True
    return action,slot

for b in rig.pose.bones:b.rotation_mode='QUATERNION'
clips={};samples=[]
standing();ground();pose=capture();clips['Standing']=bake('Standing',[pose]*7)
for frame in range(43):
    activate(walk,walk_slot);time=walk.frame_range[0]+frame/42*(walk.frame_range[1]-walk.frame_range[0]);scene.frame_set(int(time),subframe=time%1)
    for d in digit_specs:rig.pose.bones[d['name']].matrix_basis=Matrix.Identity(4);rig.pose.bones[d['name']+'_Tip'].matrix_basis=Matrix.Identity(4)
    ground();samples.append(capture())
samples[-1]=samples[0];clips['Walk']=bake('Walk',samples)
samples=[]
for frame in range(25):
    standing();phase=frame/24
    if frame<=6:amount=math.sin(math.pi/2*frame/6)**2
    elif frame<=12:amount=1
    else:amount=math.cos(math.pi/2*(frame-12)/12)**2
    world_rotation('Head',(1,0,0),.08*amount)
    start_rotation=rig.pose.bones['RightHand'].matrix.to_quaternion()
    target=Vector((-35,-2,92)).lerp(Vector((-9,-27,111)),amount)
    arm('Right',target,Vector((-34,-12,105)))
    def frame_basis(y,z):
        y=y.normalized();z=(z-y*z.dot(y)).normalized();return Matrix((y.cross(z).normalized(),y,z)).transposed()
    old_basis=frame_basis(Vector(hand_frames['Right']['axis']),Vector(hand_frames['Right']['normal']))
    new_basis=frame_basis(Vector((.05,.02,1)),Vector((0,1,0)))
    contact_rotation=(new_basis@old_basis.inverted()@rig.data.bones['RightHand'].matrix_local.to_3x3()).to_quaternion()
    hand=rig.pose.bones['RightHand'];hand.matrix=Matrix.LocRotScale(hand.head,start_rotation.slerp(contact_rotation,amount),Vector((1,1,1)))
    bpy.context.view_layer.update()
    for d in digit_specs:
        if d['side']=='Right':rig.pose.bones[d['name']].rotation_quaternion=Quaternion((1,0,0),.13+.45*amount)
    ground();samples.append(capture())
clips['Fidget']=bake('Fidget',samples)

review=ROOT/'pilot_review_v3';review.mkdir(exist_ok=True)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=500;scene.render.resolution_y=640
scene.render.image_settings.file_format='PNG';camera=scene.camera;camera.data.ortho_scale=1.95
for name,(action,slot) in clips.items():
    end=6 if name=='Standing' else 42 if name=='Walk' else 24
    activate(action,slot)
    for i,frame in enumerate([0] if name=='Standing' else [end*j/8 for j in range(9)]):
        scene.frame_set(int(frame),subframe=frame%1)
        for view,direction in [('front',(0,-5,0)),('profile',(-5,0,0))]:
            center=Vector((0,0,.85));camera.location=center+Vector(direction);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
            scene.render.filepath=str(review/f'{name}_{view}_{i:02d}.png');bpy.ops.render.render(write_still=True)
activate(*clips['Standing']);scene.frame_start=0;scene.frame_end=6;scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rig_pilots_v3.blend'))
(review/'rig_changes.json').write_text(json.dumps({'digits':digit_specs,'hand_frames':hand_frames,'coincident_seam_weights_averaged':True,'rigid_feet':True,'calf_ornaments_owned_by_lower_leg':True,'pelvis_cloth_vertices':len(cloth),'display_bone_length_factor':.01,'skin_joints':len(rig.data.bones),'clips':{k:len(v[0].layers[0].strips[0].channelbags[0].fcurves) for k,v in clips.items()}},indent=2))
print('Pilot rig and Standing/Walk/Fidget clips saved.',flush=True)

bpy.ops.object.select_all(action="DESELECT");body.select_set(True);rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/"pilots_v3.glb"),export_format="GLB",use_selection=True,export_animation_mode="NLA_TRACKS",export_frame_range=False,export_force_sampling=True,export_yup=True)
