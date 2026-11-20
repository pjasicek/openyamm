"""Reduce clothing separately; preserve all head/hand vertices and their UVs at LOD0."""
import bpy,bmesh,sys,json,subprocess,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,round3_bake as B
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));C.reset();o=bpy.data.objects['Body'];protection=C.protect(o,'body');source=C.triangles(o)
def isolate(obj,keep):
 me=obj.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index not in keep],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(me);bm.free()
 mats=list(me.materials);indices=[f.material_index for f in me.polygons];me.materials.clear()
 for i in keep:me.materials.append(mats[i])
 for f,i in zip(me.polygons,indices):f.material_index=keep.index(i)
details=o.copy();details.data=o.data.copy();bpy.context.scene.collection.objects.link(details);details.name='Details';isolate(details,[1,2]);isolate(o,[0])
protected=C.triangles(details);before=C.triangles(o);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/bake_source.blend'))
C.reduce(o,7000/before,planar=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.55,island_margin=.017,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
folder=P/'work/round3/shared_textures';assert not(folder/'receipt.json').exists(),'One clothing rebake already exists'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/bake_target.blend'));B.bake(o,folder)
subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(folder)],check=True)
for i,name in [(1,'head'),(2,'hands')]:
 for kind in ['basecolor','normal','metal_rough']:shutil.copyfile(P/'textures/round3'/f'{name}_{kind}.png',folder/f'{i}_{kind}.png')
# Details never entered the cage or rebake.
for ob in bpy.data.objects:ob.select_set(ob in [o,details])
bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.name='Body'
for mi in [1,2]:
 for node in o.data.materials[mi].node_tree.nodes:
  if node.type=='TEX_IMAGE':
   key=Path(node.image.filepath).stem.split('_',1)[1];node.image=bpy.data.images.load(str(folder/f'{mi}_{key}.png'),check_existing=False);node.image.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color'
C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/body_lod0.blend'))
entries=[{'blend':'work/round3/body_lod0.blend','textures':'work/round3/shared_textures','triangles':C.triangles(o)}]
for level,targets in [(1,[1400,700,300]),(2,[1080,460,190]),(3,[400,165,120])]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/body_lod0.blend'));C.reset();original=bpy.data.objects['Body'];parts=[]
 for mi,target in enumerate(targets):
  ob=original.copy();ob.data=original.data.copy();bpy.context.scene.collection.objects.link(ob);isolate(ob,[mi]);C.reduce(ob,target/C.triangles(ob));parts.append(ob)
 bpy.data.objects.remove(original,do_unlink=True)
 for ob in bpy.data.objects:ob.select_set(ob in parts)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name='Body';C.reset();bpy.ops.file.pack_all();dest=P/f'work/round3/body_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));entries.append({'blend':str(dest.relative_to(P)),'textures':'work/round3/shared_textures','triangles':C.triangles(o)})
selection=json.loads((P/'work/round3/selection.json').read_text());selection['body']=entries;(P/'review/reduction/selection.json').write_text(json.dumps(selection,indent=2))
(P/'review/round3/reduction.json').write_text(json.dumps({'source_triangles':source,'protected_head_hands_triangles':protected,'clothing_source_triangles':before,'clothing_lod0_triangles':entries[0]['triangles']-protected,'body':entries,'rebakes':1,'head_hand_surface_reprojection':False,'body_island_gap_px':34.816,'padding_px':16,'protection':protection},indent=2));print('ROUND3 REDUCTION',entries,flush=True)
