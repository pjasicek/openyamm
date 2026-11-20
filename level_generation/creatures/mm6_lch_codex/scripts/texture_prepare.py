import bpy,bmesh,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['transfer_uv.py','--',str(P/'work/rig_uv.blend'),str(P/'meshy/body_retexture_v1'),str(P/'work/rig_textured.blend')]
runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer,label in [('UVMap','body'),('HeadUV','head')]:
 sys.argv=['uv_raster.py','--',str(P/'work/rig_textured.blend'),layer,'1024']
 runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
 rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 body=bpy.data.objects['Body'];low=body.copy();low.data=body.data.copy();bpy.context.collection.objects.link(low);low.name='Bake'
 for ob,keep in [(low,label=='head'),(body,label!='head')]:
  bm=bmesh.new();bm.from_mesh(ob.data);hl=bm.faces.layers.int['head']
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[hl])!=keep],context='FACES');bm.to_mesh(ob.data);bm.free()
 low.data.uv_layers.active=low.data.uv_layers[layer];low.data.uv_layers.active.active_render=True
 sys.argv=['bake_creature_ao.py','--','Bake',str(P/f'work/ao_{label}.png'),'0.03','1024']
 runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
 # Bake the full-density shape onto the reduced weighted surface; texture detail is combined separately.
 with bpy.data.libraries.load(str(P/'work/rig_clips.blend'),link=False) as (src,dst):dst.objects=['Body']
 high=dst.objects[0];bpy.context.collection.objects.link(high);high.parent=None
 for mod in list(high.modifiers):high.modifiers.remove(mod)
 bm=bmesh.new();bm.from_mesh(high.data);piece=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[piece]==13],context='VERTS');bm.to_mesh(high.data);bm.free()
 for poly in high.data.polygons:poly.use_smooth=True
 body.hide_render=True
 sc=bpy.context.scene;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.005;sc.render.bake.max_ray_distance=.02
 img=bpy.data.images.new('shape_normal',1024,1024,alpha=False);img.colorspace_settings.name='Non-Color'
 mat=low.data.materials[0];node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node
 for ob in bpy.data.objects:ob.select_set(ob in (low,high))
 bpy.context.view_layer.objects.active=low;bpy.ops.object.bake(type='NORMAL')
 img.filepath_raw=str(P/f'work/shape_normal_{label}.png');img.file_format='PNG';img.save()
 print('BAKES',label)
