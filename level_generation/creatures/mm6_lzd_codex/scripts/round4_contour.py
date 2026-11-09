import bpy,bmesh,sys,json,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
for level in [2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/rebake/round4_lod{level}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 with bpy.data.libraries.load(str(P/'work/round4/near_runtime.blend'),link=False)as(src,dst):dst.objects=['Body']
 source=dst.objects[0];bpy.context.collection.objects.link(source)
 pieces=[]
 for part in range(29,37):
  ob=source.copy();ob.data=source.data.copy();bpy.context.collection.objects.link(ob);bm=bmesh.new();bm.from_mesh(ob.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]!=part],context='VERTS');bm.to_mesh(ob.data);bm.free()
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):ob.modifiers.remove(mod)
  m=ob.modifiers.new('Arrow bundle silhouette','DECIMATE');m.ratio=(6 if level==2 else 3)/sum(len(f.vertices)-2 for f in ob.data.polygons);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name);pieces.append(ob)
 bpy.data.objects.remove(source,do_unlink=True);bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for ob in pieces:ob.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();pv=np.array([v.value for v in body.data.attributes['piece'].data]);body.data.calc_loop_triangles();faces=np.array([tuple(f.vertices)for f in body.data.loop_triangles]);names=[g.name for g in body.vertex_groups];locked=np.zeros(len(posed),bool)
 for v in body.data.vertices:
  locked[v.index]=pv[v.index]>=201 or sum(g.weight for g in v.groups if any(k in names[g.group]for k in ['Hand','Finger','Foot','Toe']))>.3 or (pv[v.index]==200 and v.co.z<1.52)
 path=P/f'work/rebake/round4_contour{level}.npz';np.savez(path,vertices=posed,faces=faces,part='actor',level=level,camera='review/round4/camera.json',reference='r4_reference',locked=locked)
 subprocess.run(['/usr/bin/python3',str(P/'scripts/contour_silhouette_fit.py'),str(path)],check=True);out=np.load(path.with_suffix('.npy'));matrices={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()for g in body.vertex_groups if g.name in rig.pose.bones}
 for v in body.data.vertices:
  matrix=Matrix([[0]*4 for _ in range(4)])
  for g in v.groups:
   if g.group in matrices:matrix+=matrices[g.group]*g.weight
  v.co=matrix.inverted()@Vector(out[v.index])
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();path=P/f'work/round4/contour{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,f'round4_contour{level}',level,parts=('actor',),palette=('round4_shared','lzd_a'),samples=32,camera_path=P/'review/round4/camera.json')
