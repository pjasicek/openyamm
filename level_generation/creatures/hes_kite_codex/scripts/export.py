"""Shared textured body and C-only skinned wing-edge strips, plus rigid bone-local tier pieces."""
import bpy,bmesh,os,sys,json,math,traceback
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]

def material(name):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0
 return m,bs

def main():
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v3.blend'));r=bpy.data.objects['Ashkite_Rig'];o=bpy.data.objects['Ashkite'];r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();me=o.data;mat,bs=material('Ashkite');nt=mat.node_tree
 def tex(filename,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/'textures'/filename));n.image.colorspace_settings.name=space;return n
 bc=tex('ashkite_basecolor_2k.png','sRGB');nt.links.new(bc.outputs['Color'],bs.inputs['Base Color'])
 nm=tex('ashkite_normal_1k.png','Non-Color');node=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nm.outputs['Color'],node.inputs['Color']);nt.links.new(node.outputs['Normal'],bs.inputs['Normal'])
 mr=tex('ashkite_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 me.materials.clear();me.materials.append(mat)
 for p in me.polygons:p.material_index=0
 # Thin edge faces of the closed membranes carry factor-only C glow; keep their existing skin weights.
 edge=o.copy();edge.data=me.copy();edge.name='Static_Edges';bpy.context.collection.objects.link(edge)
 bm=bmesh.new();bm.from_mesh(edge.data);bm.faces.ensure_lookup_table()
 remove=[f for f in bm.faces if abs(f.calc_center_median().x)<.3 or abs(f.normal.z)>.42]
 bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(edge.data);bm.free()
 glow,gb=material('Static');gb.inputs['Base Color'].default_value=(.3,.23,.4,1);gb.inputs['Emission Color'].default_value=(.68,.48,.95,1);gb.inputs['Emission Strength'].default_value=1
 edge.data.materials.clear();edge.data.materials.append(glow)
 for f in edge.data.polygons:f.material_index=0
 assert 10<len(edge.data.polygons)<3000,len(edge.data.polygons)
 # Exact mouth/tail sockets; nondeforming children follow the authored pose.
 bpy.context.view_layer.objects.active=r
 bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for name,parent,co in [('Socket_Beak','Head',(0,-.889,.59)),('Socket_Tail','Tail7',(0,.844,.385))]:
  b=r.data.edit_bones.new(name);b.head=co;b.tail=Vector(co)+Vector((0,-.03,0));b.parent=r.data.edit_bones[parent];b.use_deform=False
 bpy.ops.object.mode_set(mode='OBJECT')
 (P/'export').mkdir(exist_ok=True)
 for ob in bpy.data.objects:ob.select_set(ob in (o,r,edge))
 bpy.context.view_layer.objects.active=r
 if '--attachments-only' not in sys.argv:bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_ashkite_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 if '--attachments-only' not in sys.argv:bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_animated_v3.blend'))
 # Small rigid horn sets exported in the carrying bone's coordinates; no micro geometry.
 horn,hb=material('Bone');hb.inputs['Base Color'].default_value=(.54,.47,.34,1);hb.inputs['Roughness'].default_value=.65
 venom,vb=material('Venom');vb.inputs['Base Color'].default_value=(.19,.075,.038,1);vb.inputs['Roughness'].default_value=.46
 parts=[]
 def cone(a,b,rad,mat):
  a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=rad,radius2=.001,depth=d.length,location=(a+b)/2)
  ob=bpy.context.object;ob.rotation_euler=d.to_track_quat('Z','Y').to_euler();ob.data.materials.append(mat);return ob
 for bone in ['Front_L_Fore','Front_R_Fore','Rear_L_Fore','Rear_R_Fore','Neck1','Neck2','Head','Tail7']:
  anchor=r.data.bones[bone].head_local;objects=[]
  if '_Fore' in bone:
   for k in range(2):objects.append(cone(anchor+Vector((0,k*.035,0)),anchor+Vector((0,k*.035+.025,.12-k*.025)),.028,horn))
   kind='spurs'
  elif bone=='Tail7':
   pos=anchor.lerp(r.data.bones[bone].tail_local,.6);bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=pos);ob=bpy.context.object;ob.scale=(.035,.064,.032);ob.data.materials.append(venom);objects.append(ob)
   objects.append(cone(pos+Vector((0,.025,0)),pos+Vector((0,.115,-.025)),.025,horn));kind='barb'
  else:
   for k in range(4):
    q=anchor.lerp(r.data.bones[bone].tail_local,(k+.3)/4);q.z+=.035
    objects.append(cone(q,q+Vector(((-1)**k*.025,.06,.13 if bone!='Head' else .10)),.016,horn))
   kind='quills'
  bpy.ops.object.select_all(action='DESELECT')
  for ob in objects:ob.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=kind+'_'+bone
  bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  ob.matrix_world.identity()  # Attachment post-process applies the runtime inverse bind matrix.
  filename='hes_ashkite_'+ob.name.lower()+'.glb'
  bpy.ops.export_scene.gltf(filepath=str(P/'export'/filename),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False)
  parts.append({'model':filename,'node':bone,'tiers':['B','C'] if kind!='quills' else ['C'],'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons)})
  bpy.data.objects.remove(ob,do_unlink=True)
 (P/'export/attachments.json').write_text(json.dumps(parts,indent=2)+'\n');print('EXPORTED edge faces',len(edge.data.polygons),flush=True)
try:main()
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
