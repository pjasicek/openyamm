"""CPU material/clay head review, independent of Meshy's thumbnail lights."""
import bpy,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];kind=os.environ.get('KEPT_BODY','female');code='f' if kind=='female' else 'm';mode=os.environ.get('KEPT_PREVIEW','raw')
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/kind/('rig_uv_hairfixed.blend' if kind=='female' and mode in ('final','fixedclay') else 'rig_uv.blend')))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
body=bpy.data.objects['Body'];me=body.data
for mod in list(body.modifiers):body.modifiers.remove(mod)
for o in list(bpy.data.objects):
 if o!=body:bpy.data.objects.remove(o,do_unlink=True)
me.materials.clear()
for head in (False,True):
 mat=bpy.data.materials.new('Head' if head else 'Body');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial')
 sh=nt.nodes.new('ShaderNodeEmission' if mode in ('raw','final') else 'ShaderNodeBsdfDiffuse')
 nt.links.new(sh.outputs[0],out.inputs['Surface'])
 if mode not in ('clay','fixedclay'):
  tex=nt.nodes.new('ShaderNodeTexImage');uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='HeadUV' if head else 'FreedUV';nt.links.new(uv.outputs[0],tex.inputs[0])
  file=P/'meshy'/f'kept_{code}_{"head" if head else "freed"}_v1'/'texture_urls_0_base_color.png' if mode=='raw' else P/'textures'/f'kept_{code}_{"head" if head else "freed"}_basecolor_1k.png'
  tex.image=bpy.data.images.load(str(file));nt.links.new(tex.outputs['Color'],sh.inputs['Color'])
 else:sh.inputs['Color'].default_value=(.6,.6,.6,1)
 me.materials.append(mat)
for p,h in zip(me.polygons,me.attributes['head'].data):p.material_index=int(bool(h.value))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.world=bpy.data.worlds.new('TextureReview');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.4,.4,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
if mode in ('clay','fixedclay'):
 data=bpy.data.lights.new('Key','AREA');data.energy=180;data.shape='DISK';data.size=2;o=bpy.data.objects.new('Key',data);scene.collection.objects.link(o);o.location=(-1,-2,3);o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
sys.path.insert(0,str(P/'scripts'));from kept_review_common import render_views
render_views(str(P/'review'/kind/f'head_{mode}'),1.54,.43,views=('front','three_quarter'),resolution=(640,640),target=(-.02,0))
sys.stdout.flush();sys.stderr.flush();os._exit(0)
