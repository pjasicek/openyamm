"""Short-range CPU AO for the final cloth/hair, with one target per body/head material."""
import bpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];code='m' if kind=='male' else 'f';style=os.environ.get('KEPT_STYLE','ragged' if kind=='male' else 'freed')
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/kind/('rig_uv_hairfixed.blend' if kind=='female' else 'rig_uv.blend')))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
body=bpy.data.objects['Body'];me=body.data;hd=[a.value for a in me.attributes['head'].data];layer=me.uv_layers['RaggedUV' if style=='ragged' else 'FreedUV'];headuv=me.uv_layers['HeadUV']
for p in me.polygons:
 if hd[p.index]:
  for li in p.loop_indices:layer.data[li].uv=headuv.data[li].uv
me.uv_layers.active=layer;layer.active_render=True;me.materials.clear();images=[]
for what in (style,'head'):
 im=bpy.data.images.new(f'ao_{code}_{what}',1024,1024,alpha=False);mat=bpy.data.materials.new('BakeAO');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node;me.materials.append(mat);images.append((im,what))
for p in me.polygons:p.material_index=int(hd[p.index])
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body;sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.world=bpy.data.worlds.new('AO');sc.world.light_settings.distance=.035;sc.render.bake.margin=8;sc.render.bake.use_selected_to_active=False
bpy.ops.object.bake(type='AO')
for im,what in images:im.filepath_raw=str(P/'texturing'/f'kept_{code}_{what}_ao.png');im.file_format='PNG';im.save()
print('AO',kind,style,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
