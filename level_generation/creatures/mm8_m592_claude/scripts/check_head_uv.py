from pathlib import Path
import bpy,sys,json,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'));body=bpy.data.objects['Body'];me=body.data;uv=me.uv_layers['HeadUV'];hd=me.attributes['head'];areas=[]
for f in me.polygons:
 if not hd.data[f.index].value:continue
 a,b,c=[uv.data[i].uv.copy() for i in f.loop_indices];areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5)
report={'head_triangles':len(areas),'summed_head_uv_area':sum(areas),'zero_uv_triangles':sum(x<1e-12 for x in areas)};print('HEAD_UV_PACK',report,flush=True);assert .35<sum(areas)<1 and report['zero_uv_triangles']==0
im=bpy.data.images.new('Head UV checker',1024,1024);im.generated_type='COLOR_GRID';mat=bpy.data.materials.new('UV checker');mat.use_nodes=True;nt=mat.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=im;nt.links.new(n.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);body.data.materials.clear();body.data.materials.append(mat);me.uv_layers.active=me.uv_layers['HeadUV'];me.uv_layers['HeadUV'].active_render=True
for f in me.polygons:f.material_index=0
common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/'review/head_checker'),1.3,.8,views=('front','left','three_quarter'),resolution=(700,700));(P/'review/head_uv_pack.json').write_text(json.dumps(report,indent=2)+'\n')
