import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
# Preserve UVs and remove the remaining isolated long sliver faces, not real membranes.
bm=bmesh.new();bm.from_mesh(body.data);bad=[]
for f in bm.faces:
 c=f.calc_center_median();le=max(e.calc_length() for e in f.edges)
 if abs(c.x)<.21 and c.y<-.15 and f.material_index!=2 and le>.075 and f.calc_area()/le**2<.007:bad.append(f)
print('SECOND_BRIDGES',len(bad));bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(body.data);bm.free()
dup=body.copy();dup.data=body.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.collection.objects.link(dup);bm=bmesh.new();bm.from_mesh(dup.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(dup.data);bm.free()
bpy.context.view_layer.objects.active=dup;bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);dec=dup.modifiers.new('Charred_remnant_reduction','DECIMATE');dec.ratio=.24;bpy.ops.object.modifier_apply(modifier=dec.name)
for v in dup.data.vertices:v.co=(v.co-Vector((0,-.40,.65)))*.80
zmin=min(v.co.z for v in dup.data.vertices)
for v in dup.data.vertices:v.co.z-=zmin
mat=bpy.data.materials.new('DrakeRemains');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.012,.011,.009,1);bs.inputs['Roughness'].default_value=.98;dup.data.materials.clear();dup.data.materials.append(mat)
for f in dup.data.polygons:f.material_index=0
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('Remains');b.head=(0,0,0);b.tail=(0,0,.1);bpy.ops.object.mode_set(mode='OBJECT');vg=dup.vertex_groups.new(name='Remains');vg.add(list(range(len(dup.data.vertices))),1.,'REPLACE')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);dup.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join();rig.pose.bones['Remains'].scale=(.001,)*3
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv_remains.blend'))
