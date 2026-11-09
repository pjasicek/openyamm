"""Remove the reused skull's central orbital bumps, retaining the socket rim and posterior cranium."""
import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
me=bpy.data.objects['Body'].data;co=np.array([tuple(v.co)for v in me.vertices])
piece=np.array([x.value for x in me.attributes['piece'].data]);off=json.loads((P/'work/skull_fit.json').read_text())['offset'];report=[]
for s in [-1,1]:
    c=np.array([off[0]+s*.027,1.675]);xz=co[:,[0,2]]-c;r=np.linalg.norm(xz,axis=1)
    domain=(piece==2000)&(co[:,1]<0)&(r<.012)
    ring=(piece==2000)&(co[:,1]<0)&(r>.008)&(r<.012)
    fit=np.linalg.lstsq(np.c_[xz[ring],np.ones(sum(ring))],co[ring,1],rcond=None)[0]
    target=np.c_[xz,np.ones(len(co))]@fit+.004*(1-(r/.012)**2)
    w=np.clip((.012-r)/.004,0,1);w=w*w*(3-2*w)
    for i in np.where(domain)[0]:me.vertices[int(i)].co.y=float(co[i,1]*(1-w[i])+target[i]*w[i])
    displacement=[abs(me.vertices[int(i)].co.y-co[i,1])for i in np.where(domain)[0]]
    assert max(displacement)<.02
    report.append({'side':s,'vertices':int(sum(domain)),'max_displacement':max(displacement)})
bpy.context.view_layer.update();common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/skull_hollow'),1.68,.30,views=('front','left','three_quarter'),resolution=(600,600),target=(off[0],off[1]))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_complete.blend'))
(P/'work/orbit_cleanup.json').write_text(json.dumps(report,indent=2));print('ORBIT CLEANUP',report)
