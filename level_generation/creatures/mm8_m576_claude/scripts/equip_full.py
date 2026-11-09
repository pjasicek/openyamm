"""Equip the solved left-hand trident and export a portable pilot viewer model."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_contacts.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
G=json.loads((P/'work/grip_pose.json').read_text());H=rig.data.bones['B_L_Hand'].matrix_local
c=H@Vector(G['handle_centre_hand_local']);axis=-(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
# Tines spread along the knuckle line's perpendicular palm tangent.
side=H.to_3x3()@Vector((0,1,0));side=(side-axis*side.dot(axis)).normalized();normal=side.cross(axis).normalized()
R=Matrix((side,axis,normal)).transposed();M=R.to_4x4();M.translation=c
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones.new('Trident');eb.head=c;eb.tail=c+axis*.15;eb.align_roll(normal);eb.parent=rig.data.edit_bones['B_L_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/trident.blend')) as (src,dst):dst.objects=['TridentMesh']
prop=dst.objects[0];bpy.context.collection.objects.link(prop);prop.data.transform(M);prop.parent=rig
prop.vertex_groups.new(name='Trident').add(list(range(len(prop.data.vertices))),1,'REPLACE');mod=prop.modifiers.new('Armature','ARMATURE');mod.object=rig
for a in list(bpy.data.actions):
    if a.name not in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):bpy.data.actions.remove(a)
sc=bpy.context.scene;sc.render.fps=30;sc.render.fps_base=1
for a in bpy.data.actions:
    for lay in a.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
for o in bpy.data.objects:o.select_set(o in (body,prop,rig))
bpy.context.view_layer.objects.active=rig
out=P/'review/viewer';out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/full_equipped.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'full.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
common.workbench_clay(sc);sc.display.shading.show_xray=False
for name,frames in [('Standing',[0]),('Walking',[8,16]),('Running',[0,5,11,16]),('Attack',[11,21,30]),('Hit',[5,10]),('Fidget',[15,30,50]),('Death',[10,35,63,90,109])]:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    for f in frames:
        sc.frame_set(f);common.render_views(str(P/f'review/full_{name}_{f:02}'),1.05,2.25,views=('front','left','three_quarter'),resolution=(450,600))
