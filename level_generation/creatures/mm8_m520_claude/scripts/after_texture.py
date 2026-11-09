from pathlib import Path
import bpy,sys,runpy,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
def run(n,args):
 s=p/f'scripts/{n}.py';sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('transfer_uv',[p/'work/rig_surface.blend',p/'meshy/body_retexture_v1',p/'work/rig_texturing.blend'])
run('transfer_uv',[p/'work/rig_texturing.blend',p/'meshy/head_retexture_v1',p/'work/rig_texturing.blend','HeadUV'])
run('uv_gate',[])
for layer in ['UVMap','HeadUV']:run('uv_raster',[p/'work/rig_texturing.blend',layer,1024])
body=bpy.data.objects['Body'];me=body.data;edges={};head=me.attributes['head'].data
for face in me.polygons:
 for a,b in zip(face.vertices,list(face.vertices[1:])+[face.vertices[0]]):edges.setdefault(tuple(sorted((a,b))),[]).append(face)
seams=[]
for (a,b),faces in edges.items():
 if len(faces)!=2 or head[faces[0].index].value==head[faces[1].index].value:continue
 for t in [0,.5,1]:
  row={'pos':list(me.vertices[a].co.lerp(me.vertices[b].co,t))}
  for face in faces:
   name='head' if head[face.index].value else 'body';uv=me.uv_layers['HeadUV' if name=='head' else 'UVMap'].data;inds=list(face.vertices);ls=list(face.loop_indices)
   row[name]=list(uv[ls[inds.index(a)]].uv.lerp(uv[ls[inds.index(b)]].uv,t))
  seams.append(row)
assert len(seams)>20,len(seams);(p/'work/seam_samples.json').write_text(json.dumps(seams))
me.materials.clear()
for kind in ['body','head']:
 mat=bpy.data.materials.new(kind);mat.use_nodes=True;nt=mat.node_tree;img=nt.nodes.new('ShaderNodeTexImage');img.image=bpy.data.images.load(str(p/f'meshy/{kind}_retexture_v1/texture_urls_0_base_color.png'));nt.nodes.active=img;nt.links.new(img.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);me.materials.append(mat)
for face in me.polygons:
 face.material_index=int(head[face.index].value)
 if face.material_index:
  for li in face.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
me.uv_layers.active=me.uv_layers['UVMap'];common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/texture_raw_body'),1.2,2.7,views=('front','left','back','three_quarter'),resolution=(800,1000))
common.render_views(str(p/'review/texture_raw_head'),2.2,.52,views=('front','left','back','three_quarter'),resolution=(800,800))
