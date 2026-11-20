"""Fit hinge centres inside limb shells, then build source-frame bones and connected finger chains."""
from pathlib import Path
import bpy,bmesh,json,runpy,sys
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
# The generator dent at the front belt is a small folded patch, away from joints.
verts=[v for v in bm.verts if abs(v.co.x+.025)<.035 and .895<v.co.z<.955 and v.co.y<-.10]
for _ in range(8):bmesh.ops.smooth_vert(bm,verts=verts,factor=.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(me);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
M=json.loads((p/'work/meshy_joints.json').read_text())['joints'];R=json.loads((p/'work/joints.json').read_text())['joints']
report={}
def cross_center(piece,z):
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if me.attributes['piece'].data[v.index].value!=piece],context='VERTS')
 res=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,z),plane_no=(0,0,1))
 pts=np.array([v.co[:] for v in res['geom_cut'] if isinstance(v,bmesh.types.BMVert)])
 assert len(pts)>5,(piece,z,len(pts))
 # At knee height each leg is a single loop; extrema avoid vertex-density bias.
 result=(pts.min(0)+pts.max(0))/2;bm.free();return result.tolist()
for side,piece in [('L',0),('R',2)]:
 old=M[side+'_Calf'];M[side+'_Calf']=cross_center(piece,old[2]);report[side+'_knee']={'old':old,'fitted':M[side+'_Calf']}
 M[side+'_Hand']=R[side+'_Hand'];M[side+'_Foot']=R[side+'_Foot']
 # Preserve source-compatible toe joint at the ball of the actual boot.
 M[side+'_Toe0']=[M[side+'_Foot'][0],-.130,.035]
(p/'work/joints_final.json').write_text(json.dumps({'height_m':1.7,'joints':M,'report':report},indent=2))
print('FITTED',json.dumps(report))
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',p/'work/rig_v1.blend')
