"""Fit the reviewed skull/cowl, shorten excess trailing cloth, and measure skeletal arm joints."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();parts=bm.verts.layers.int['part']
remove=[v for v in bm.verts if v.co.z>1.925 or v[parts] in [2,10,14,16,17]]
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(me);bm.free()
for v in me.vertices:
 if v.co.z<1.5 and v.co.y>.16:
  blend=np.clip((1.5-v.co.z)/.8,0,1);v.co.y=.16+(v.co.y-.16)*(1-.45*blend)
with bpy.data.libraries.load(str(P/'work/head_detail.blend'),link=False) as (src,dst):dst.objects=['HeadDetail']
head=dst.objects[0];bpy.context.collection.objects.link(head)
for v in head.data.vertices:
 if v.co.y>.09:v.co.y=.09+(v.co.y-.09)*.48
 v.co.x-=.014
for a in head.data.attributes['part'].data:a.value+=100
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
me=body.data;co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data])
for f in me.polygons:f.use_smooth=True
# Exposed forearm pieces independently locate both elbow and wrist ends.
J={'Pelvis':[-.014,.075,1.30],'Spine':[-.014,.075,1.45],'Spine1':[-.014,.075,1.62],'Spine2':[-.014,.075,1.79],'Neck':[-.014,.055,1.91],'Head':[-.014,.04,2.015]}
for sd,sign,pn in [('L',1,7),('R',-1,13)]:
 c=co[pa==pn];axis=np.array([sign*.79,-.12,-.60]);axis/=np.linalg.norm(axis);d=c@axis;lo=c[d<np.quantile(d,.12)].mean(0);hi=c[d>np.quantile(d,.88)].mean(0)
 J[sd+'_Clavicle']=[-.014+sign*.065,.075,1.82];J[sd+'_UpperArm']=[-.014+sign*.215,.067,1.835];J[sd+'_Forearm']=lo.tolist();J[sd+'_Hand']=hi.tolist()
(P/'work/joints_final.json').write_text(json.dumps({'joints':J,'method':'Forearm endpoint cross sections; shoulder inside garment contour; source-frame body fitting.'},indent=2))
np.savez(P/'work/fitted_geometry.npz',co=co,parts=pa,edges=np.array([e.vertices[:] for e in me.edges]),tri=np.array([f.vertices[:] for f in me.polygons],dtype=np.int32))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/fitted'),1.115,2.55,views=('front','left','three_quarter','back'),resolution=(650,850),target=(0,.05))
common.render_views(str(P/'review/fitted_head'),2.025,.63,views=('front','left'),resolution=(700,700),target=(0,.025))
print('FIT',len(me.vertices),len(me.polygons),J)
