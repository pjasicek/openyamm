"""Export the armoured Necromancer with shared body/head maps and measured casting/eye sockets."""
import bpy,bmesh,sys,os,json,math,runpy
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
HERE=str(p);T=str(p/'textures');HEAD=True
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
# Sockets are bone children so the head turn and both palm releases follow the fitted pose.
pc=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([tuple(v.co) for v in me.vertices]);sockets={}
for side,piece in [('Left',3),('Right',4)]:
 parent='B_L_Hand' if side=='Left' else 'B_R_Hand';hand=rig.data.bones[parent].head_local
 point=Vector(co[pc==piece].mean(0));point=hand.lerp(point,.50)
 sockets['Socket_Palm_'+side]=(parent,point)
for side,sign in [('Left',1),('Right',-1)]:
 point=Vector(co[np.isin(pc,[10,11])&(co[:,0]*sign>0)].mean(0));point.y-=.010
 sockets['Socket_Eye_'+side]=('B_Head',point)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,(parent,point) in sockets.items():
 b=rig.data.edit_bones.new(name);b.head=point;b.tail=point+Vector((0,-.012,0));b.parent=rig.data.edit_bones[parent];b.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT');assert len(rig.data.bones)==128,len(rig.data.bones)
# Correct winding only on confirmed closed shells.
bm=bmesh.new();bm.from_mesh(me);remaining=set(bm.faces);flipped=0
while remaining:
 stack=[next(iter(remaining))];component=set()
 while stack:
  f=stack.pop()
  if f in component:continue
  component.add(f);remaining.discard(f);stack.extend(n for e in f.edges for n in e.link_faces if n not in component)
 if all(len(e.link_faces)==2 for f in component for e in f.edges):
  vol=sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i+1].co)) for f in component for i in range(1,len(f.verts)-1))/6
  if vol< -1e-12:bmesh.ops.reverse_faces(bm,faces=list(component));flipped+=1
bm.to_mesh(me);bm.free();print('CLOSED_SHELL_WINDING',flipped)
hd=np.array([a.value for a in me.attributes['head'].data]);huv=me.uv_layers['HeadUV'].data;buv=me.uv_layers['UVMap'].data
for face in me.polygons:
 if hd[face.index]:
  for li in face.loop_indices:buv[li].uv=huv[li].uv
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers.remove(me.uv_layers['HeadUV'])
def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m



mats=[material('Necromancer_A','necromancer_basecolor_1k.png','necromancer_normal_1k.png','necromancer_metal_rough_1k.png'),material('NecromancerHead_A','necromancer_head_basecolor_1k.png','necromancer_head_normal_1k.png','necromancer_head_metal_rough_1k.png')]
me.materials.clear()
for m in mats:me.materials.append(m)
me.polygons.foreach_set('material_index',hd.tolist())
body.name=body.data.name='Necromancer'
for at in [a.name for a in body.data.attributes if a.name in ('piece','garment','garment_region','cloth_region','finger','head','orig_co')]:body.data.attributes.remove(body.data.attributes[at])
# Runtime supports eight weights; retain the fitted thumb-web blends within that contract.
for v in body.data.vertices:
    entries=sorted([(e.group,e.weight) for e in v.groups],key=lambda e:-e[1])
    keep=entries[:8];total=sum(w for _,w in keep)
    assert total>.99
    for gi,_ in entries[8:]:body.vertex_groups[gi].remove([v.index])
    for gi,w in keep:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
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
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh()
zs=[(body.matrix_world@v.co).z for v in posed.vertices]
standing_height=max(zs)-min(zs);ev.to_mesh_clear()
open(os.path.join(HERE,'work','runtime_scale.json'),'w').write(json.dumps({'standing_height_m':standing_height,'native_standing_height':192.0,'scale':192.0/standing_height},indent=2))
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm8_m472_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=True, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
info = {'glb': out, 'head_set': HEAD, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work','necromancer_master.blend'))
print('EXPORTED', json.dumps(info))
