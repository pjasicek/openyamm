"""Reduce the weighted skin, retain facial/claw detail, and add measured FX sockets and held corpse."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
piece=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',piece)
eyes={side:np.mean([tuple(v.co) for v in me.vertices if piece[v.index]==p],axis=0) for side,p in (('Left',26),('Right',27))}
centers=list(eyes.values());eyes={'Left':max(centers,key=lambda v:v[0]),'Right':min(centers,key=lambda v:v[0])}
assert eyes['Left'][0]>0 and eyes['Right'][0]<0
names=[g.name for g in body.vertex_groups]
protect=body.vertex_groups.new(name='_protect')
for v in me.vertices:
    weight=sum(e.weight for e in v.groups if e.group<len(names) and any(t in names[e.group] for t in ('Head','Neck','Hand','Finger','Foot','Toe')))
    if piece[v.index]!=0 or weight>.3 or v.co.y>.8:protect.add([v.index],1,'REPLACE')
before=sum(len(f.vertices)-2 for f in me.polygons)
for ob in bpy.data.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body
mod=body.modifiers.new('Weighted reduction','DECIMATE');mod.ratio=10000/before
mod.vertex_group='_protect';mod.invert_vertex_group=True
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
bpy.ops.object.modifier_apply(modifier=mod.name)
body.vertex_groups.remove(body.vertex_groups['_protect'])
me=body.data;after=sum(len(f.vertices)-2 for f in me.polygons)
assert 8500<after<11000,(before,after)
max_discard=0
for v in me.vertices:
    weights=sorted([(e.group,e.weight) for e in v.groups if e.weight>0],key=lambda x:-x[1])
    kept=weights[:8];total=sum(w for _,w in kept)
    max_discard=max(max_discard,sum(w for _,w in weights[8:]))
    assert total>0
    for g in body.vertex_groups:g.remove([v.index])
    for group,w in kept:body.vertex_groups[group].add([v.index],w/total,'REPLACE')
assert max_discard<.025,max_discard
def socket(name,bone,point):
    ob=bpy.data.objects.new(name,None);sc.collection.objects.link(ob)
    ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=bone
    ob.empty_display_size=.025;ob.matrix_world=Matrix.Translation(point)
    bpy.context.view_layer.update()
    assert (ob.matrix_world.translation-Vector(point)).length<1e-5,name
    return {'node':name,'bone':bone,'rest_position':list(point)}
sockets={}
for side,label,sign in (('L','Left',-1),('R','Right',1)):
    wrist=rig.data.bones[f'B_{side}_Hand'].head_local
    middle=rig.data.bones[f'B_{side}_Finger2'].head_local
    across=rig.data.bones[f'B_{side}_Finger1'].head_local-rig.data.bones[f'B_{side}_Finger4'].head_local
    normal=(middle-wrist).cross(across).normalized()
    if normal.x*sign<0:normal=-normal
    point=wrist+(middle-wrist)*.48+normal*.022
    sockets['palm_'+label.lower()]=socket('Socket_'+label+'Palm',f'B_{side}_Hand',point)
for side,point in eyes.items():
    sockets['eye_'+side.lower()]=socket('Socket_'+side+'Eye','B_Head',point)
death=bpy.data.actions['Death'];rig.animation_data.action=death
if death.slots:rig.animation_data.action_slot=death.slots[0]
sc.frame_set(int(death.frame_range[1]))
held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones}
dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;rig.animation_data.action=dead
for f in (0,30):
    for pb in rig.pose.bones:
        pb.rotation_mode='QUATERNION';pb.rotation_quaternion,pb.location=held[pb.name]
        pb.keyframe_insert('rotation_quaternion',frame=f)
        if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
sc.render.fps=30;sc.render.fps_base=1
sys.path.insert(0,str(P/'scripts'))
from fit_hit_timing import fit_hit
fit_hit()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_final.blend'))
info={'triangles_before':before,'triangles':after,'vertices':len(me.vertices),'maximum_discarded_weight':max_discard,
      'sockets':sockets,'clips':{a.name:float(a.frame_range[1]/30) for a in bpy.data.actions if a.use_fake_user}}
(P/'work/final_rig.json').write_text(json.dumps(info,indent=2))
out=P/'review/viewer';out.mkdir(parents=True,exist_ok=True)
for ob in bpy.data.objects:ob.select_set(ob==body or ob==rig or ob.type=='EMPTY')
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(out/'gog_clay.glb'),use_selection=True,export_format='GLB',export_yup=True,
    export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
    export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,
    export_anim_slide_to_zero=True)
print('FINAL_RIG',info,flush=True)
