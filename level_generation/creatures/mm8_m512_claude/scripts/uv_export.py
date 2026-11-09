"""Freeze the selected reduced wolf, allocate extra muzzle density and retain the complete animated master."""
import bpy
import json
import sys
import hashlib
from pathlib import Path
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'claude_shared'))
from uv_head_density import scale_head_islands
selection=json.loads((PROJECT/'review/reduction/selected.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/selection['blend']))
mesh=bpy.data.objects['Wolf'];rig=bpy.data.objects['Wolf_Rig']
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
for uv in list(mesh.data.uv_layers):mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY',ngon_method='BEAUTY')
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.0015,area_weight=0.,scale_to_bounds=False)
scale_head_islands(mesh,('Head','Jaw'),factor=2.5)
bpy.ops.uv.pack_islands(margin=.0015,rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
me=mesh.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
# Smart projection folds a few concave fur faces over their neighbours; isolate only those detected faces.
for i,face in enumerate(json.loads((PROJECT/'work/uv_overlap_repair_faces.json').read_text())):
    for loop in me.loop_triangles[face].loops:uv[loop].uv.x+=1+i*.01
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=.0015,rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
me=mesh.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
u=np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles],dtype=np.float32)
xyz=np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles],dtype=np.float32)
uv_area=np.abs(np.cross(u[:,1]-u[:,0],u[:,2]-u[:,0]))*.5
geo_area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)*.5
assert np.isfinite(u).all() and u.min()>=0 and u.max()<=1
assert np.all(uv_area>1e-12) and np.all(geo_area>1e-12),'Degenerate triangles in UVs or geometry'
np.savez(PROJECT/'work/uv3d.npz',uv=u,xyz=xyz,part=np.zeros(len(u),dtype=np.int32))
report={'triangles':len(u),'vertices':len(me.vertices),'uv_area':float(uv_area.sum()),
        'density_percentiles':np.percentile(np.sqrt(uv_area/geo_area),[0,5,50,95,100]).tolist(),
        'head_density_factor':2.5,'padding_fraction':.0015,'degenerate_uv_triangles':0}
(PROJECT/'work/uv_report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/wolf_uv_master.blend'))
dup=mesh.copy();dup.data=mesh.data.copy();dup.modifiers.clear();dup.parent=None
bpy.context.scene.collection.objects.link(dup)
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
out=PROJECT/'export/wolf_neutral_upload.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,
                        export_skins=False,export_animations=False,export_materials='NONE')
print('UPLOAD',json.dumps({**report,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)
