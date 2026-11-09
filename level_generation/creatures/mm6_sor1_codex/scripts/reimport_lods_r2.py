"""Reimport a packaged lower LOD, restoring nearest source part labels only for the surface gates."""
import bpy,bmesh,sys,json
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
p=Path(__file__).resolve().parents[1];level=int(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(p/'work/runtime_reimport.blend'));body=bpy.data.objects['Body'];tree=kdtree.KDTree(len(body.data.vertices));labels=[a.value for a in body.data.attributes['piece'].data]
for i,v in enumerate(body.data.vertices):tree.insert(body.matrix_world@v.co,i)
tree.balance();bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=120;bpy.ops.import_scene.gltf(filepath=str(p/f'work/round2_lod{level}_audit.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';body=bpy.data.objects['Sorcerer'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();staffids=set()
for f in body.data.polygons:
 if 'Staff' in body.data.materials[f.material_index].name:staffids.update(f.vertices)
assert staffids
body.data.transform(body.matrix_world.copy());body.matrix_world=Matrix();a=body.data.attributes.new('piece','INT','POINT');dist=[]
for v in body.data.vertices:
 if v.index in staffids:a.data[v.index].value=200
 else:
  _,i,d=tree.find(v.co);a.data[v.index].value=labels[i];dist.append(d)
body.name='Body';staff=body.copy();staff.data=body.data.copy();bpy.context.collection.objects.link(staff);staff.name='Staff'
for o,keep in [(body,False),(staff,True)]:
 bm=bmesh.new();bm.from_mesh(o.data);l=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v[l]==200)!=keep],context='VERTS');bm.to_mesh(o.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p/f'work/round2_lod{level}_audit.blend'));print('LOD_REIMPORT',level,'nearest rest-label distance mm',max(dist)*1000,flush=True)
