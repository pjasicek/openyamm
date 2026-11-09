from pathlib import Path
p=Path(__file__).resolve().parent/'animate_lizard.py';source=p.read_text().split('reports={}')[0]
source=source.replace("rot('Foot_'+s,body_x,15*fall)","rot('Foot_'+s,body_x,15*fall);f=rig.pose.bones['Foot_'+s];f.matrix=Matrix.LocRotScale(f.head.copy(),f.matrix.to_quaternion().slerp(Q[s],fall),Vector((1,1,1)));bpy.context.view_layer.update()")
source=source.replace("if fall:offset((0,0,.006-float(co()[:,2].min())))","if fall:rot('Tail1',X,-DROP*fall);offset((0,0,.006-float(co()[:,2].min())))")
exec(compile(source,str(p),'exec'))
for DROP in [0,6,10,12,15]:
 pose('Dead',0);v=co();report={}
 for name in ['Hips','Chest','Head','Foot_L','Foot_R','Tail8']:
  g=body.vertex_groups[name].index;ids=[x.index for x in body.data.vertices if any(a.group==g and a.weight>.5 for a in x.groups)];report[name]=[round(float(v[ids,2].min()),3),round(float(v[ids,2].max()),3)]
 print('TRIAL',DROP,report,flush=True)
