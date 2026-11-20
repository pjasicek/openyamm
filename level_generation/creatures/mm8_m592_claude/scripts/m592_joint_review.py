"""Use the shared joint X-ray with a square frame suited to the Guardian's width."""
from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];R=P.parent/'mm6_natm_claude/scripts';sys.path.insert(0,str(R));import common
render=common.render_views
def wide(prefix,centre,height,**kw):
 if kw.get('resolution')==(600,900):height=2.5;kw['resolution']=(900,900)
 return render(prefix,centre,height,**kw)
common.render_views=wide
s=R/'joint_xray.py';sys.argv=[str(s),'--',str(P/'work/rig_v1.blend'),'Body',str(P/'work/joints_final.json'),str(P/'review/rig_probes/joints'),str(P/'work/meshy_joints_symmetric.json')]
runpy.run_path(str(s),run_name='__main__')
