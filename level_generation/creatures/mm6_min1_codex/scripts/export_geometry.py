import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;sc.render.fps=30;sc.render.fps_base=1
# Head UV must occupy real area and stay in bounds before paying for a retexture.
h=b.data.attributes['head'];u=b.data.uv_layers['HeadUV'].data;rat=[]
for f in b.data.polygons:
 if not h.data[f.index].value:continue
 q=np.array([u[i].uv[:] for i in f.loop_indices]);assert q.min()>=-1e-5 and q.max()<=1.00001
 a=abs(np.linalg.det(np.stack([q[1]-q[0],q[2]-q[0]])))/2;assert a>1e-10,(f.index,a);rat.append(a/max(f.area,1e-10))
(P/'review/uv_preflight.json').write_text(json.dumps({'head_triangles':len(rat),'area_density_percentiles':np.percentile(rat,[1,50,99]).tolist(),'body_uv_route':'Meshy owns layout; topology-preserving UV transfer checked after return','pass':True},indent=2))
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
for o in bpy.data.objects:o.select_set(o in [r,b,ax])
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(P/'work/geometry_review.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
common.workbench_clay(sc)
for nm in ['Standing','Attack','Death','Dead']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(17 if nm=='Attack' else int(a.frame_range[1]) if nm in ['Death','Dead'] else 0);common.render_views(str(P/f'review/final_clay_{nm}'),1,3.0,views=['front','left','three_quarter'],resolution=(420,600))
