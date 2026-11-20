"""Relieve the Forgemaster's armholes and wrist cuffs without changing its body or fitted grips."""
import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';src=P/'work/forge_fitted.blend';out=P/'work/forge_edgefit.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
for side in 'LR':
 ob=bpy.data.objects['Arm_breast_'+side]
 for v in ob.data.vertices:v.co.x*=.8
 ob=bpy.data.objects['Arm_forearm_'+side];elbow=r.data.bones[f'B_{side}_Forearm'].head_local;delta=r.data.bones[f'B_{side}_Hand'].head_local-elbow
 for v in ob.data.vertices:
  t=(v.co-elbow).dot(delta)/delta.length_squared;k=min(1,max(0,(t-.60)/.30));v.co-=delta*(.13*k*k*(3-2*k))
bpy.ops.wm.save_as_mainfile(filepath=str(out))
sys.argv=['skin_shell.py','--',str(out),str(S/'armour_forge.json'),str(out)];runpy.run_path(str(S/'skin_shell.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
