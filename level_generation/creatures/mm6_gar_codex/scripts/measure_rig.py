"""Classify wing surface by connected back-side geometry and measure the body skin rings."""
import bpy,sys,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_assembled.blend'))
body=bpy.data.objects['Body']; co=np.array([v.co[:] for v in body.data.vertices])
zs=np.arange(1.0,1.61,.025); back=[]
for z in zs:
    sample=co[(abs(co[:,2]-z)<.018)&(abs(co[:,0])<.04)]
    back.append(float(sample[:,1].max()) if len(sample) else .1)
back_y=np.interp(co[:,2],zs,back)
cand=((co[:,1]>back_y+.018)&(abs(co[:,0])>.05)&(co[:,2]>1.07))|((co[:,2]>1.80)&(co[:,1]>.05))
adj=[[] for _ in co]
for edge in body.data.edges:
    a,b=edge.vertices; adj[a].append(b); adj[b].append(a)
wing=np.zeros(len(co),bool); stack=list(np.flatnonzero(cand&(abs(co[:,0])>.55)&(co[:,2]>1.5))); wing[stack]=True
while stack:
    a=stack.pop()
    for b in adj[a]:
        if cand[b] and not wing[b]: wing[b]=True; stack.append(b)
assert 500<wing.sum()<len(co)*.6,int(wing.sum())
np.save(P/'work/wing_mask.npy',wing); np.save(P/'work/body_vertices.npy',co)
report={'wing_vertices':int(wing.sum()),'body_vertices':len(co),'torso':[],'arms':{},'legs':{}}
def ring(mask,z):
    points=co[mask&(abs(co[:,2]-z)<.018)]
    if len(points)<4: return None
    low,high=points.min(0),points.max(0)
    return {'z':round(float(z),3),'n':len(points),'centre':((low+high)/2).round(4).tolist(),'bounds':[low.round(4).tolist(),high.round(4).tolist()]}
for z in np.arange(.85,1.64,.05):
    r=ring(~wing&(abs(co[:,0])<.13),z)
    if r: report['torso'].append(r)
for name,sg in [('L',1),('R',-1)]:
    report['arms'][name]=[r for z in np.arange(.90,1.57,.04) if (r:=ring(~wing&(co[:,0]*sg>.21),z))]
    report['legs'][name]=[r for z in np.arange(.15,.89,.04) if (r:=ring(~wing&(co[:,0]*sg>.05),z))]
(P/'work/skin_rings.json').write_text(json.dumps(report,indent=2))
attr=body.data.color_attributes.new('wing_class','FLOAT_COLOR','POINT')
for i,w in enumerate(wing): attr.data[i].color=(.8,.15,.12,1) if w else (.6,.64,.67,1)
body.data.color_attributes.active_color=attr
sc=bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type='VERTEX'
common.render_views(str(P/'review/wing_class'),1.5,3.3,views=('front','left','back','three_quarter'),resolution=(750,1050))
print('WING_CLASS',int(wing.sum()),'body',len(co),'back',np.round(back,3).tolist())
