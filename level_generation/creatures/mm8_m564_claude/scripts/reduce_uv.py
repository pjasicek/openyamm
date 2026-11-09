"""Reduce the reviewed rig, keep the face/hooves/ridge, then unwrap with denser head islands."""
from pathlib import Path
import sys,json
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
mesh=bpy.data.objects['Gorgon'];rig=bpy.data.objects['Gorgon_Rig']
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
before=len(mesh.data.polygons)
original=[v.co.copy() for v in mesh.data.vertices]
report=[]
selected=None
for ratio in [.90,.81,.729]:
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
    mesh=bpy.data.objects['Gorgon'];rig=bpy.data.objects['Gorgon_Rig']
    rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active=mesh
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True)
    group=mesh.vertex_groups.new(name='_protect')
    for v in mesh.data.vertices:
        if v.co.y<-.27 or v.co.z<.055 or v.co.z>.37:group.add([v.index],1,'REPLACE')
    mod=mesh.modifiers.new('PlateBudget','DECIMATE');mod.ratio=ratio
    mod.vertex_group=group.name;mod.invert_vertex_group=True
    bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    tree=BVHTree.FromPolygons([v.co for v in mesh.data.vertices],[f.vertices for f in mesh.data.polygons],all_triangles=True)
    errors=np.array([tree.find_nearest(v)[3] for v in original])
    row={'ratio':ratio,'triangles':len(mesh.data.polygons),'max_surface_error_m':float(errors.max()),
         'p99_surface_error_m':float(np.quantile(errors,.99))}
    print('REDUCTION',row,flush=True);report.append(row)
    if errors.max()>.0025 or np.quantile(errors,.99)>.001:
        break
    mesh.vertex_groups.remove(mesh.vertex_groups['_protect'])
    selected=P/'work'/f'reduced_{round(ratio*1000)}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(selected))
assert selected is not None
bpy.ops.wm.open_mainfile(filepath=str(selected))
mesh=bpy.data.objects['Gorgon'];rig=bpy.data.objects['Gorgon_Rig']
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert len(mesh.data.polygons)<15000
assert all(1<=len(v.groups)<=4 for v in mesh.data.vertices)
report.append({'selected_triangles':len(mesh.data.polygons),'source_triangles':before})
(P/'work/reduction_report.json').write_text(json.dumps(report,indent=2)+'\n')
for uv in list(mesh.data.uv_layers):mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.55334,island_margin=.004,area_weight=0,scale_to_bounds=False)
scale_head_islands(mesh,('Head',),factor=2)
bpy.ops.uv.pack_islands(margin=.004,rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
me=mesh.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
u=np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles],np.float32)
xyz=np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles],np.float32)
assert u.min()>=-1e-5 and u.max()<=1.00001
np.savez(P/'work/uv3d.npz',uv=u,xyz=xyz,part=np.zeros(len(u),np.int32))
for folder in ['texturing','textures','export']:(P/folder).mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_master.blend'))
dup=mesh.copy();dup.data=mesh.data.copy();dup.modifiers.clear();dup.parent=None
bpy.context.scene.collection.objects.link(dup)
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/gorgon_neutral.glb'),use_selection=True,export_format='GLB',
                          export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
print('UV MASTER',len(me.polygons),'triangles',flush=True)
