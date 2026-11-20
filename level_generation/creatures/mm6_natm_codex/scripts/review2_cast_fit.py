"""Fit casting-hand roll using the shared evaluator's actual shield/skin contact function."""
import sys,json,numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
import run_gates as G
config=json.loads((P/'gates.json').read_text());glb=G.Glb(P/'export/mm6_natm.glb')
prop=G.Glb(P/'export/mm6_natm_buckler.glb');body=G.load_meshes(glb);shield=G.load_meshes(prop)
action=next(a for n,a,t,e in glb.clips()if n=='Cast')
frames=np.arange(6,69,2);times=frames/48;poses=glb.pose(action,times)
hand=glb.names['B_L_Hand'];affected=[hand]
for node in affected:affected.extend(glb.nodes[node].get('children',[]))
normal=np.array(config['hands']['L']['palm_axis'])
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
amount=smooth(4,23,frames)*(1-smooth(38,68,frames))
surfaces={}
for level in [0,3]:
    m=body[level];mask=np.ones(len(m.rest),bool)
    for cloth in config['cloth']:mask &= ~m.select(config['regions'][cloth['surface']])
    surfaces[level]=G.Surface(m,mask)
results=[]
for degrees in [-40,-30,-20,0,20,30,40]:
    worst=0
    for frame,t,pose,weight in zip(frames,times,poses,amount):
        changed=pose.copy();axis=G.unit(pose[hand,:3,:3]@normal)
        delta=np.array(Quaternion(Vector(axis),np.radians(degrees*weight)).to_matrix())
        origin=pose[hand,:3,3]
        for node in affected:
            changed[node,:3,:3]=delta@pose[node,:3,:3]
            changed[node,:3,3]=origin+delta@(pose[node,:3,3]-origin)
        for level in [0,3]:
            points=body[level].posed(changed)
            prop_points=G.transform(changed[glb.names['Buckler']]@np.linalg.inv(G.C),shield[level].rest)
            depth,_=G.penetration(surfaces[level].build(points),prop_points)
            worst=max(worst,depth)
    results.append({'roll_deg':degrees,'fit_max_penetration_mm':worst})
    print('FIT',results[-1],flush=True)
best=min(results,key=lambda x:(x['fit_max_penetration_mm'],abs(x['roll_deg'])))
(P/'work/round2_cast_fit.json').write_text(json.dumps({'candidates':results,'selected':best,
    'scope':'Authoring fit, 24 Hz LOD0/3. Final acceptance uses the complete unmodified shared runner.'},indent=2))
