"""Non-overlapping UVs and per-component high-to-low texture baking prevent sleeve/skin projection bleed."""
import bpy,bmesh,json,math,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/round3/reduction/rebaked';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/candidate_0.95.blend'));low=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
low.data.uv_layers.active=low.data.uv_layers['UVMap']
for uv in list(low.data.uv_layers):
 if uv.name!='UVMap':low.data.uv_layers.remove(uv)
bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,area_weight=.3,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/candidate_rebaked.blend'))
with bpy.data.libraries.load(str(p/'export/mm6_mnk1.blend'),link=False) as (a,b):b.objects=['Body']
high=b.objects[0];bpy.context.collection.objects.link(high);high.parent=None;high.modifiers.clear();source=high.data.materials[0]
lowmat=bpy.data.materials.new('Reduction bake target');lowmat.use_nodes=True
def parts(obj):
 result={};values={x.value for x in obj.data.attributes['piece'].data}
 for value in values:
  o=obj.copy();o.data=obj.data.copy();o.parent=None;o.modifiers.clear();bpy.context.collection.objects.link(o);bm=bmesh.new();bm.from_mesh(o.data);pv=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if any(v[pv]!=value for v in f.verts)],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free();o.hide_render=True;result[value]=o
 obj.hide_render=True;return result
H,L=parts(high),parts(low)
for o in L.values():
 o.data.materials.clear();o.data.materials.append(lowmat)
 for face in o.data.polygons:face.material_index=0
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1;sc.render.bake.use_selected_to_active=True;sc.render.bake.use_clear=False;sc.render.bake.cage_extrusion=.01;sc.render.bake.max_ray_distance=.025;sc.render.bake.margin=8;sc.render.bake.normal_space='TANGENT';sc.render.image_settings.file_format='PNG'
report={}
for filename,kind,space in [('mnk1_basecolor_2k.png','EMIT','sRGB'),('mnk1_region_mask.png','EMIT','Non-Color'),('mnk1_orm_1k.png','EMIT','Non-Color'),('mnk1_normal_1k.png','NORMAL','Non-Color')]:
 size=2048 if '2k' in filename else 1024;sc.render.bake.margin=4 if size==2048 else 2;im=bpy.data.images.new('Rebaked_'+filename,width=size,height=size,alpha=True);im.colorspace_settings.name=space;im.generated_color=(.5,.5,1,1) if kind=='NORMAL' else (0,0,0,1);im.filepath_raw=str(out/filename);im.file_format='PNG';node=lowmat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;lowmat.node_tree.nodes.active=node
 mat=source.copy()
 if kind=='EMIT':
  nt=mat.node_tree;nt.nodes.clear();tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'textures'/filename),check_existing=False);tex.image.colorspace_settings.name=space;em=nt.nodes.new('ShaderNodeEmission');output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],output.inputs['Surface'])
 for value in sorted(L):
  h,l=H[value],L[value];h.data.materials.clear();h.data.materials.append(mat)
  for face in h.data.polygons:face.material_index=0
  bpy.ops.object.select_all(action='DESELECT');h.hide_render=False;l.hide_render=False;h.select_set(True);l.select_set(True);bpy.context.view_layer.objects.active=l;bpy.ops.object.bake(type=kind);h.hide_render=True;l.hide_render=True
 if filename=='mnk1_region_mask.png':
  values=np.array(im.pixels[:],np.float32).reshape(-1,4);values[:,1:]=0;im.pixels.foreach_set(values.ravel())
 im.save();report[filename]={'kind':kind,'resolution':list(im.size),'pieces':len(L),'cage_m':.01,'max_ray_distance_m':.025,'uv':'smart_project, average island scale, non-overlapping pack'};print('REBAKED',filename,flush=True)
(out/'bake.json').write_text(json.dumps(report,indent=2))
