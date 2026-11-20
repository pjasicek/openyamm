"""Bake feather coverage onto the far envelopes instead of treating empty feather gaps as solid cloth."""
import bpy,bmesh,sys,json,shutil,numpy as np,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from reduction_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_shaft125.blend'));C.reset();low=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];tex=P/'work/reduction/lod3_coverage';shutil.copytree(P/'work/reduction/lod3_shaft125',tex,dirs_exist_ok=True)
with bpy.data.libraries.load(str(P/'work/bake_source.blend'),link=False)as(src,dst):dst.objects=['Body']
high=dst.objects[0];bpy.context.collection.objects.link(high);high.parent=r
for m in high.modifiers:
 if m.type=='ARMATURE':m.object=r
pv=[x.value for x in high.data.attributes['piece'].data];bm=bmesh.new();bm.from_mesh(high.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i]for i,p in enumerate(pv)if p in [0,1,2,3,10,12,15]],context='VERTS');bm.to_mesh(high.data);bm.free()
mat=bpy.data.materials.new('Feather coverage source');mat.use_nodes=True;nt=mat.node_tree;out=nt.nodes.get('Material Output');em=nt.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1,1,1,1);nt.links.new(em.outputs[0],out.inputs[0]);high.data.materials.clear();high.data.materials.append(mat)
ims=[]
for i,m in enumerate(low.data.materials):
 im=bpy.data.images.new(f'Coverage{i}',width=1024,height=1024,alpha=False);im.colorspace_settings.name='Non-Color';n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.nodes.active=n;ims.append(im)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=1;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.025;sc.render.bake.max_ray_distance=.045;sc.render.bake.margin=1;bpy.ops.object.select_all(action='DESELECT');high.select_set(True);low.select_set(True);bpy.context.view_layer.objects.active=low;bpy.ops.object.bake(type='EMIT')
ims[0].filepath_raw=str(tex/'body/coverage.png');ims[0].file_format='PNG';ims[0].save();bpy.data.objects.remove(high,do_unlink=True)
# Raster labels keep skin, eyes and both flat loincloth panels opaque.
uv=low.data.uv_layers.active;pv=np.array([x.value for x in low.data.attributes['piece'].data]);tri=[]
for poly in low.data.polygons:
 if poly.material_index==0:tri.append({'uv':[uv.data[i].uv[:]for i in poly.loop_indices],'feather':bool(pv[poly.vertices[0]]>=1000)})
(P/'work/far_uv_faces.json').write_text(json.dumps(tri));subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/coverage_maps.py'),str(tex)],check=True)
for i,m in enumerate(low.data.materials):
 if i:continue
 bs=m.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(tex/'body/0_basecolor.png'),check_existing=False);cut=m.node_tree.nodes.new('ShaderNodeMath');cut.operation='GREATER_THAN';cut.inputs[1].default_value=.5;m.node_tree.links.new(node.outputs['Alpha'],cut.inputs[0]);m.node_tree.links.new(cut.outputs[0],bs.inputs['Alpha']);m.surface_render_method='DITHERED'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/lod3_coverage.blend'));subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True)
# Review previews preserve the newly baked opacity.
subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/coverage_maps.py'),str(tex),'previews'],check=True)
render(P/'work/lod3_coverage.blend',P/'review/reduction/lod3_coverage',tex,88)
