import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/bow_clay.blend'));ob=bpy.data.objects['BowArrow'];T=P/'textures/bow';mat=bpy.data.materials.new('LizardBow');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
def tex(file,space):
 n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/file));n.image.colorspace_settings.name=space;return n
nt.links.new(tex('basecolor_1k.png','sRGB').outputs['Color'],bs.inputs['Base Color']);mr=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough_1k.png','Non-Color').outputs['Color'],mr.inputs['Color']);nt.links.new(mr.outputs['Green'],bs.inputs['Roughness']);nt.links.new(mr.outputs['Blue'],bs.inputs['Metallic']);bs.inputs['Specular IOR Level'].default_value=.2
norm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k.png','Non-Color').outputs['Color'],norm.inputs['Color']);nt.links.new(norm.outputs['Normal'],bs.inputs['Normal']);norm.inputs['Strength'].default_value=.65
ob.data.materials.clear();ob.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bow_textured.blend'))
# The assembled actor uses a keyed nock; this fixed line is only the standalone prop review.
cu=bpy.data.curves.new('StringReview','CURVE');cu.dimensions='3D';cu.bevel_depth=.0009;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(1);sp.points[0].co=(0,.215,-.55,1);sp.points[1].co=(0,.215,.55,1);so=bpy.data.objects.new('StringReview',cu);bpy.context.collection.objects.link(so);ma=bpy.data.materials.new('Natural sinew');ma.diffuse_color=(.35,.27,.16,1);cu.materials.append(ma)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.view_settings.view_transform='AgX';scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,pos,power,size in [('Key',(1,-1,1.1),70,1.3),('Fill',(-1,.5,.2),35,1.3)]:
 da=bpy.data.lights.new(name,'AREA');da.energy=power;da.size=size;o=bpy.data.objects.new(name,da);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
for name,vec,centre,scale,rez in [('bow_textured',(1,-.6,.12),(.08,.10,0),1.28,(850,1100)),('bow_grip_closeup',(1,-.8,.12),(0,0,0),.29,(1000,800))]:
 d=Vector(vec).normalized();c=Vector(centre);cam=common.ortho_camera('PropCamera',c+d*3,(0,0,0),scale);cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=rez;scene.render.filepath=str(P/f'review/{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
