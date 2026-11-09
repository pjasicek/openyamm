import bpy,sys,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v1.blend'))
m=bpy.data.objects['Gargoyle']; co=np.array([v.co[:] for v in m.data.vertices])
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('ReviewWorld'); common.workbench_clay(scene)
for name,c,h in [('left_hand',(.42,-.10,.88),.5),('right_hand',(-.42,-.10,.88),.5),('left_foot',(.34,-.22,.12),.5),('head',(0,-.29,1.66),.58)]:
    common.render_views(str(P/'review'/name),c[2],h,views=('front','left','three_quarter'),resolution=(650,650),target=c[:2])
np.save(P/'work/mesh_edges.npy',np.array([e.vertices[:] for e in m.data.edges]))
for name,mask in [('left_hand',(co[:,0]>.3)&(co[:,2]>.70)&(co[:,2]<1.02)),('left_foot',(co[:,0]>0)&(co[:,2]<.23))]:
    ids=np.flatnonzero(mask); np.savetxt(P/'work'/f'{name}_vertices.csv',np.column_stack((ids,co[ids])),delimiter=',',header='id,x,y,z',fmt=['%d','%.6f','%.6f','%.6f'])
print('DETAILS_RENDERED')
