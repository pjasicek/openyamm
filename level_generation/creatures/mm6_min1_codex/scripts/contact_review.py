import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gated_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];j=json.loads((P/'review/rig_gates.json').read_text());sc=bpy.context.scene;common.workbench_clay(sc)
red=bpy.data.materials.new('contact');red.diffuse_color=(1,.01,.01,1);gold=bpy.data.materials.new('body contact');gold.diffuse_color=(1,.6,.01,1)
for nm,k in [('Walking','L_hand'),('Death','L_forearm')]:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];v=j[nm]['G6'][k];sc.frame_set(v['frame']);o=ax if k=='axe' else b;ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=o.matrix_world@m.vertices[v['sample']].co;ev.to_mesh_clear()
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c2=sum((b.matrix_world@m.vertices[i].co for i in v['hit_face']),Vector())/3;ev.to_mesh_clear()
 print('CONTACT',nm,k,v['frame'],'rest sample',list(o.data.vertices[v['sample']].co),'rest hit',[(i,list(b.data.vertices[i].co)) for i in v['hit_face']],'posed',list(c),list(c2),flush=True)
 marks=[]
 for pos,mat in [(c,red),(c2,gold)]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.015,location=pos);ob=bpy.context.object;ob.data.materials.append(mat);marks.append(ob)
 common.render_views(str(P/f'review/contact_{nm}_{k}'),c.z,1.0,views=['front','left','three_quarter'],target=(c.x,c.y),resolution=(640,640))
 for ob in marks:bpy.data.objects.remove(ob,do_unlink=True)
