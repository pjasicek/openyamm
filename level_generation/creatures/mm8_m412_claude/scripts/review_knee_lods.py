import bpy,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));sys.path.insert(0,str(P/'scripts'))
from run_gates import Glb,load_meshes
from common import setup_render,workbench_clay,render_views
bpy.ops.wm.read_factory_settings(use_empty=True)
g=Glb(P/'export/mm8_m412.glb');meshes=[m for m in load_meshes(g) if '/colour' in m.label];clip=next(a for n,a,s,e in g.clips() if n=='Running')
scene=setup_render();workbench_clay(scene)
for f in [16,33]:
 pose=g.pose(clip,np.array([f/48]))[0]
 for m in meshes:
  co=m.posed(pose);me=bpy.data.meshes.new('review');me.from_pydata(co.tolist(),[],m.faces.tolist());me.update()
  for face in me.polygons:face.use_smooth=True
  ob=bpy.data.objects.new('review',me);scene.collection.objects.link(ob)
  render_views(str(P/'review/knee_fix'/f'LOD{m.label[-1]}_frame{f}'),center_z=.5,height=.9,views=('front','right'),resolution=(600,600))
  bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(me)
