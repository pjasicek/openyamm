"""Run the existing shared gates on the regenerated unreduced pilot."""
import bpy,sys,json,runpy,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
for o in list(bpy.data.objects):
 if o not in [body,rig]:bpy.data.objects.remove(o,do_unlink=True)
for v in body.data.vertices:
 ws=sorted([(g.group,g.weight)for g in v.groups],key=lambda x:-x[1])[:4];total=sum(w for _,w in ws)
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for gi,w in ws:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
for o in bpy.data.objects:o.select_set(o in [body,rig])
bpy.context.view_layer.objects.active=rig
# Match final 120 Hz baked interpolation.
for a in bpy.data.actions:
 for layer in a.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x*=4;k.handle_left.x*=4;k.handle_right.x*=4
     fc.update()
for a in bpy.data.actions:
 if a.use_frame_range:
  first,last=a.frame_start,a.frame_end;a.frame_end=last*4;a.frame_start=first*4
bpy.context.scene.render.fps=120
bpy.ops.export_scene.gltf(filepath=str(P/'work/round2/pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_extras=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
glb=G.Glb(P/'work/round2/pilot.glb');meshes=G.load_meshes(glb)
co=np.array([tuple(v.co)for v in body.data.vertices]);part=np.array([v.value for v in body.data.attributes['piece'].data]);kd=KDTree(len(co))
for i,c in enumerate(co):kd.insert(c,i)
kd.balance();lod={}
for m in meshes:
 pp=part[[kd.find(v)[1]for v in m.rest]]
 ids=lambda mask:{'vertices':np.where(mask)[0].tolist()}
 lod[m.label.split('/')[-1]]={'head':ids((pp==0)&(m.rest[:,2]>1.555)),'head_obstacles':ids(pp==1),'skirt':ids(pp==2),'boots':ids(np.isin(pp,[6,7])&(m.rest[:,2]<.84)),'shirt':ids(pp==1),'hand_L':ids(pp==3),'hand_R':ids(pp==4)}
cfg=json.loads((P/'gates.json').read_text());cfg['lod_regions']=lod;cfg.pop('previous_counts',None)
cfg['cloth']=[{'name':'coat hem','surface':'skirt','samples':'boots','opening':{'axis':[0,0,-1]}}]
for sd in 'LR':
 hand=glb.rest[glb.names[f'B_{sd}_Hand']];wr=hand[:3,3];finger=glb.rest[glb.names[f'B_{sd}_Finger2'],:3,3];axis=G.unit(finger-wr)
 cfg['cloth'].append({'name':sd+' sleeve cuff','surface':'shirt','samples':'hand_'+sd,'containment':True,'opening':{'node':f'B_{sd}_Hand','point':[0,0,0],'axis':(hand[:3,:3].T@axis).tolist()}})
cfg['props'][0]['file']=str(P/'export/mm6_mer1_club.glb')
config=P/'work/round2/pilot_gates.json';config.write_text(json.dumps(cfg,indent=2))
sys.argv=['run_gates.py','--',str(P/'work/round2/pilot.glb'),'--config',str(config),'--out',str(P/'review/round2/polished_gates')]
runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='__main__')
