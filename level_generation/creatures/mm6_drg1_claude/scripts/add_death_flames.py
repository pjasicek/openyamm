"""Baked flame-frame bones use existing unlit blended skinning in both consumers."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/repair_uv.blend'));rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
regions={}
for s,sign in [('L',1),('R',-1)]:
 regions[s+'Wing0']=[[(sign*x,y,z),.26,.43] for x,y,z in [(.24,-.10,.49),(.40,-.07,.64),(.56,-.02,.70)]]
 regions[s+'Wing1']=[[(sign*x,y,z),.28,.43] for x,y,z in [(.73,.01,.79),(.92,.03,.82),(1.10,.04,.82),(1.24,.02,.87)]]
regions['Spine2']=[[(x,y,z),.28,.46] for x,y,z in [(-.06,-.22,.27),(.06,-.20,.27),(0,-.12,.39),(0,-.29,.38)]]
regions['Neck2']=[[(x,y,z),.22,.37] for x,y,z in [(0,-.32,.48),(-.02,-.30,.56),(0,-.35,.62)]]
regions['Head']=[[(x,y,z),.26,.35] for x,y,z in [(0,-.43,.66),(-.05,-.32,.72),(.05,-.32,.72)]]
regions['Tail4']=[[(0,y,z),.23,.33] for y,z in [(.30,.23),(.56,.16),(.84,.11),(1.08,.075)]]
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');origins={}
for parent in regions:
 origin=rig.data.edit_bones[parent].head.copy();origins[parent]=origin[:]
 for frame in range(8):
  b=rig.data.edit_bones.new(f'Burn_{parent}_{frame}');b.head=origin;b.tail=origin+Vector((0,0,.1))
bpy.ops.object.mode_set(mode='OBJECT')
body=bpy.data.objects['Body'];trees={i:BVHTree.FromPolygons([v.co[:] for v in body.data.vertices],[list(f.vertices) for f in body.data.polygons if f.material_index==i],all_triangles=True) for i in range(3)}
verts=[];faces=[];uvs=[];weights=[]
for parent,centers in regions.items():
 for frame in range(8):
  # Eight alternating cells of the existing sixteen-frame bonfire atlas.
  tile=frame*2;col=tile%4;row=tile//4
  for ci,(c,width,height) in enumerate(centers):
   c=Vector(c);surface,normal,_,_=trees[2 if 'Wing' in parent else 1 if parent=='Head' else 0].find_nearest(c);c=surface+normal*.004
   for angle in [ci*.31,ci*.31+math.pi/2]:
    right=Vector((math.cos(angle),math.sin(angle),0))*width/2;bottom=c-Vector((0,0,height*.12));top=bottom+Vector((0,0,height));off=len(verts)
    verts.extend([bottom-right,bottom+right,top+right,top-right]);faces.extend([(off,off+1,off+2),(off,off+2,off+3)])
    uv=[((col+.015+u*.97)/4,1-(row+.015+(1-v)*.97)/4) for u,v in [(0,0),(1,0),(1,1),(0,1)]];uvs.extend([uv[:3],[uv[0],uv[2],uv[3]]]);weights.extend([(f'Burn_{parent}_{frame}',i) for i in range(off,off+4)])
me=bpy.data.meshes.new('DeathFlames');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('DeathFlames',me);bpy.context.collection.objects.link(ob);layer=me.uv_layers.new(name='UVMap')
for f,uv in zip(me.polygons,uvs):
 for li,u in zip(f.loop_indices,uv):layer.data[li].uv=u
for name,i in weights:
 g=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name);g.add([i],1.,'REPLACE')
mod=ob.modifiers.new('Rig','ARMATURE');mod.object=rig;ob.parent=rig
mat=bpy.data.materials.new('DrakeDeathFlames');mat.use_nodes=True;mat.surface_render_method='BLENDED';mat.use_backface_culling=False;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures/drg1_death_flames.png'))
nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);nt.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1;bs.inputs['Roughness'].default_value=1;me.materials.append(mat)

for pb in rig.pose.bones:
 if pb.name.startswith('Burn_'):pb.scale=(1e-6,)*3
assert len(rig.data.bones)==101 and len(faces)==896
(P/'work/death_flames.json').write_text(json.dumps({'source':'level_generation/decorations/mm6_new_sorpigal_3d/props/textures/bonfire_basecolor.png','frames':8,'regions':list(regions),'origins':origins,'triangles':len(faces)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/repair_fx.blend'))
