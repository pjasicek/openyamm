"""Use Meshy axial/limb estimates, measured hand opening centres and boot cross-sections."""
import bpy,bmesh,json,os
import numpy as np
from mathutils import Vector
p=os.path.dirname(os.path.dirname(__file__))
bpy.ops.wm.open_mainfile(filepath=p+'/work/step1.blend')
body=bpy.data.objects['Body'];me=body.data
M=json.load(open(p+'/work/meshy_joints.json'))['joints'];J={k:list(v) for k,v in M.items()}
pieces=[v.value for v in me.attributes['piece'].data];report={}
for side,hand_id,boot_id in (('L',3,5),('R',4,6)):
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if pieces[v.index]!=hand_id],context='VERTS')
 edges=[e for e in bm.edges if e.is_boundary];vertices=list({v for e in edges for v in e.verts})
 assert len(vertices)>=8 and all(sum(e.is_boundary for e in v.link_edges)==2 for v in vertices)
 wrist=sum((v.co for v in vertices),Vector())/len(vertices);perimeter=sum(e.calc_length() for e in edges)
 assert .10<perimeter<.30,(side,perimeter)
 J[side+'_Hand']=list(wrist);bm.free()
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if pieces[v.index]!=boot_id],context='VERTS')
 ankle=Vector(M[side+'_Foot'])
 cut=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=ankle,plane_no=Vector((0,0,1)))
 ev=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
 vs=list({v for e in ev for v in e.verts});assert len(vs)>=6
 J[side+'_Foot']=list(sum((v.co for v in vs),Vector())/len(vs));bm.free()
 report[side]={'wrist_opening_vertices':len(vertices),'wrist_perimeter_cm':perimeter*100,'meshy_wrist_shift_cm':float((wrist-Vector(M[side+'_Hand'])).length*100),'ankle_center_shift_cm':float((Vector(J[side+'_Foot'])-ankle).length*100)}
 print('JOINT_COMPOSE',side,report[side])
json.dump({'height_m':1.7,'joints':J,'report':report,'method':'Meshy axial/shoulder/elbow/hip/knee estimates; actual hand boundary-loop centres; boot cross-section centres at Meshy ankle height'},open(p+'/work/joints_final.json','w'),indent=2)
