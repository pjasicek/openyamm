"""Update only UVs and material maps in the editable masters; positions, weights and actions stay intact."""
import bpy,numpy as np,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'round3_lod{level}.blend'));body=bpy.data.objects['Body'];mesh=body.data;mesh.calc_loop_triangles();d=np.load(p/'work'/f'uv_final_lod{level}_r4.npz');assert np.array_equal(np.array([t.vertices[:] for t in mesh.loop_triangles]),d['faces'])
 assigned={}
 for t,uv in zip(mesh.loop_triangles,d['uv']):
  for loop,q in zip(t.loops,uv):
   if loop in assigned:assert np.max(np.abs(assigned[loop]-q))<1e-6
   assigned[loop]=q;mesh.uv_layers.active.data[loop].uv=q
 for m in body.data.materials:
  for n in m.node_tree.nodes:
   if n.type!='TEX_IMAGE' or not n.image:continue
   channel='basecolor' if 'basecolor' in n.image.name else 'normal' if 'normal' in n.image.name else 'orm' if 'metal_rough' in n.image.name or '_orm' in n.image.name else None
   if channel:
    im=bpy.data.images.load(str(p/'textures/round4'/f'sor1_{channel}.png'),check_existing=True);im.colorspace_settings.name='sRGB' if channel=='basecolor' else 'Non-Color';n.image=im
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/f'round4_lod{level}.blend'))
 if level==0:
  bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/production_master.blend'));common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(p/'review/round4/colour_preview'),.90,2.0,views=('front','left','back','three_quarter'),resolution=(700,900));common.render_views(str(p/'review/round4/collar_preview'),1.45,.65,views=('front',),resolution=(700,700))
