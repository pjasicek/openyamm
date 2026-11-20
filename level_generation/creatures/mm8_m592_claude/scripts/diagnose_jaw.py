from pathlib import Path
import bpy,numpy as np,json,sys,math
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];co=np.array([tuple(v.co) for v in b.data.vertices]);E=np.array([tuple(e.vertices) for e in b.data.edges]);L=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)
g=b.vertex_groups['Jaw'].index;w=np.array([sum(x.weight for x in v.groups if x.group==g) for v in b.data.vertices]);a=b.data.color_attributes.new(name='JawWeights',type='FLOAT_COLOR',domain='POINT');a.data.foreach_set('color',np.array([[x,.15,1-x,1] for x in w]).ravel())
common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='VERTEX';common.render_views(str(P/'review/rig_probes/jaw_weights'),1.24,.55,views=('front','left','three_quarter'),resolution=(700,700),target=(0,-.43))
r.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(15));bpy.context.view_layer.update();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();posed=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(posed[E[:,0]]-posed[E[:,1]],axis=1)/np.maximum(L,1e-9)
for j in np.argsort(ratio)[-16:]:
 aa,bb=E[j];print('BAD_JAW',round(float(ratio[j]),2),aa,bb,np.round(co[aa],4),np.round(co[bb],4),round(float(w[aa]),3),round(float(w[bb]),3),flush=True)
