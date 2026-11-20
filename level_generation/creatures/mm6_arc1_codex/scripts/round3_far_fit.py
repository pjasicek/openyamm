import bpy,json,sys,numpy as np,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/lod3.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);world=[];rest=[];transforms=[];tri=[];editable=[]
for name in ['Body','BowAsset','BowString']:
 o=bpy.data.objects[name];o.data.calc_loop_triangles();base=len(world);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();world.extend([list(v.co)for v in m.vertices]);ev.to_mesh_clear();rest.extend([list(v.co)for v in o.data.vertices]);gn={g.index:g.name for g in o.vertex_groups};piece=o.data.attributes.get('piece')
 for v in o.data.vertices:
  mat=sum((np.array(r.pose.bones[gn[g.group]].matrix@r.data.bones[gn[g.group]].matrix_local.inverted())[:3,:3]*g.weight for g in v.groups),np.zeros((3,3)));transforms.append(mat.tolist());protect=sum(g.weight for g in v.groups if any(t in gn[g.group]for t in ['Hand','Finger','Foot','Toe','Head','Neck']))>.15;editable.append(name=='Body'and not protect and piece.data[v.index].value in [0,1]and v.co.z>.04)
 tri.extend([[base+i for i in t.vertices]for t in o.data.loop_triangles])
(P/'work/round3/fit_input.json').write_text(json.dumps({'world':world,'rest':rest,'transforms':transforms,'triangles':tri,'editable':editable}));subprocess.run(['/usr/bin/python3',str(P/'scripts/round3_far_fit_cpu.py')],check=True)
data=json.loads((P/'work/round3/fit_output.json').read_text());ob=bpy.data.objects['Body']
for v,co in zip(ob.data.vertices,data['rest']):v.co=co
ob.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/lod3_fitted.blend'))
