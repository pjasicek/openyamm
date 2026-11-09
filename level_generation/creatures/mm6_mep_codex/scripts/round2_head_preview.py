import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_head_lod0.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
# Produce the exact engine region-ramp colour in the authoring preview.
mat=next(m for m in b.data.materials if 'Head' in m.name);cfg=json.loads((P/'textures/mep_ramps.json').read_text())['materials'][1];N=1024
base=bpy.data.images.load(str(P/'textures/lod0/mep_head_basecolor.png'),check_existing=False);mask=bpy.data.images.load(str(P/'textures/lod0/mep_head_region_mask.png'),check_existing=False);mask.colorspace_settings.name='Non-Color';mask.alpha_mode='CHANNEL_PACKED'
a=np.array(base.pixels[:]).reshape(N,N,4);w=np.array(mask.pixels[:]).reshape(N,N,4);lum=a[:,:,:3]@np.array([.2126,.7152,.0722]);out=a[:,:,:3].copy()
for c,reg in enumerate(cfg['ramps']['mep_a']):
 t=np.clip((lum-reg['range'][0])/(reg['range'][1]-reg['range'][0]),0,1)*15;i=np.minimum(t.astype(int),14);f=(t-i)[:,:,None];colors=np.array(reg['colors']);out=out*(1-w[:,:,c,None])+(colors[i]*(1-f)+colors[i+1]*f)*w[:,:,c,None]
a[:,:,:3]=out;im=bpy.data.images.new('TierA',width=N,height=N,alpha=True,float_buffer=True);im.pixels.foreach_set(a.astype(np.float32).ravel());nt=mat.node_tree;nt.nodes.clear();tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.nodes.active=tex;bs=nt.nodes.new('ShaderNodeBsdfPrincipled');outn=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(bs.outputs[0],outn.inputs[0]);b.data.uv_layers.active=b.data.uv_layers['MergedUV'];b.data.uv_layers['MergedUV'].active_render=True
sc=bpy.context.scene;common.workbench_clay(sc,True);sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.display.shading.show_specular_highlight=False
common.render_views(str(P/'review/round2/head_candidate'),1.53,.44,views=('front','left','three_quarter'),resolution=(700,800))
