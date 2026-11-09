import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
src=(p/'scripts/feedback_tabard.py').read_text().replace('rig_v10_geometry.blend','rig_v11_geometry.blend').replace('rig_v10.blend','rig_v11.blend').replace('feedback_20261011','feet_cloak_20261011')
start=src.index('for i in C:')
end=src.index('co=np.array([v.co[:] for v in me.vertices]);index=',start)
src=src[:start]+src[end:]
exec(compile(src,str(p/'scripts/feedback_tabard.py'),'exec'))
