"""Round-two review from final runtime GLBs, including the user's exact problem poses."""
from pathlib import Path
P = Path(__file__).resolve().parents[1]
import sys,json,numpy as np
from mathutils import Vector
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
import run_gates as G
glb=G.Glb(P/'export/mm6_natm.glb');mesh=G.load_meshes(glb)[0]
action=next(a for name,a,t,end in glb.clips()if name=='Cast')
pose=glb.pose(action,np.array([23/48]))[0];cfg=json.loads((P/'gates.json').read_text())
palm=pose[glb.names['B_L_Hand'],:3,:3]@cfg['hands']['L']['palm_axis']
socket=pose[glb.names['Socket_LeftPalm'],:3,3]
surface=G.Surface(mesh,mesh.weight(['B_L_Hand','B_L_Finger*'])>.4).build(mesh.posed(pose))
closest=surface.tree.find_nearest(Vector(socket))
(P/'review/round2_release_diagnostic.json').write_text(json.dumps({
    'source_sha256':glb.sha256,'time_s':23/48,'palm_forward_deg':float(G.angle(palm,[0,-1,0])),
    'socket_world_m':socket.tolist(),'socket_to_hand_surface_mm':closest[3]*1000,
    'scope':'Single release-pose diagnostic using the shared GLB evaluator and contact BVH; not a head/palm gate.'},indent=2))
source = (P/'scripts/review1_render.py').read_text().replace('round1', 'round2').replace('ROUND1', 'ROUND2')
source = source.replace('[(0,700),(1,550),(2,220),(3,88)]',
                        '[(0,700),(0,550),(0,220),(0,88),(1,550),(2,220),(3,88)]')
source = source.replace("if level==0 else['natm_b']", "if level==0 and size==700 else['natm_b']")
exec(compile(source, str(P/'scripts/review1_render.py'), 'exec'))
sc,r,meshes = load(P/'review/viewer/mm6_natm_b.glb')
for role, time in [('Attack',15/48),('Attack',23.5/48),('Cast',23/48),('Fidget',77/48),('Standing',0)]:
    activate(r,role,time)
    common.render_views(str(folder/f'round2_{role}_{round(time*48):02}_head'),1.49,.66,
                        views=('front','left','three_quarter'),resolution=(850,850))
    if role == 'Cast':
        common.render_views(str(folder/'round2_cast_release'),1.20,1.35,
                            views=('front','left','three_quarter'),resolution=(900,900))
