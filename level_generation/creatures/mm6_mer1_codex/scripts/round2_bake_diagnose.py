import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['master','reduced_unbaked','body_lod0_rebaked','body_lod0']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round2/{name}.blend'));o=bpy.data.objects['Body'];me=o.data
 print('UV DIAG',name,'hidden',o.hide_render,o.hide_get(),'scale',o.scale[:], 'polys',len(me.polygons),flush=True)
 for uv in me.uv_layers:
  a=np.array([v.uv[:]for v in uv.data]);print(uv.name,uv.active_render,a.min(0),a.max(0),len(np.unique(np.round(a,5),axis=0)),flush=True)
 print('render',bpy.context.scene.render.bake.use_selected_to_active,'modifiers',[(m.name,m.show_render)for m in o.modifiers],flush=True)
