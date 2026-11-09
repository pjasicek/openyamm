"""Eight bone-switched frames of our existing flame atlas, confined to the native mouth fire."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));rig=bpy.data.objects['Rig']
origin=Vector((0,-.395,.287));bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for i in range(8):
 b=rig.data.edit_bones.new(f'MouthFire{i}');b.head=origin;b.tail=origin+Vector((0,0,.03))
bpy.ops.object.mode_set(mode='OBJECT')
verts=[];faces=[];uvs=[];weights=[]
for i in range(8):
 tile=i*2;col=tile%4;row=tile//4
 for a in (0,math.pi/2):
  right=Vector((math.cos(a),math.sin(a),0))*.018;bottom=origin-Vector((0,0,.005));top=bottom+Vector((0,0,.085));off=len(verts)
  verts.extend([bottom-right,bottom+right,top+right,top-right]);faces.extend([(off,off+1,off+2),(off,off+2,off+3)])
  uv=[((col+.02+u*.96)/4,1-(row+.02+(1-v)*.96)/4) for u,v in [(0,0),(1,0),(1,1),(0,1)]]
  uvs.extend([uv[:3],[uv[0],uv[2],uv[3]]]);weights.extend([(f'MouthFire{i}',j) for j in range(off,off+4)])
me=bpy.data.meshes.new('MouthFire');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('MouthFire',me);bpy.context.collection.objects.link(ob);uv=me.uv_layers.new(name='UVMap')
for f,coords in zip(me.polygons,uvs):
 for li,u in zip(f.loop_indices,coords):uv.data[li].uv=u
for n,i in weights:
 g=ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n);g.add([i],1.,'REPLACE')
mod=ob.modifiers.new('Rig','ARMATURE');mod.object=rig;ob.parent=rig
mat=bpy.data.materials.new('DragonDeathFire');mat.use_nodes=True;mat.surface_render_method='BLENDED';mat.use_backface_culling=False
nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures/dragon_death_fire.png'))
nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);nt.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1;bs.inputs['Roughness'].default_value=1;me.materials.append(mat)
for pb in rig.pose.bones:
 if pb.name.startswith('MouthFire'):pb.scale=(1e-6,)*3
assert len(faces)==32
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_fx.blend'))
(P/'work/mouth_fire.json').write_text(json.dumps({'source':'level_generation/decorations/mm6_new_sorpigal_3d/props/textures/bonfire_basecolor.png','sha256':hashlib.sha256((P/'textures/dragon_death_fire.png').read_bytes()).hexdigest(),'triangles':32,'frames':8,'fps':12,'visibility_seconds':[.25,1.25],'route':'bone switched, STEP scale, unlit BLEND at export'},indent=2)+'\n')
