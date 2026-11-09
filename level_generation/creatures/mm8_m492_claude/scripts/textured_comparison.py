"""Fixed textured comparisons of the selected reduction and its preceding 10% checkpoint."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'))
low=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;rig.animation_data_create()
coords=[v.co.copy() for v in low.data.vertices];trees={}
for slot in range(3):
 faces=[f for f in low.data.polygons if f.material_index==slot]
 trees[slot]=(BVHTree.FromPolygons(coords,[list(f.vertices) for f in faces],all_triangles=True),faces)
layout=json.loads((P/'work/atlas_layout.json').read_text())
mat=bpy.data.materials.new('TexturedComparison');mat.use_nodes=True
nt=mat.node_tree;im=bpy.data.images.load(str(P/'textures/dragon_basecolor_2k.png'));node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.nodes.active=node
nt.links.new(node.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
objects=[('step05',low)]
for level in [0,1,2,3,4,6]:
 path=P/'work/anim_v1.blend' if level==0 else P/f'review/reduction/step_{level:02d}.blend'
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=['Body']
 high=dst.objects[0];sc.collection.objects.link(high);high.parent=rig
 for mod in high.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 if not high.data.uv_layers:high.data.uv_layers.new(name='UVMap')
 for f in high.data.polygons:
  slot=1 if f.material_index==3 else f.material_index;tree,faces=trees[slot]
  center=sum((high.data.vertices[v].co for v in f.vertices),Vector())/3
  point,normal,index,distance=tree.find_nearest(center);source=faces[index]
  uv=[Vector((*low.data.uv_layers.active.data[j].uv,0)) for j in source.loop_indices]
  for li,vi in zip(f.loop_indices,f.vertices):
   co=high.data.vertices[vi].co
   mapped=barycentric_transform(co,*[coords[j] for j in source.vertices],*uv)
   high.data.uv_layers.active.data[li].uv=mapped.xy
  f.material_index=slot
 objects.append((f'step{level:02d}',high))
for _,obj in objects:
 for f in obj.data.polygons:
  offset=layout['offsets'][f.material_index]
  for li in f.loop_indices:obj.data.uv_layers.active.data[li].uv.x=(offset+obj.data.uv_layers.active.data[li].uv.x*2048)/layout['width']
  f.material_index=0
 obj.data.materials.clear();obj.data.materials.append(mat)
bpy.data.objects['MouthFire'].hide_render=True
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE';sc.display.shading.light='STUDIO';sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('CompareCamera',bpy.data.cameras.new('CompareCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
out=P/'review/reduction/textured';out.mkdir(exist_ok=True)
for pose,clip,frame,target,scale,direction in [('flight','Walking',12,(0,-.02,.25),1.1,(1,-1,.5)),('head','Attack',26,(0,-.34,.32),.3,(1,-1,.12)),('corpse','Dead',0,(.1,-.02,.1),1.1,(1,-1,1.2))]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame)
 target=Vector(target);cam.location=target+Vector(direction)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 for label,obj in sorted(objects):
  for _,other in objects:other.hide_render=other!=obj
  sc.render.filepath=str(out/f'{pose}_{label}.png');bpy.ops.render.render(write_still=True)
print('TEXTURED_COMPARISON',out)
