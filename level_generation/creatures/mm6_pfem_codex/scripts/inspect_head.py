import bpy,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_model_v1/model_urls_glb.glb'))
for o in bpy.data.objects:
 if o.type!='MESH':continue
 co=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
 print(o.name,len(co),'bounds',lo,hi)
 for a,b in ((.25,.4),(.4,.55),(.55,.7),(.7,.85)):
  z=lo[2]+(hi[2]-lo[2])*np.array([a,b]);c=co[(co[:,2]>z[0])&(co[:,2]<z[1])];print('nose band',a,b,c[c[:,1].argmin()])
common.workbench_clay(bpy.context.scene,True)
common.render_views(str(p/'review/head_source'),float((lo[2]+hi[2])/2),float((hi[2]-lo[2])*1.1),views=('front','left','back'),resolution=(600,600),target=(float((lo[0]+hi[0])/2),float((lo[1]+hi[1])/2)))
