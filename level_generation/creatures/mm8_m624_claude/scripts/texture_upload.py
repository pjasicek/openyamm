import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
rig.location=(0,0,0);bpy.context.view_layer.update();me=body.data;me.calc_loop_triangles();before=len(me.loop_triangles);reference=[v.co.copy()for v in me.vertices];parts=np.array([v.value for v in me.attributes['part'].data]);fixed=set()
for v in me.vertices:
    finger=any(('Hand' in body.vertex_groups[g.group].name or any(d in body.vertex_groups[g.group].name for d in ['thumb','index','middle','ring','pinky']))and g.weight>.01 for g in v.groups)
    if finger or v.co.z>1.79 or parts[v.index]not in [0,5] or v.co.z<.35:fixed.add(v.index)
protected=[reference[i]for i in fixed]
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
body.modifiers.clear();group=body.vertex_groups.new(name='Protect');group.add(list(fixed),1,'REPLACE');mod=body.modifiers.new('SilhouetteReduction','DECIMATE');mod.ratio=.80;mod.vertex_group=group.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name);body.vertex_groups.remove(body.vertex_groups['Protect'])
me=body.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free();me.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices)for f in me.polygons],all_triangles=True);error=max(tree.find_nearest(p)[3]for p in protected);assert error<.001,error
mod=body.modifiers.new('NagaSkin','ARMATURE');mod.object=rig
body.data.materials.clear()
for n in ['Naga_A','NagaHead_A']:
    m=bpy.data.materials.new(n);m.use_nodes=True;body.data.materials.append(m)
parts=np.array([a.value for a in me.attributes['part'].data]);headparts=[3,8,9,11,13,15]
for face in me.polygons:
    z=sum(me.vertices[v].co.z for v in face.vertices)/len(face.vertices);face.material_index=1 if z>1.82 or all(parts[v]in headparts for v in face.vertices) else 0
if not me.uv_layers:me.uv_layers.new(name='UVMap')
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for face in me.polygons:face.select=face.material_index==1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008);bpy.ops.uv.pack_islands(margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob!=body:
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.to_mesh(ob.data);bm.free()
(P/'texturing').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
for label in ['body','head']:
    dup=body.copy();dup.data=me.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.collection.objects.link(dup)
    if label=='head':
        bm=bmesh.new();bm.from_mesh(dup.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==0],context='FACES');bm.to_mesh(dup.data);bm.free()
    dup.data.materials.clear();dup.data.materials.append(body.data.materials[0])
    for f in dup.data.polygons:f.material_index=0
    bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
    bpy.ops.export_scene.gltf(filepath=str(P/f'texturing/naga_{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
    bpy.data.objects.remove(dup,do_unlink=True)
(P/'work/reduction.json').write_text(json.dumps({'before_triangles':before,'selected_triangles':len(me.loop_triangles),'protected_surface_error_m':error,'protected_vertices':len(fixed),'scope':'Preserve face, all six hands, rigid jewelry and tight basal tail turn. Reduce other smooth surfaces at 0.80.'},indent=2));print('REDUCTION',before,len(me.loop_triangles),'protected error',error)
