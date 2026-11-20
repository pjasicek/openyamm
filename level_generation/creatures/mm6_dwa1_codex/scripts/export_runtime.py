import bpy,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];HERE=str(P);sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
from attach_axe import build
so=build(rig)
# Head is authored at independent 1K density; the runtime packer merges it after attachment split.
hd=[a.value for a in me.attributes['head'].data];uv=me.uv_layers['UVMap'].data;huv=me.uv_layers['HeadUV'].data
for f in me.polygons:
 if hd[f.index]:
  for li in f.loop_indices:uv[li].uv=huv[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV']);me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers.active.active_render=True
def material(name,prefix):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/'textures'/f'{prefix}{suffix}_1k.png'));n.image.colorspace_settings.name=space;return n
 base=tex('basecolor','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);nt.nodes.active=base
 n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal'])
 n=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Green'],bs.inputs['Roughness']);nt.links.new(n.outputs['Blue'],bs.inputs['Metallic']);return m
body.data.materials.clear();body.data.materials.append(material('Dwarf_A','dwa1_'));body.data.materials.append(material('DwarfHead_A','dwa1_head_'))
for f in me.polygons:f.material_index=hd[f.index]
so.data.materials.clear();so.data.materials.append(material('DwarfAxe_A','axe/'))
for f in so.data.polygons:f.material_index=0
# Exact four influence contract, including interpolated vertices from the local reduction.
for v in me.vertices:
 w=sorted([(e.group,e.weight)for e in v.groups if e.weight>1e-7],key=lambda x:-x[1])[:4];total=sum(x[1]for x in w);assert total>0
 for e in v.groups[:]:body.vertex_groups[e.group].remove([v.index])
 for g,x in w:body.vertex_groups[g].add([v.index],x/total,'REPLACE')
for o in bpy.data.objects:o.select_set(o in(body,so))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Dwarf'
# Dead: the last Death frame held one second
death = bpy.data.actions['Death']
rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
bpy.context.scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for act in bpy.data.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values():
            fc.update()
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
bpy.context.scene.render.fps = 30; bpy.context.scene.render.fps_base = 1
out = os.path.join(HERE, 'export', 'mm6_dwa1_lod0.glb'); os.makedirs(os.path.dirname(out), exist_ok=True)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
# Preserve the subframe IK contacts by exporting at 120 Hz; seconds remain unchanged.
for a in bpy.data.actions:
    for fc in fcurves(a):
        for k in fc.keyframe_points:
            k.co.x *= 4; k.handle_left.x *= 4; k.handle_right.x *= 4
        fc.update()
    a.frame_end *= 4; a.frame_start *= 4
bpy.context.scene.render.fps = 120
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions})

bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_master.blend'))
