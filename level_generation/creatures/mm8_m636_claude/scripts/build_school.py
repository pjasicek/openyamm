"""One shared fish mesh/atlas, twelve fitted rigs, bounded coordinated swimming and native death timing."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix, Euler

P=Path(__file__).resolve().parents[1]
FPS=48
TAU=math.tau
PILOT='--pilot' in sys.argv
# x/y/z positions and lengths in metres; native front/side silhouettes establish the loose school volume.
FISH=[(-.75,-.10,1.55,.78),(-.32,.55,2.05,.62),(.42,.50,1.93,.32),(.02,.70,1.58,.24),
      (.50,-.20,1.50,.83),(-.92,.65,1.10,.30),(.05,-.05,1.00,.55),(-.68,.25,.65,.64),
      (.43,.58,.73,.80),(.88,-.25,.35,.25),(.18,-.40,.38,.80),(-.33,.35,.25,.38)]
CLIPS={'Swim':1.875,'Death':1.25,'Dead':1.0}

bpy.ops.wm.open_mainfile(filepath=str(P/'work/fish_rig.blend'))
source=bpy.data.objects['Fish']
source.parent=None
source.modifiers.clear()
old_rig=bpy.data.objects['FishRig']
for action in list(bpy.data.actions): bpy.data.actions.remove(action)
joints={b.name:(b.head_local.copy(),b.tail_local.copy(),b.parent.name if b.parent else None)
        for b in old_rig.data.bones}
bpy.data.objects.remove(old_rig,do_unlink=True)
source.name='FishSource'

mat=source.data.materials[0]
mat.name='FishMaterial'
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Metallic'].default_value=0
bs.inputs['Roughness'].default_value=.65
if not PILOT:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    def texture(filename,noncolor=False):
        n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/'textures'/filename))
        if noncolor:n.image.colorspace_settings.name='Non-Color'
        return n
    color=texture('fish_basecolor.png');links.new(color.outputs['Color'],bs.inputs['Base Color'])
    normal=texture('fish_normal.png',True);nm=nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value=.65;links.new(normal.outputs['Color'],nm.inputs['Color'])
    links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    orm=texture('fish_orm.png',True);split=nodes.new('ShaderNodeSeparateColor')
    links.new(orm.outputs['Color'],split.inputs['Color']);links.new(split.outputs['Green'],bs.inputs['Roughness'])

arm=bpy.data.armatures.new('SchoolRig');rig=bpy.data.objects.new('SchoolRig',arm)
bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
root=arm.edit_bones.new('Root');root.head=(0,0,0);root.tail=(0,.1,0)
for i,(*position,size) in enumerate(FISH):
    p=Vector(position)
    for name,(head,tail,parent) in joints.items():
        bone=arm.edit_bones.new(f'Fish{i:02d}_{name}')
        bone.head=p+head*size;bone.tail=p+tail*size
        bone.parent=arm.edit_bones[f'Fish{i:02d}_{parent}'] if parent else root
bpy.ops.object.mode_set(mode='OBJECT')

meshes=[];counts=[]
for lod,ratio in enumerate([1,.5,.25,.125]):
    template=source.copy();template.data=source.data.copy();bpy.context.collection.objects.link(template)
    if lod:
        bpy.context.view_layer.objects.active=template
        dec=template.modifiers.new('Fish LOD','DECIMATE');dec.ratio=ratio
        bpy.ops.object.modifier_apply(modifier=dec.name)
    parts=[]
    for i,(*position,size) in enumerate(FISH):
        obj=template.copy();obj.data=template.data.copy();bpy.context.collection.objects.link(obj)
        for group in obj.vertex_groups:group.name=f'Fish{i:02d}_{group.name}'
        for v in obj.data.vertices:v.co=Vector(position)+v.co*size
        obj.parent=rig;obj.modifiers.new('SchoolRig','ARMATURE').object=rig
        parts.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
    obj=bpy.context.object;obj.name='School' if lod==0 else f'School_LOD{lod}'
    corrected=obj.data.validate(verbose=True)
    print('VALIDATE',obj.name,corrected,flush=True)
    assert not obj.data.validate()
    meshes.append(obj);counts.append(sum(len(f.vertices)-2 for f in obj.data.polygons))
    bpy.data.objects.remove(template,do_unlink=True)
bpy.data.objects.remove(source,do_unlink=True)
assert counts[0]<9000 and all(a>b for a,b in zip(counts,counts[1:]))
assert len(rig.data.bones)==61
for obj in meshes:
    assert all(v.groups and abs(sum(g.weight for g in v.groups)-1)<1e-3 for v in obj.data.vertices)

sc=bpy.context.scene;sc.render.fps=FPS
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def pose(name,t):
    dying=name in ('Death','Dead')
    death=1 if name=='Dead' else smooth(t/1.25) if dying else 0
    phase=TAU*t/CLIPS['Swim'] if not dying else 0
    root=rig.pose.bones['Root'];root.rotation_mode='XYZ'
    root.rotation_euler=(0,0,(1-death)*.06*math.sin(phase))
    root.location=((1-death)*.025*math.sin(phase),0,0)
    root.scale=(1,1,1)
    bpy.context.view_layer.update()
    for i,(*position,size) in enumerate(FISH):
        p=Vector(position);lag=i*2.399963
        wave=phase+.5*p.y
        tail_phase=3*phase+lag
        amplitude=(1-death)
        displacement=Vector((.035*math.sin(wave+lag),.055*math.sin(wave),.028*math.sin(wave+lag)))
        displacement*=amplitude
        displacement.z+=death*(max(.26*size+.03,p.z-.16)-p.z)
        angles=(.045*math.sin(wave+lag)*amplitude+death*.16*math.sin(lag),
                death*((-1 if i%2 else 1)*(2.4+.35*math.sin(lag))),
                .12*math.sin(wave)*amplitude+death*.18*math.sin(lag))
        body=rig.pose.bones[f'Fish{i:02d}_Body']
        rotation=Euler(angles,'XYZ').to_matrix().to_4x4()
        transform=Matrix.Translation(p+displacement)@rotation@Matrix.Translation(-p)
        body.matrix=rig.pose.bones['Root'].matrix@transform@body.bone.matrix_local
        for name2,amount in [('Tail1',.12),('Tail2',.25)]:
            b=rig.pose.bones[f'Fish{i:02d}_{name2}'];b.rotation_mode='XYZ'
            b.rotation_euler=(0,0,amplitude*amount*math.sin(tail_phase-(.8 if name2=='Tail2' else 0))
                +death*.10*math.sin(lag))
            b.location=(0,0,0);b.scale=(1,1,1)
        for side in ['L','R']:
            b=rig.pose.bones[f'Fish{i:02d}_Fin{side}'];b.rotation_mode='XYZ'
            b.rotation_euler=(0,amplitude*.16*math.sin(2*phase+lag)+(death*.08),0)
            b.location=(0,0,0);b.scale=(1,1,1)

for name,seconds in CLIPS.items():
    rig.animation_data_create();action=bpy.data.actions.new(name);rig.animation_data.action=action
    for f in range(round(seconds*FPS)+1):
        sc.frame_set(f);pose(name,f/FPS)
        for b in rig.pose.bones:
            b.keyframe_insert('location',frame=f)
            b.keyframe_insert('rotation_euler' if b.rotation_mode!='QUATERNION' else 'rotation_quaternion',frame=f)
            b.keyframe_insert('scale',frame=f)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    action.use_fake_user=True
rig.animation_data.action=bpy.data.actions['Swim'];sc.frame_set(0)
for obj in meshes:obj.hide_render='_LOD' in obj.name;obj.hide_viewport='_LOD' in obj.name
bpy.ops.file.pack_all()
master='m636_pilot.blend' if PILOT else 'm636_master.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export'/master))
for obj in meshes:obj.hide_viewport=False
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes+[rig]:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m636_raw.glb'),use_selection=True,
    export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
    export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,
    export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'export/export_info.json').write_text(json.dumps({'fish_count':len(FISH),'formation':FISH,'triangles':counts,
    'bones':61,'influences':max(len(v.groups) for obj in meshes for v in obj.data.vertices),'clips':CLIPS,'scale':100,'pilot':PILOT},indent=2)+'\n')
print('SCHOOL',counts,CLIPS,flush=True)
