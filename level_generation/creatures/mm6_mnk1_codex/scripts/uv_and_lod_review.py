import bpy,numpy as np,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mnk1.blend'));b=bpy.data.objects['Body'];uv=b.data.uv_layers['UVMap'];coords=np.array([tuple(q.uv) for q in uv.data]);areas=[]
b.data.calc_loop_triangles()
for f in b.data.loop_triangles:
 a,c,d=[coords[i] for i in f.loops];areas.append(abs(np.cross(c-a,d-a))/2)
report={'finite':bool(np.isfinite(coords).all()),'range':[float(coords.min()),float(coords.max())],'min_area':float(min(areas)),'zero_area_faces':int((np.array(areas)<1e-14).sum()),'faces':len(areas),'repairs':'Round 4: fresh non-overlapping UVs and four-map rebake; see round4/rebaked/bake.json'}
assert report['finite'] and coords.min()>=-1e-5 and coords.max()<=1.00001 and report['zero_area_faces']==0
(p/'review/uv_validation.json').write_text(json.dumps(report,indent=2))
for level in range(4):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/f'work/review_lod{level}.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;common.workbench_clay(sc);sc.display.shading.show_specular_highlight=False;sc.display.shading.show_cavity=False
 for name,time in [('Standing',0),('Attack',.717),('Dead',0)]:
  a=next(a for a in bpy.data.actions if a.name==name);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=time*sc.render.fps;sc.frame_set(int(f),subframe=f%1)
  common.render_views(str(p/f'review/final_frames/lod{level}_{name}'),.85,2.5,views=('three_quarter',),resolution=(480,480),target=(.18,.22))
