"""Freeze final local UVs, keeping 2.5x head density; export static texturing upload."""
from pathlib import Path
import sys,json
import bpy
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
mesh=bpy.data.objects['Wyvern'];rig=bpy.data.objects['Wyvern_Rig']
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for uv in list(mesh.data.uv_layers):mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
for o in bpy.data.objects:o.select_set(o==mesh)
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004,area_weight=0.,scale_to_bounds=False)
scale_head_islands(mesh,('Head','Jaw'),factor=2.5)
bpy.ops.uv.pack_islands(margin=.004,rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
me=mesh.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
U=np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles],dtype=np.float32)
X=np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles],dtype=np.float32)
areas=np.abs(np.cross(U[:,1]-U[:,0],U[:,2]-U[:,0]))*.5
assert np.isfinite(U).all() and U.min()>=-.00001 and U.max()<=1.00001
assert (areas>1e-12).all(), 'Degenerate UV triangles'
# Connected parts distinguish membrane sheets from the body and rigid details.
adj=[[] for _ in me.vertices]
for e in me.edges:
    a,b=e.vertices;adj[a].append(b);adj[b].append(a)
labels=np.full(len(adj),-1,dtype=np.int32);part=0
for start in range(len(adj)):
    if labels[start]>=0:continue
    stack=[start];labels[start]=part
    while stack:
        for n in adj[stack.pop()]:
            if labels[n]<0:labels[n]=part;stack.append(n)
    part+=1
parts=np.array([labels[t.vertices[0]] for t in me.loop_triangles])
np.savez(P/'work/uv3d.npz',uv=U,xyz=X,part=parts)
report={'triangles':len(U),'vertices':len(me.vertices),'parts':part,'uv_area':float(areas.sum()),'minimum_uv_triangle':float(areas.min()),'head_density_multiplier':2.5,'margin':.004}
(P/'review/uv_metrics.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_master.blend'))
(P/'texturing').mkdir(exist_ok=True)
dup=mesh.copy();dup.data=mesh.data.copy();dup.modifiers.clear();dup.parent=None
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:o.select_set(o==dup)
bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/wyvern_neutral.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
print('UV',report,flush=True)
