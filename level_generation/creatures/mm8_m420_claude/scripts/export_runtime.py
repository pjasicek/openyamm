"""Export the fitted PirateMage and separate cobra-staff material; retain all 120Hz contact keys."""
import bpy,sys,os,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'))
scene=bpy.context.scene;scene.render.fps=30
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
hd=np.array([a.value for a in me.attributes['head'].data]);buv=me.uv_layers['UVMap'].data;huv=me.uv_layers['HeadUV'].data
for poly in me.polygons:
 if hd[poly.index]:
  for li in poly.loop_indices:buv[li].uv=huv[li].uv
# The runtime has one UV channel; discard the unused Meshy chart before joining the prop.
for layer in list(me.uv_layers):
 if layer.name != 'UVMap':me.uv_layers.remove(layer)
assert len(me.uv_layers)==1
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers.active.active_render=True
def material(name,prefix):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 def tex(suffix,space):
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures'/f'{prefix}_{suffix}.png'));t.image.colorspace_settings.name=space;return t
 base=tex('basecolor','sRGB');l.new(base.outputs['Color'],bs.inputs['Base Color']);n.active=base
 normal=n.new('ShaderNodeNormalMap');l.new(tex('normal','Non-Color').outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],bs.inputs['Normal'])
 sep=n.new('ShaderNodeSeparateColor');l.new(tex('orm','Non-Color').outputs['Color'],sep.inputs['Color']);l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 return m
me.materials.clear();me.materials.append(material('PirateMage_A','body'));me.materials.append(material('PirateMageHead_A','head'))
me.polygons.foreach_set('material_index',hd.tolist())
so=bpy.data.objects['StaffMesh'];so.data.materials.clear();so.data.materials.append(material('PirateMageStaff_A','staff'))
assert len(so.data.uv_layers)==1
so.data.uv_layers[0].name='UVMap'
for o in bpy.data.objects:o.select_set(o in (body,so))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='PirateMage'
# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 3):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 3
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
# Dense contact keys must use the same linear interpolation as the delivered glTF.
for action in bpy.data.actions:
 for curve in fcurves(action):
  for key in curve.keyframe_points:key.interpolation='LINEAR'
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget', 'Cast')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)

bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pirate_mage_textured_30fps.blend'))
# All action timelines use the same 4x time scale so Blender exports subframes without rounding them away.
for act in bpy.data.actions:
 for fc in fcurves(act):
  for key in fc.keyframe_points:
   key.co.x*=4;key.handle_left.x*=4;key.handle_right.x*=4
 act.frame_start*=4;act.frame_end*=4
scene.render.fps=120
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
scene.frame_set(0)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pirate_mage_final.blend'))
for at in list(body.data.attributes):
 if at.name in ('piece','finger','head','orig_co'):body.data.attributes.remove(at)
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
(P/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m420_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_optimize_animation_size=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
info={'triangles':sum(len(p.vertices)-2 for p in me.polygons),'clips':{a.name:[float(x)/120 for x in a.frame_range] for a in bpy.data.actions},'bones':len(rig.data.bones)}
(P/'export/export_info.json').write_text(json.dumps(info,indent=2)+'\n');print('EXPORTED',info)
